"""
روت‌های لایسنس

Endpointهای مربوط به اعتبارسنجی و مدیریت لایسنس.

نویسنده: MT5 Trading Team
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from ...core.logger import get_logger
from ...services.license_service import license_service
from ...models.license import (
    LicenseValidateRequest,
    DeviceActivateRequest,
    LicenseValidationResult,
    LicenseResponse,
    LicenseCreateRequest,
    LicenseExtendRequest,
)
from ...services import audit_service

logger = get_logger("api.license")
router = APIRouter()


# =====================================================
# Public Endpoints (بدون احراز هویت)
# =====================================================

@router.post("/validate")
async def validate_license(
    request: Request,
    data: LicenseValidateRequest
):
    """
    اعتبارسنجی لایسنس

    این endpoint توسط MT5 EA یا Telegram Bot برای بررسی اعتبار لایسنس استفاده می‌شود.

    خروجی استاندارد:
    - allowed: وضعیت دسترسی
    - user_id: شناسه کاربر
    - license_id: شناسه لایسنس
    - plan: نوع پلن
    - status: وضعیت
    - blocked_reasons: دلایل مسدودی
    - limits: محدودیت‌ها
    - enabled_modules: ماژول‌های فعال
    - expires_at: تاریخ انقضا
    - checked_at: زمان بررسی
    """
    logger.info(f"درخواست اعتبارسنجی لایسنس: {data.license_key[:12]}****")

    ip_address = request.client.host if request.client else None

    result = await license_service.validate(
        license_key=data.license_key,
        device_id=data.device_id,
        ip_address=ip_address,
        requested_features=data.requested_features
    )

    return {
        "success": result.allowed,
        "data": result.model_dump(),
        "message": None if result.allowed else result.get_block_message()
    }


@router.post("/activate")
async def activate_device(
    request: Request,
    data: DeviceActivateRequest
):
    """
    فعال‌سازی دستگاه

    ثبت دستگاه جدید برای لایسنس.
    """
    logger.info(f"درخواست فعال‌سازی دستگاه: {data.device_id}")

    ip_address = request.client.host if request.client else None

    try:
        result = await license_service.activate_device(
            license_key=data.license_key,
            device_id=data.device_id,
            device_name=data.device_name,
            device_type=data.device_type,
            mt5_account=data.mt5_account,
            ip_address=ip_address
        )

        return {
            "success": True,
            "data": result,
            "message": "دستگاه با موفقیت فعال شد"
        }

    except Exception as e:
        return {
            "success": False,
            "data": {},
            "message": str(e)
        }


@router.post("/deactivate")
async def deactivate_device(
    request: Request,
    data: DeviceActivateRequest
):
    """
    غیرفعال‌سازی دستگاه

    حذف دستگاه از لیست دستگاه‌های مجاز.
    """
    logger.info(f"درخواست غیرفعال‌سازی دستگاه: {data.device_id}")

    result = await license_service.deactivate_device(
        license_key=data.license_key,
        device_id=data.device_id
    )

    return {
        "success": result,
        "data": {},
        "message": "دستگاه غیرفعال شد" if result else "دستگاه یافت نشد"
    }


@router.get("/devices")
async def get_devices(
    license_key: str
):
    """
    دریافت لیست دستگاه‌ها
    """
    devices = await license_service.get_devices(license_key)

    return {
        "success": True,
        "data": devices
    }


@router.get("/feature-check")
async def check_feature_access(
    license_key: str,
    feature: str
):
    """
    بررسی دسترسی به ویژگی

    بررسی اینکه آیا لایسنس به ویژگی خاصی دسترسی دارد.
    """
    has_access = await license_service.has_feature(license_key, feature)

    return {
        "success": True,
        "data": {
            "feature": feature,
            "has_access": has_access
        }
    }


@router.get("/limit-check")
async def check_limits(
    license_key: str,
    account_count: Optional[int] = None,
    symbol_count: Optional[int] = None,
    trade_count_today: Optional[int] = None
):
    """
    بررسی محدودیت‌ها
    """
    result = await license_service.check_limits(
        license_key=license_key,
        account_count=account_count,
        symbol_count=symbol_count,
        trade_count_today=trade_count_today
    )

    return {
        "success": result["allowed"],
        "data": result
    }


# =====================================================
# Protected Endpoints (با احراز هویت)
# =====================================================

# NOTE: این endpointها باید با auth middleware محافظت شوند

@router.get("/my")
async def get_my_license():
    """
    دریافت لایسنس کاربر جاری

    اطلاعات لایسنس فعال کاربر را برمی‌گرداند.
    """
    # TODO: دریافت user_id از token
    # فعلاً برای demo
    return {
        "success": True,
        "data": None,
        "message": "لطفاً احراز هویت کنید"
    }


@router.get("/stats")
async def get_license_stats(
    license_key: str
):
    """
    آمار لایسنس
    """
    stats = await license_service.get_license_stats(license_key)

    return {
        "success": True,
        "data": stats
    }


# =====================================================
# Admin Endpoints
# =====================================================

@router.post("/create")
async def create_license(
    data: LicenseCreateRequest
):
    """
    ایجاد لایسنس جدید (Admin only)
    """
    result = await license_service.create_license(
        user_id=data.user_id,
        license_type=data.license_type,
        max_accounts=data.max_accounts,
        max_symbols=data.max_symbols,
        max_trades_per_day=data.max_trades_per_day,
        max_devices=data.max_devices,
        notes=data.notes
    )

    return {
        "success": True,
        "data": result,
        "message": "لایسنس با موفقیت ایجاد شد"
    }


@router.post("/extend")
async def extend_license(
    license_key: str,
    data: LicenseExtendRequest
):
    """
    تمدید لایسنس (Admin only)
    """
    result = await license_service.extend_license(
        license_key=license_key,
        days=data.days
    )

    return {
        "success": True,
        "data": result,
        "message": f"لایسنس به مدت {data.days} روز تمدید شد"
    }


@router.post("/revoke")
async def revoke_license(
    license_key: str,
    reason: Optional[str] = None
):
    """
    ابطال لایسنس (Admin only)
    """
    result = await license_service.revoke_license(
        license_key=license_key,
        reason=reason
    )

    return {
        "success": result,
        "message": "لایسنس ابطال شد" if result else "خطا در ابطال"
    }


@router.post("/suspend")
async def suspend_license(
    license_key: str,
    reason: Optional[str] = None
):
    """
    تعلیق لایسنس (Admin only)
    """
    result = await license_service.suspend_license(
        license_key=license_key,
        reason=reason
    )

    return {
        "success": result,
        "message": "لایسنس تعلیق شد" if result else "خطا در تعلیق"
    }


@router.post("/activate-license")
async def activate_license_admin(
    license_key: str
):
    """
    فعال‌سازی لایسنس از حالت suspended (Admin only)
    """
    result = await license_service.activate_license(license_key)

    return {
        "success": result,
        "message": "لایسنس فعال شد" if result else "خطا در فعال‌سازی"
    }
