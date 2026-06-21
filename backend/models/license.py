"""
مدل‌های لایسنس

تعریف مدل‌های Pydantic برای سیستم لایسنس.

نویسنده: MT5 Trading Team
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import os


class LicenseStatus(str, Enum):
    """وضعیت لایسنس"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class LicenseType(str, Enum):
    """نوع لایسنس"""
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    LIFETIME = "lifetime"
    DEVELOPER = "developer"


class Feature(str, Enum):
    """ویژگی‌های سیستم"""
    # تحلیل
    SMC_ANALYSIS = "smc_analysis"
    PRICE_ACTION = "price_action"
    MULTI_TIMEFRAME = "multi_timeframe"

    # معاملات
    MANUAL_TRADING = "manual_trading"
    AUTO_TRADING = "auto_trading"
    SIGNALS = "signals"

    # ابزارها
    TELEGRAM_BOT = "telegram_bot"
    DASHBOARD = "dashboard"
    CHART_DRAWING = "chart_drawing"

    # گزارش‌ها
    DAILY_REPORTS = "daily_reports"
    ADVANCED_REPORTS = "advanced_reports"

    # تنظیمات
    CUSTOM_STRATEGIES = "custom_strategies"
    API_ACCESS = "api_access"
    PRIORITY_SUPPORT = "priority_support"


class BlockedReason(str, Enum):
    """دلایل مسدود شدن لایسنس"""
    LICENSE_NOT_FOUND = "LICENSE_NOT_FOUND"
    LICENSE_EXPIRED = "LICENSE_EXPIRED"
    LICENSE_REVOKED = "LICENSE_REVOKED"
    LICENSE_SUSPENDED = "LICENSE_SUSPENDED"
    DEVICE_LIMIT_REACHED = "DEVICE_LIMIT_REACHED"
    ACCOUNT_LIMIT_REACHED = "ACCOUNT_LIMIT_REACHED"
    SYMBOL_LIMIT_REACHED = "SYMBOL_LIMIT_REACHED"
    DAILY_TRADE_LIMIT_REACHED = "DAILY_TRADE_LIMIT_REACHED"
    FEATURE_NOT_ENABLED = "FEATURE_NOT_ENABLED"
    LICENSE_INACTIVE = "LICENSE_INACTIVE"


# =====================================================
# مدل‌های Pydantic
# =====================================================

class LicenseLimits(BaseModel):
    """محدودیت‌های لایسنس"""
    max_accounts: int = Field(default=1, ge=1, description="حداکثر حساب")
    max_symbols: int = Field(default=1, ge=-1, description="حداکثر نماد (-1 = نامحدود)")
    max_trades_per_day: int = Field(default=10, ge=-1, description="حداکثر معامله روزانه (-1 = نامتحود)")
    max_devices: int = Field(default=1, ge=1, description="حداکثر دستگاه")
    devices_used: int = Field(default=0, ge=0, description="تعداد دستگاه استفاده شده")


class LicensePlanBase(BaseModel):
    """پایه پلن لایسنس"""
    code: str
    name: str
    description: Optional[str] = None
    duration_days: int = Field(default=30, ge=1)
    max_accounts: int = Field(default=1, ge=1)
    max_symbols: int = Field(default=1, ge=-1)
    max_trades_per_day: int = Field(default=10, ge=-1)
    max_devices: int = Field(default=1, ge=1)
    enabled_features: List[str] = Field(default_factory=list)


class LicensePlan(LicensePlanBase):
    """پلن لایسنس کامل"""
    id: str
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LicenseDeviceBase(BaseModel):
    """پایه دستگاه لایسنس"""
    device_id: str
    device_name: Optional[str] = None
    device_type: str = Field(default="mt5")
    mt5_account: Optional[int] = None


class LicenseDevice(LicenseDeviceBase):
    """دستگاه لایسنس کامل"""
    id: str
    license_id: str
    ip_address: Optional[str] = None
    hardware_id: Optional[str] = None
    activated_at: datetime
    last_used_at: datetime
    deactivated_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class LicenseBase(BaseModel):
    """پایه لایسنس"""
    license_key: str = Field(..., min_length=12, max_length=64)
    license_type: LicenseType
    status: LicenseStatus = LicenseStatus.INACTIVE


class License(LicenseBase):
    """لایسنس کامل"""
    id: str
    user_id: Optional[str] = None
    activated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_validated_at: Optional[datetime] = None
    max_accounts: int = 1
    max_symbols: int = 1
    max_trades_per_day: int = 10
    max_devices: int = 1
    notes: Optional[str] = None
    status_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LicenseValidationResult(BaseModel):
    """
    نتیجه اعتبارسنجی لایسنس

    خروجی استاندارد برای تمام سیستم‌ها.
    """
    allowed: bool = Field(..., description="آیا دسترسی مجاز است")
    user_id: Optional[str] = Field(default=None, description="شناسه کاربر")
    license_id: Optional[str] = Field(default=None, description="شناسه لایسنس")
    plan: Optional[str] = Field(default=None, description="نوع پلن")
    status: Optional[str] = Field(default=None, description="وضعیت لایسنس")
    blocked_reasons: List[str] = Field(default_factory=list, description="دلایل مسدودی")
    limits: LicenseLimits = Field(default_factory=LicenseLimits, description="محدودیت‌ها")
    enabled_modules: List[str] = Field(default_factory=list, description="ماژول‌های فعال")
    expires_at: Optional[datetime] = Field(default=None, description="تاریخ انقضا")
    days_remaining: int = Field(default=0, ge=0, description="روزهای باقی‌مانده")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="زمان بررسی")

    class Config:
        from_attributes = True

    def has_feature(self, feature: str) -> bool:
        """بررسی دسترسی به ویژگی"""
        return feature in self.enabled_modules

    def is_blocked(self) -> bool:
        """بررسی مسدود بودن"""
        return len(self.blocked_reasons) > 0

    def get_block_message(self) -> str:
        """دریافت پیام مسدودی"""
        if not self.blocked_reasons:
            return ""

        messages = {
            BlockedReason.LICENSE_NOT_FOUND.value: "لایسنس یافت نشد",
            BlockedReason.LICENSE_EXPIRED.value: "لایسنس منقضی شده است",
            BlockedReason.LICENSE_REVOKED.value: "لایسنس ابطال شده است",
            BlockedReason.LICENSE_SUSPENDED.value: "لایسنس تعلیق شده است",
            BlockedReason.DEVICE_LIMIT_REACHED.value: "حداکثر دستگاه استفاده شده است",
            BlockedReason.ACCOUNT_LIMIT_REACHED.value: "حداکثر حساب استفاده شده است",
            BlockedReason.SYMBOL_LIMIT_REACHED.value: "حداکثر نماد استفاده شده است",
            BlockedReason.DAILY_TRADE_LIMIT_REACHED.value: "حداکثر معامله روزانه استفاده شده است",
            BlockedReason.FEATURE_NOT_ENABLED.value: "این ویژگی در پلن شما فعال نیست",
            BlockedReason.LICENSE_INACTIVE.value: "لایسنس غیرفعال است",
        }

        return " | ".join(messages.get(r, r) for r in self.blocked_reasons)


# =====================================================
# مدل‌های درخواست
# =====================================================

class LicenseValidateRequest(BaseModel):
    """درخواست اعتبارسنجی لایسنس"""
    license_key: str = Field(..., min_length=12, max_length=64, description="کلید لایسنس")
    device_id: Optional[str] = Field(default=None, max_length=255, description="شناسه دستگاه")
    requested_features: Optional[List[str]] = Field(default=None, description="ویژگی‌های درخواستی")


class DeviceActivateRequest(BaseModel):
    """درخواست فعال‌سازی دستگاه"""
    license_key: str = Field(..., min_length=12, max_length=64)
    device_id: str = Field(..., min_length=4, max_length=255)
    device_name: Optional[str] = Field(default=None, max_length=100)
    device_type: str = Field(default="mt5")
    mt5_account: Optional[int] = None


class LicenseCreateRequest(BaseModel):
    """درخواست ایجاد لایسنس"""
    user_id: str
    license_type: LicenseType
    max_accounts: int = Field(default=1, ge=1)
    max_symbols: int = Field(default=1, ge=-1)
    max_trades_per_day: int = Field(default=10, ge=-1)
    max_devices: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class LicenseUpdateRequest(BaseModel):
    """درخواست به‌روزرسانی لایسنس"""
    status: Optional[LicenseStatus] = None
    max_accounts: Optional[int] = Field(default=None, ge=1)
    max_symbols: Optional[int] = Field(default=None, ge=-1)
    max_trades_per_day: Optional[int] = Field(default=None, ge=-1)
    max_devices: Optional[int] = Field(default=None, ge=1)
    notes: Optional[str] = None
    status_reason: Optional[str] = None


class LicenseExtendRequest(BaseModel):
    """درخواست تمدید لایسنس"""
    days: int = Field(..., ge=1, le=365, description="تعداد روز تمدید")


# =====================================================
# مدل‌های پاسخ
# =====================================================

class LicenseResponse(BaseModel):
    """پاسخ استاندارد لایسنس"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class LicenseStatsResponse(BaseModel):
    """آمار لایسنس"""
    license_key: str
    license_type: str
    status: str
    days_remaining: int
    devices: Dict[str, Any]
    features: List[str]
    validations_count: int
    last_validation: Optional[datetime]


# =====================================================
# تنظیمات از Environment
# =====================================================

class LicenseConfig(BaseModel):
    """تنظیمات سیستم لایسنس"""
    validation_cache_seconds: int = Field(default=60, ge=10, le=600)
    max_retry_attempts: int = Field(default=3, ge=1, le=10)
    trial_extension_days: int = Field(default=0, ge=0, le=7)

    @classmethod
    def from_env(cls) -> "LicenseConfig":
        """بارگذاری از متغیرهای محیطی"""
        return cls(
            validation_cache_seconds=int(os.getenv("LICENSE_CACHE_SECONDS", "60")),
            max_retry_attempts=int(os.getenv("LICENSE_MAX_RETRIES", "3")),
            trial_extension_days=int(os.getenv("LICENSE_TRIAL_EXTEND_DAYS", "0")),
        )


# =====================================================
# ثابت‌ها
# =====================================================

# ویژگی‌های هر پلن
PLAN_FEATURES: Dict[LicenseType, List[Feature]] = {
    LicenseType.TRIAL: [
        Feature.SMC_ANALYSIS,
        Feature.PRICE_ACTION,
        Feature.SIGNALS,
    ],
    LicenseType.BASIC: [
        Feature.SMC_ANALYSIS,
        Feature.PRICE_ACTION,
        Feature.MULTI_TIMEFRAME,
        Feature.MANUAL_TRADING,
        Feature.TELEGRAM_BOT,
        Feature.DASHBOARD,
        Feature.SIGNALS,
    ],
    LicenseType.PRO: [
        Feature.SMC_ANALYSIS,
        Feature.PRICE_ACTION,
        Feature.MULTI_TIMEFRAME,
        Feature.MANUAL_TRADING,
        Feature.AUTO_TRADING,
        Feature.TELEGRAM_BOT,
        Feature.DASHBOARD,
        Feature.CHART_DRAWING,
        Feature.DAILY_REPORTS,
        Feature.ADVANCED_REPORTS,
        Feature.API_ACCESS,
        Feature.SIGNALS,
    ],
    LicenseType.ENTERPRISE: [
        Feature.SMC_ANALYSIS,
        Feature.PRICE_ACTION,
        Feature.MULTI_TIMEFRAME,
        Feature.MANUAL_TRADING,
        Feature.AUTO_TRADING,
        Feature.TELEGRAM_BOT,
        Feature.DASHBOARD,
        Feature.CHART_DRAWING,
        Feature.DAILY_REPORTS,
        Feature.ADVANCED_REPORTS,
        Feature.CUSTOM_STRATEGIES,
        Feature.API_ACCESS,
        Feature.SIGNALS,
        Feature.PRIORITY_SUPPORT,
    ],
    LicenseType.LIFETIME: [f for f in Feature],
    LicenseType.DEVELOPER: [f for f in Feature],
}

# مدت اعتبار پلن‌ها (روز)
PLAN_DURATION: Dict[LicenseType, int] = {
    LicenseType.TRIAL: 7,
    LicenseType.BASIC: 30,
    LicenseType.PRO: 90,
    LicenseType.ENTERPRISE: 365,
    LicenseType.LIFETIME: 36500,
    LicenseType.DEVELOPER: 36500,
}
