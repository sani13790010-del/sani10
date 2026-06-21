"""
درگاه لایسنس برای Telegram Bot

بررسی لایسنس قبل از انجام عملیات در Telegram.
جلوگیری از دسترسی غیرمجاز به ربات.

نویسنده: MT5 Trading Team
"""

from typing import Optional, Callable, List
from functools import wraps

from ..core.logger import get_logger
from ..services.license_service import license_service
from ..services.audit_service import audit_service, AuditAction
from ..models.license import LicenseValidationResult, BlockedReason, LicenseType, Feature

logger = get_logger("telegram_license_gate")


# =====================================================
# استثناها
# =====================================================

class TelegramLicenseError(Exception):
    """خطای لایسنس در Telegram"""
    def __init__(self, message: str, blocked_reasons: Optional[List[str]] = None):
        self.message = message
        self.blocked_reasons = blocked_reasons or []
        super().__init__(message)


# =====================================================
# پیام‌های خطا
# =====================================================

ERROR_MESSAGES = {
    BlockedReason.LICENSE_NOT_FOUND.value: (
        "❌ لایسنس یافت نشد\n\n"
        "لطفاً ابتدا لایسنس خود را فعال کنید.\n"
        "برای خرید لایسنس از دستور /plans استفاده کنید."
    ),
    BlockedReason.LICENSE_EXPIRED.value: (
        "❌ لایسنس شما منقضی شده است\n\n"
        "برای تمدید لایسنس از دستور /renew استفاده کنید."
    ),
    BlockedReason.LICENSE_REVOKED.value: (
        "❌ لایسنس شما ابطال شده است\n\n"
        "برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
    ),
    BlockedReason.LICENSE_SUSPENDED.value: (
        "❌ لایسنس شما تعلیق شده است\n\n"
        "برای رفع مشکل با پشتیبانی تماس بگیرید."
    ),
    BlockedReason.DEVICE_LIMIT_REACHED.value: (
        "❌ حداکثر تعداد دستگاه مجاز استفاده شده است\n\n"
        "برای مدیریت دستگاه‌ها از دستور /devices استفاده کنید."
    ),
    BlockedReason.FEATURE_NOT_ENABLED.value: (
        "❌ این قابلیت در پلن شما فعال نیست\n\n"
        "برای ارتقای پلن از دستور /upgrade استفاده کنید."
    ),
    BlockedReason.LICENSE_INACTIVE.value: (
        "❌ لایسنس شما فعال نیست\n\n"
        "لطفاً ابتدا لایسنس را فعال کنید."
    ),
}

FEATURE_NAMES = {
    Feature.SMC_ANALYSIS.value: "تحلیل SMC",
    Feature.PRICE_ACTION.value: "تحلیل Price Action",
    Feature.MULTI_TIMEFRAME.value: "تحلیل چند تایم‌فریم",
    Feature.MANUAL_TRADING.value: "معامله دستی",
    Feature.AUTO_TRADING.value: "معامله خودکار",
    Feature.TELEGRAM_BOT.value: "ربات تلگرام",
    Feature.DASHBOARD.value: "داشبورد",
    Feature.CHART_DRAWING.value: "رسم روی نمودار",
    Feature.DAILY_REPORTS.value: "گزارش‌های روزانه",
    Feature.ADVANCED_REPORTS.value: "گزارش‌های پیشرفته",
    Feature.CUSTOM_STRATEGIES.value: "استراتژی‌های سفارشی",
    Feature.API_ACCESS.value: "دسترسی API",
    Feature.SIGNALS.value: "سیگنال‌ها",
    Feature.PRIORITY_SUPPORT.value: "پشتیبانی ویژه",
}


# =====================================================
# کلاس اصلی
# =====================================================

class TelegramLicenseGate:
    """
    درگاه لایسنس برای Telegram

    بررسی لایسنس کاربر قبل از انجام عملیات.
    """

    def __init__(self):
        self._license_cache: dict = {}

    async def validate_user(
        self,
        user_id: int,
        license_key: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> LicenseValidationResult:
        """
        اعتبارسنجی لایسنس کاربر Telegram

        Args:
            user_id: شناسه تلگرام کاربر
            license_key: کلید لایسنس (اختیاری)
            device_id: شناسه دستگاه (اختیاری)

        Returns:
            LicenseValidationResult
        """
        # تلاش برای دریافت لایسنس از cache یا دیتابیس
        cache_key = f"tg_{user_id}"

        if cache_key in self._license_cache:
            cached_result = self._license_cache[cache_key]
            # بررسی اعتبار کش (60 ثانیه)
            from datetime import datetime
            if "cached_at" in cached_result:
                cached_at = datetime.fromisoformat(cached_result["cached_at"])
                if (datetime.utcnow() - cached_at).total_seconds() < 60:
                    return LicenseValidationResult(**cached_result["result"])

        # اگر license_key داده شده
        if license_key:
            result = await license_service.validate(
                license_key=license_key,
                device_id=device_id or f"TG-{user_id}"
            )
        else:
            # تلاش برای دریافت لایسنس کاربر
            from ..database import db
            user_license = await db.select_one(
                "licenses",
                filters={"user_id": user_id},
                use_admin=True
            )

            if not user_license:
                return LicenseValidationResult(
                    allowed=False,
                    status="not_found",
                    blocked_reasons=[BlockedReason.LICENSE_NOT_FOUND.value],
                    checked_at=None
                )

            result = await license_service.validate(
                license_key=user_license["license_key"],
                device_id=device_id or f"TG-{user_id}"
            )

        # کش نتیجه
        from datetime import datetime
        self._license_cache[cache_key] = {
            "result": result.model_dump(),
            "cached_at": datetime.utcnow().isoformat()
        }

        # ثبت audit
        await audit_service.log_license(
            action=AuditAction.LICENSE_VALIDATE,
            license_key=license_key or "from_db",
            user_id=str(user_id),
            device_id=device_id,
            success=result.allowed
        )

        return result

    async def get_user_license_key(self, telegram_id: int) -> Optional[str]:
        """دریافت کلید لایسنس کاربر از دیتابیس"""
        from ..database import db

        # دریافت user_id از telegram_id
        user_profile = await db.select_one(
            "user_profiles",
            filters={"telegram_id": telegram_id},
            use_admin=True
        )

        if not user_profile:
            return None

        # دریافت لایسنس
        license_data = await db.select_one(
            "licenses",
            filters={"user_id": user_profile["id"], "status": "active"},
            use_admin=True
        )

        return license_data.get("license_key") if license_data else None

    def get_error_message(self, result: LicenseValidationResult) -> str:
        """دریافت پیام خطای مناسب"""
        if not result.blocked_reasons:
            return ""

        # اولویت با خطاهای مهم‌تر
        priority_order = [
            BlockedReason.LICENSE_NOT_FOUND.value,
            BlockedReason.LICENSE_REVOKED.value,
            BlockedReason.LICENSE_EXPIRED.value,
            BlockedReason.LICENSE_SUSPENDED.value,
            BlockedReason.LICENSE_INACTIVE.value,
            BlockedReason.DEVICE_LIMIT_REACHED.value,
            BlockedReason.FEATURE_NOT_ENABLED.value,
        ]

        for reason in priority_order:
            if reason in result.blocked_reasons:
                return ERROR_MESSAGES.get(reason, f"❌ خطا: {reason}")

        return f"❌ خطا: {result.blocked_reasons[0]}"

    def clear_cache(self, user_id: int) -> None:
        """پاک کردن کش کاربر"""
        cache_key = f"tg_{user_id}"
        self._license_cache.pop(cache_key, None)


# نمونه گلوبال
telegram_license_gate = TelegramLicenseGate()


# =====================================================
# Decorators
# =====================================================

def require_license(func: Callable) -> Callable:
    """
    Decorator برای بررسی لایسنس

    Usage:
        @require_license
        async def handle_signal(update, context):
            ...
    """
    @wraps(func)
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else None

        if not user_id:
            await update.message.reply_text("خطا: شناسه کاربر یافت نشد")
            return

        # بررسی لایسنس
        result = await telegram_license_gate.validate_user(user_id)

        if not result.allowed:
            error_msg = telegram_license_gate.get_error_message(result)
            await update.message.reply_text(error_msg)
            return

        # ذخیره در context
        context.user_data["license_result"] = result

        return await func(update, context, *args, **kwargs)

    return wrapper


def require_feature(feature: str) -> Callable:
    """
    Decorator برای بررسی دسترسی به ویژگی خاص

    Usage:
        @require_feature("auto_trading")
        async def handle_auto_trade(update, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else None

            if not user_id:
                return

            result = await telegram_license_gate.validate_user(user_id)

            if not result.allowed:
                error_msg = telegram_license_gate.get_error_message(result)
                await update.message.reply_text(error_msg)
                return

            if feature not in result.enabled_modules:
                feature_name = FEATURE_NAMES.get(feature, feature)
                await update.message.reply_text(
                    f"❌ دسترسی به \"{feature_name}\" در پلن شما فعال نیست\n\n"
                    f"پلن فعلی: {result.plan}\n"
                    f"برای ارتقا از دستور /upgrade استفاده کنید."
                )
                return

            context.user_data["license_result"] = result
            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator


def require_plan(minimum_plan: LicenseType) -> Callable:
    """
    Decorator برای بررسی حداقل پلن

    Usage:
        @require_plan(LicenseType.PRO)
        async def handle_advanced_features(update, context):
            ...
    """
    PLAN_NAMES = {
        LicenseType.TRIAL: "آزمایشی",
        LicenseType.BASIC: "پایه",
        LicenseType.PRO: "حرفه‌ای",
        LicenseType.ENTERPRISE: "سازمانی",
        LicenseType.LIFETIME: "مادام‌العمر",
    }

    PLAN_LEVELS = {
        LicenseType.TRIAL: 1,
        LicenseType.BASIC: 2,
        LicenseType.PRO: 3,
        LicenseType.ENTERPRISE: 4,
        LicenseType.LIFETIME: 5,
    }

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else None

            if not user_id:
                return

            result = await telegram_license_gate.validate_user(user_id)

            if not result.allowed:
                error_msg = telegram_license_gate.get_error_message(result)
                await update.message.reply_text(error_msg)
                return

            try:
                current_plan = LicenseType(result.plan)
                current_level = PLAN_LEVELS.get(current_plan, 0)
                required_level = PLAN_LEVELS.get(minimum_plan, 0)

                if current_level < required_level:
                    await update.message.reply_text(
                        f"❌ این قابلیت نیاز به پلن {PLAN_NAMES.get(minimum_plan, minimum_plan.value)} دارد\n\n"
                        f"پلن فعلی: {PLAN_NAMES.get(current_plan, result.plan)}\n"
                        f"برای ارتقا از دستور /upgrade استفاده کنید."
                    )
                    return
            except ValueError:
                await update.message.reply_text("❌ پلن نامعتبر")
                return

            context.user_data["license_result"] = result
            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator


# =====================================================
# Helper Functions
# =====================================================

async def get_user_plan_info(telegram_id: int) -> dict:
    """
    دریافت اطلاعات پلن کاربر

    Returns:
        dict با اطلاعات پلن یا None
    """
    result = await telegram_license_gate.validate_user(telegram_id)

    if not result.allowed and result.status == "not_found":
        return None

    return {
        "plan": result.plan,
        "status": result.status,
        "allowed": result.allowed,
        "days_remaining": result.days_remaining,
        "features": result.enabled_modules,
        "limits": result.limits.model_dump() if result.limits else {},
        "blocked_reasons": result.blocked_reasons
    }


async def can_use_feature(telegram_id: int, feature: str) -> bool:
    """بررسی دسترسی به ویژژی خاص"""
    result = await telegram_license_gate.validate_user(telegram_id)

    if not result.allowed:
        return False

    return feature in result.enabled_modules


async def get_features_list(result: LicenseValidationResult) -> str:
    """
    دریافت لیست قابلیت‌ها به صورت متن

    برای نمایش در پیام تلگرام
    """
    if not result.enabled_modules:
        return "هیچ قابلیتی فعال نیست"

    lines = []
    for feature in result.enabled_modules:
        feature_name = FEATURE_NAMES.get(feature, feature)
        lines.append(f"✅ {feature_name}")

    return "\n".join(lines)


async def get_upgrade_message(current_plan: str) -> str:
    """پیام ارتقای پلن"""
    return (
        "📈 ارتقای پلن\n\n"
        "برای دسترسی به قابلیت‌های بیشتر، پلن خود را ارتقا دهید:\n\n"
        "🔹 پایه - معاملات دستی\n"
        "🔹 حرفه‌ای - معاملات خودکار\n"
        "🔹 سازمانی - مدیریت چند حساب\n"
        "🔹 مادام‌العمر - دسترسی کامل\n\n"
        "برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
    )
