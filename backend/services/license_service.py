"""
سرویس کامل لایسنس

مدیریت و اعتبارسنجی لایسنس‌ها با قابلیت‌های:
- اعتبارسنجی کامل (active, expired, revoked, suspended)
- بررسی محدودیت‌ها (accounts, symbols, devices, trades)
- مدیریت دستگاه‌ها
- کش کردن نتایج
- ثبت audit

نویسنده: MT5 Trading Team
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import secrets
import time
import os

from ..core.logger import get_logger
from ..core.exceptions import LicenseError, LicenseExpiredError
from ..database import db
from ..models.license import (
    License,
    LicenseType,
    LicenseStatus,
    LicenseValidationResult,
    LicenseLimits,
    LicenseDevice,
    LicenseConfig,
    BlockedReason,
    PLAN_FEATURES,
    PLAN_DURATION,
)
from .audit_service import audit_service, AuditAction

logger = get_logger("license_service")


class LicenseService:
    """
    سرویس کامل لایسنس

    مسئولیت‌ها:
    - اعتبارسنجی لایسنس با خروجی استاندارد
    - بررسی تمام وضعیت‌ها (active, expired, revoked, suspended)
    - بررسی محدودیت‌ها
    - مدیریت دستگاه‌ها
    - کش کردن نتایج
    """

    def __init__(self):
        self._config = LicenseConfig.from_env()
        self._cache: Dict[str, Dict[str, Any]] = {}

    # =====================================================
    # اعتبارسنجی
    # =====================================================

    async def validate(
        self,
        license_key: str,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        requested_features: Optional[List[str]] = None
    ) -> LicenseValidationResult:
        """
        اعتبارسنجی کامل لایسنس

        خروجی استاندارد برای همه سیستم‌ها:
        - allowed
        - user_id
        - license_id
        - plan
        - status
        - blocked_reasons
        - limits
        - enabled_modules
        - expires_at
        - checked_at
        """
        start_time = time.time()

        try:
            # بررسی کش
            cached = self._get_cached(license_key)
            if cached and not device_id:
                logger.debug(f"بازگشت از کش: {license_key[:12]}****")
                return LicenseValidationResult(**cached)

            # دریافت از دیتابیس
            license_data = await self._get_license(license_key)

            if not license_data:
                return self._create_result(
                    allowed=False,
                    status="not_found",
                    blocked_reasons=[BlockedReason.LICENSE_NOT_FOUND.value]
                )

            # بررسی وضعیت
            result = await self._validate_status(license_data, device_id, ip_address)

            # بررسی ویژگی‌های درخواستی
            if result.allowed and requested_features:
                result = self._check_requested_features(result, license_data, requested_features)

            # به‌روزرسانی دستگاه
            if result.allowed and device_id:
                await self._update_device_usage(license_data, device_id, ip_address)

            # ثبت اعتبارسنجی
            await self._log_validation(
                license_data,
                device_id,
                ip_address,
                result,
                int((time.time() - start_time) * 1000)
            )

            # کش کردن
            self._cache_result(license_key, result.model_dump())

            # ثبت audit
            await audit_service.log_license(
                action=AuditAction.LICENSE_VALIDATE,
                license_key=license_key,
                user_id=user_id or license_data.get("user_id"),
                device_id=device_id,
                success=result.allowed,
                ip_address=ip_address
            )

            return result

        except LicenseExpiredError as e:
            return self._create_result(
                allowed=False,
                status="expired",
                blocked_reasons=[BlockedReason.LICENSE_EXPIRED.value]
            )
        except Exception as e:
            logger.error(f"خطا در اعتبارسنجی لایسنس: {e}")
            return self._create_result(
                allowed=False,
                status="error",
                blocked_reasons=["INTERNAL_ERROR"]
            )

    async def _validate_status(
        self,
        license_data: Dict[str, Any],
        device_id: Optional[str],
        ip_address: Optional[str]
    ) -> LicenseValidationResult:
        """بررسی وضعیت لایسنس"""
        blocked_reasons = []
        status = license_data.get("status", LicenseStatus.INACTIVE.value)
        license_type = license_data.get("license_type", LicenseType.TRIAL.value)

        # بررسی وضعیت‌های مختلف
        if status == LicenseStatus.INACTIVE.value:
            blocked_reasons.append(BlockedReason.LICENSE_INACTIVE.value)

        elif status == LicenseStatus.EXPIRED.value:
            blocked_reasons.append(BlockedReason.LICENSE_EXPIRED.value)

        elif status == LicenseStatus.REVOKED.value:
            blocked_reasons.append(BlockedReason.LICENSE_REVOKED.value)

        elif status == LicenseStatus.SUSPENDED.value:
            blocked_reasons.append(BlockedReason.LICENSE_SUSPENDED.value)

        # بررسی انقضا (حتی اگر status اشتباه باشد)
        expires_at = license_data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_at < datetime.utcnow():
                if BlockedReason.LICENSE_EXPIRED.value not in blocked_reasons:
                    blocked_reasons.append(BlockedReason.LICENSE_EXPIRED.value)
                status = LicenseStatus.EXPIRED.value

        # بررسی دستگاه
        if device_id and license_data.get("id"):
            device_blocked = await self._check_device_limit(license_data, device_id)
            if device_blocked and BlockedReason.DEVICE_LIMIT_REACHED.value not in blocked_reasons:
                blocked_reasons.append(device_blocked)

        is_allowed = len(blocked_reasons) == 0 and status == LicenseStatus.ACTIVE.value

        # دریافت limits
        limits = await self._get_limits(license_data)
        enabled_modules = self._get_enabled_modules(license_type)
        days_remaining = self._calculate_days_remaining(license_data.get("expires_at"))

        return LicenseValidationResult(
            allowed=is_allowed,
            user_id=str(license_data.get("user_id")) if license_data.get("user_id") else None,
            license_id=str(license_data.get("id")),
            plan=license_type,
            status=status,
            blocked_reasons=blocked_reasons,
            limits=limits,
            enabled_modules=enabled_modules,
            expires_at=expires_at if isinstance(expires_at, datetime) else None,
            days_remaining=days_remaining,
            checked_at=datetime.utcnow()
        )

    async def _check_device_limit(
        self,
        license_data: Dict[str, Any],
        device_id: str
    ) -> Optional[str]:
        """بررسی محدودیت دستگاه"""
        license_id = license_data.get("id")
        max_devices = license_data.get("max_devices", 1)

        # شمارش دستگاه‌های فعال
        devices = await db.select_many(
            "license_devices",
            filters={"license_id": license_id, "is_active": True},
            use_admin=True
        )

        devices_used = len(devices)
        device_ids = [d.get("device_id") for d in devices]

        # اگر دستگاه قبلاً ثبت شده
        if device_id in device_ids:
            return None

        # بررسی محدودیت
        if devices_used >= max_devices:
            return BlockedReason.DEVICE_LIMIT_REACHED.value

        return None

    def _check_requested_features(
        self,
        result: LicenseValidationResult,
        license_data: Dict[str, Any],
        requested_features: List[str]
    ) -> LicenseValidationResult:
        """بررسی ویژگی‌های درخواستی"""
        enabled_modules = result.enabled_modules
        missing_features = []

        for feature in requested_features:
            if feature not in enabled_modules:
                missing_features.append(feature)

        if missing_features:
            result.allowed = False
            result.blocked_reasons.append(BlockedReason.FEATURE_NOT_ENABLED.value)

        return result

    async def _update_device_usage(
        self,
        license_data: Dict[str, Any],
        device_id: str,
        ip_address: Optional[str]
    ) -> None:
        """به‌روزرسانی استفاده از دستگاه"""
        license_id = license_data.get("id")

        # بررسی وجود دستگاه
        existing = await db.select_one(
            "license_devices",
            filters={"license_id": license_id, "device_id": device_id},
            use_admin=True
        )

        now = datetime.utcnow().isoformat()

        if existing:
            # به‌روزرسانی آخرین استفاده
            await db.update(
                "license_devices",
                {"id": existing["id"]},
                {"last_used_at": now, "ip_address": ip_address},
                use_admin=True
            )
        else:
            # ثبت دستگاه جدید
            await db.insert(
                "license_devices",
                {
                    "license_id": license_id,
                    "device_id": device_id,
                    "activated_at": now,
                    "last_used_at": now,
                    "ip_address": ip_address,
                    "is_active": True
                },
                use_admin=True
            )

    async def _get_limits(self, license_data: Dict[str, Any]) -> LicenseLimits:
        """دریافت محدودیت‌های لایسنس"""
        license_id = license_data.get("id")

        # شمارش دستگاه‌ها
        devices = await db.select_many(
            "license_devices",
            filters={"license_id": license_id, "is_active": True},
            use_admin=True
        )

        return LicenseLimits(
            max_accounts=license_data.get("max_accounts", 1),
            max_symbols=license_data.get("max_symbols", 1),
            max_trades_per_day=license_data.get("max_trades_per_day", 10),
            max_devices=license_data.get("max_devices", 1),
            devices_used=len(devices)
        )

    def _get_enabled_modules(self, license_type: str) -> List[str]:
        """دریافت ماژول‌های فعال"""
        try:
            ltype = LicenseType(license_type)
            features = PLAN_FEATURES.get(ltype, [])
            return [f.value for f in features]
        except ValueError:
            return []

    # =====================================================
    # مدیریت لایسنس
    # =====================================================

    async def create_license(
        self,
        user_id: str,
        license_type: LicenseType,
        max_accounts: int = 1,
        max_symbols: int = 1,
        max_trades_per_day: int = 10,
        max_devices: int = 1,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """ایجاد لایسنس جدید"""
        license_key = self._generate_license_key()
        duration = PLAN_DURATION.get(license_type, 30)
        expires_at = datetime.utcnow() + timedelta(days=duration)

        license_data = {
            "license_key": license_key,
            "user_id": user_id,
            "license_type": license_type.value,
            "status": LicenseStatus.ACTIVE.value,
            "activated_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "max_accounts": max_accounts,
            "max_symbols": max_symbols,
            "max_trades_per_day": max_trades_per_day,
            "max_devices": max_devices,
            "notes": notes
        }

        result = await db.insert("licenses", license_data, use_admin=True)

        logger.info(f"لایسنس جدید ایجاد شد: {license_key} برای کاربر {user_id}")

        return result

    async def extend_license(
        self,
        license_key: str,
        days: int
    ) -> Dict[str, Any]:
        """تمدید لایسنس"""
        license_data = await self._get_license(license_key)
        if not license_data:
            raise LicenseError("لایسنس یافت نشد")

        current_expiry = license_data.get("expires_at")
        if isinstance(current_expiry, str):
            current_expiry = datetime.fromisoformat(current_expiry.replace("Z", "+00:00"))

        if current_expiry > datetime.utcnow():
            new_expiry = current_expiry + timedelta(days=days)
        else:
            new_expiry = datetime.utcnow() + timedelta(days=days)

        await db.update(
            "licenses",
            {"license_key": license_key},
            {
                "expires_at": new_expiry.isoformat(),
                "status": LicenseStatus.ACTIVE.value
            },
            use_admin=True
        )

        self._clear_cache(license_key)

        logger.info(f"لایسنس تمدید شد: {license_key} به مدت {days} روز")

        return {"license_key": license_key, "new_expiry": new_expiry.isoformat()}

    async def revoke_license(
        self,
        license_key: str,
        reason: Optional[str] = None,
        revoked_by: Optional[str] = None
    ) -> bool:
        """ابطال لایسنس"""
        result = await db.update(
            "licenses",
            {"license_key": license_key},
            {
                "status": LicenseStatus.REVOKED.value,
                "status_reason": reason,
                "revoked_at": datetime.utcnow().isoformat(),
                "revoked_by": revoked_by
            },
            use_admin=True
        )

        self._clear_cache(license_key)

        await audit_service.log_license(
            action=AuditAction.LICENSE_REVOKE,
            license_key=license_key,
            success=True,
            error_message=reason
        )

        logger.warning(f"لایسنس ابطال شد: {license_key}")

        return bool(result)

    async def suspend_license(
        self,
        license_key: str,
        reason: Optional[str] = None,
        suspended_by: Optional[str] = None
    ) -> bool:
        """تعلیق لایسنس"""
        result = await db.update(
            "licenses",
            {"license_key": license_key},
            {
                "status": LicenseStatus.SUSPENDED.value,
                "status_reason": reason,
                "suspended_at": datetime.utcnow().isoformat(),
                "suspended_by": suspended_by
            },
            use_admin=True
        )

        self._clear_cache(license_key)

        logger.warning(f"لایسنس تعلیق شد: {license_key}")

        return bool(result)

    async def activate_license(
        self,
        license_key: str
    ) -> bool:
        """فعال‌سازی لایسنس (از حالت suspended)"""
        license_data = await self._get_license(license_key)
        if not license_data:
            return False

        # بررسی انقضا
        expires_at = license_data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expires_at < datetime.utcnow():
                return False

        result = await db.update(
            "licenses",
            {"license_key": license_key},
            {
                "status": LicenseStatus.ACTIVE.value,
                "status_reason": None,
                "suspended_at": None
            },
            use_admin=True
        )

        self._clear_cache(license_key)

        return bool(result)

    # =====================================================
    # دستگاه‌ها
    # =====================================================

    async def activate_device(
        self,
        license_key: str,
        device_id: str,
        device_name: Optional[str] = None,
        device_type: str = "mt5",
        mt5_account: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """فعال‌سازی دستگاه"""
        # ابتدا اعتبارسنجی
        result = await self.validate(license_key, device_id, ip_address=ip_address)

        if not result.allowed and BlockedReason.DEVICE_LIMIT_REACHED.value in result.blocked_reasons:
            raise LicenseError("حداکثر دستگاه استفاده شده است")

        license_data = await self._get_license(license_key)
        if not license_data:
            raise LicenseError("لایسنس یافت نشد")

        license_id = license_data.get("id")
        now = datetime.utcnow().isoformat()

        # بررسی دستگاه موجود
        existing = await db.select_one(
            "license_devices",
            filters={"license_id": license_id, "device_id": device_id},
            use_admin=True
        )

        if existing:
            await db.update(
                "license_devices",
                {"id": existing["id"]},
                {
                    "last_used_at": now,
                    "device_name": device_name or existing.get("device_name"),
                    "is_active": True,
                    "deactivated_at": None,
                    "ip_address": ip_address
                },
                use_admin=True
            )
        else:
            # ثبت دستگاه جدید
            await db.insert(
                "license_devices",
                {
                    "license_id": license_id,
                    "device_id": device_id,
                    "device_name": device_name or f"Device-{device_id[:8]}",
                    "device_type": device_type,
                    "mt5_account": mt5_account,
                    "activated_at": now,
                    "last_used_at": now,
                    "ip_address": ip_address,
                    "is_active": True
                },
                use_admin=True
            )

        return {"success": True, "device_id": device_id}

    async def deactivate_device(
        self,
        license_key: str,
        device_id: str
    ) -> bool:
        """غیرفعال‌سازی دستگاه"""
        license_data = await self._get_license(license_key)
        if not license_data:
            return False

        result = await db.update(
            "license_devices",
            {
                "license_id": license_data["id"],
                "device_id": device_id
            },
            {
                "is_active": False,
                "deactivated_at": datetime.utcnow().isoformat()
            },
            use_admin=True
        )

        return bool(result)

    async def get_devices(
        self,
        license_key: str
    ) -> List[Dict[str, Any]]:
        """دریافت لیست دستگاه‌ها"""
        license_data = await self._get_license(license_key)
        if not license_data:
            return []

        devices = await db.select_many(
            "license_devices",
            filters={"license_id": license_data["id"]},
            order_by="last_used_at",
            order_desc=True,
            use_admin=True
        )

        # حذف اطلاعات حساس
        for d in devices:
            d.pop("ip_address", None)
            d.pop("hardware_id", None)

        return devices

    # =====================================================
    # دریافت اطلاعات
    # =====================================================

    async def get_user_license(self, user_id: str) -> Optional[Dict[str, Any]]:
        """دریافت لایسنس فعال کاربر"""
        licenses = await db.select_many(
            "licenses",
            filters={"user_id": user_id},
            order_by="created_at",
            order_desc=True,
            limit=1,
            use_admin=True
        )

        if not licenses:
            return None

        return licenses[0]

    async def get_license_stats(self, license_key: str) -> Dict[str, Any]:
        """آمار لایسنس"""
        license_data = await self._get_license(license_key)
        if not license_data:
            return {}

        devices = await self.get_devices(license_key)
        validations = await db.select_many(
            "license_validations",
            filters={"license_key": license_key},
            order_by="created_at",
            order_desc=True,
            limit=100,
            use_admin=True
        )

        return {
            "license_key": license_key[:12] + "****",
            "license_type": license_data.get("license_type"),
            "status": license_data.get("status"),
            "days_remaining": self._calculate_days_remaining(license_data.get("expires_at")),
            "devices": {
                "limit": license_data.get("max_devices", 1),
                "used": len([d for d in devices if d.get("is_active")]),
                "list": devices
            },
            "features": self._get_enabled_modules(license_data.get("license_type", "trial")),
            "validations_count": len(validations),
            "last_validation": validations[0].get("created_at") if validations else None
        }

    # =====================================================
    # بررسی دسترسی
    # =====================================================

    async def has_feature(
        self,
        license_key: str,
        feature: str
    ) -> bool:
        """بررسی دسترسی به ویژگی"""
        result = await self.validate(license_key)
        if not result.allowed:
            return False
        return feature in result.enabled_modules

    async def check_limits(
        self,
        license_key: str,
        account_count: Optional[int] = None,
        symbol_count: Optional[int] = None,
        trade_count_today: Optional[int] = None
    ) -> Dict[str, Any]:
        """بررسی محدودیت‌ها"""
        result = await self.validate(license_key)

        if not result.allowed:
            return {"allowed": False, "reasons": result.blocked_reasons}

        reasons = []

        if account_count is not None:
            if result.limits.max_accounts != -1 and account_count >= result.limits.max_accounts:
                reasons.append(BlockedReason.ACCOUNT_LIMIT_REACHED.value)

        if symbol_count is not None:
            if result.limits.max_symbols != -1 and symbol_count >= result.limits.max_symbols:
                reasons.append(BlockedReason.SYMBOL_LIMIT_REACHED.value)

        if trade_count_today is not None:
            if result.limits.max_trades_per_day != -1 and trade_count_today >= result.limits.max_trades_per_day:
                reasons.append(BlockedReason.DAILY_TRADE_LIMIT_REACHED.value)

        return {
            "allowed": len(reasons) == 0,
            "reasons": reasons,
            "limits": result.limits.model_dump()
        }

    # =====================================================
    # توابع کمکی
    # =====================================================

    async def _get_license(self, license_key: str) -> Optional[Dict[str, Any]]:
        """دریافت لایسنس از دیتابیس"""
        return await db.select_one(
            "licenses",
            filters={"license_key": license_key},
            use_admin=True
        )

    async def _log_validation(
        self,
        license_data: Dict[str, Any],
        device_id: Optional[str],
        ip_address: Optional[str],
        result: LicenseValidationResult,
        response_time_ms: int
    ) -> None:
        """ثبت اعتبارسنجی در دیتابیس"""
        try:
            await db.insert(
                "license_validations",
                {
                    "license_id": license_data.get("id"),
                    "user_id": license_data.get("user_id"),
                    "license_key": result.license_id,
                    "device_id": device_id,
                    "ip_address": ip_address,
                    "is_valid": result.allowed,
                    "status": result.status,
                    "blocked_reasons": result.blocked_reasons,
                    "enabled_features": result.enabled_modules,
                    "limits": result.limits.model_dump() if result.limits else {},
                    "response_time_ms": response_time_ms
                },
                use_admin=True
            )
        except Exception as e:
            logger.error(f"خطا در ثبت اعتبارسنجی: {e}")

    def _generate_license_key(self) -> str:
        """تولید کلید لایسنس"""
        random_bytes = secrets.token_hex(8)
        parts = [random_bytes[i:i+4].upper() for i in range(0, 16, 4)]
        return f"MT5-{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}"

    def _calculate_days_remaining(self, expires_at: Optional[str]) -> int:
        """محاسبه روزهای باقی‌مانده"""
        if not expires_at:
            return 0
        try:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            remaining = (expires_at - datetime.utcnow()).days
            return max(0, remaining)
        except Exception:
            return 0

    def _create_result(
        self,
        allowed: bool,
        status: str,
        blocked_reasons: List[str]
    ) -> LicenseValidationResult:
        """ایجاد نتیجه اعتبارسنجی"""
        return LicenseValidationResult(
            allowed=allowed,
            status=status,
            blocked_reasons=blocked_reasons,
            checked_at=datetime.utcnow()
        )

    # =====================================================
    # کش
    # =====================================================

    def _get_cached(self, license_key: str) -> Optional[Dict[str, Any]]:
        """دریافت از کش"""
        if license_key not in self._cache:
            return None

        cached = self._cache[license_key]
        cached_at = datetime.fromisoformat(cached.get("_cached_at", "2000-01-01"))
        if (datetime.utcnow() - cached_at).total_seconds() > self._config.validation_cache_seconds:
            del self._cache[license_key]
            return None

        return cached

    def _cache_result(self, license_key: str, result: Dict[str, Any]) -> None:
        """کش کردن نتیجه"""
        result["_cached_at"] = datetime.utcnow().isoformat()
        self._cache[license_key] = result

    def _clear_cache(self, license_key: str) -> None:
        """پاک کردن کش"""
        self._cache.pop(license_key, None)

    def clear_all_cache(self) -> None:
        """پاک کردن همه کش"""
        self._cache.clear()
        logger.info("کش لایسنس پاک شد")


# نمونه گلوبال
license_service = LicenseService()
