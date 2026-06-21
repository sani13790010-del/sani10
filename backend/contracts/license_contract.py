"""
قرارداد اعتبارسنجی لایسنس برای MQL5

تعریف فرمت درخواست و پاسخ برای ارتباط بین MT5 EA و Backend API.

نویسنده: MT5 Trading Team
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# =====================================================
# Request Contract
# =====================================================

class MQL5LicenseValidateRequest(BaseModel):
    """
    درخواست اعتبارسنجی لایسنس از MT5 EA

    فرمت درخواستی که MT5 EA ارسال می‌کند.
    """
    license_key: str = Field(..., min_length=12, max_length=64, description="کلید لایسنس")
    device_id: str = Field(..., min_length=4, max_length=255, description="شناسه دستگاه")
    mt5_account: Optional[int] = Field(default=None, description="شماره حساب MT5")
    mt5_build: Optional[int] = Field(default=None, description="نسخه MT5")
    symbol: Optional[str] = Field(default=None, description="نماد فعلی")
    ip_address: Optional[str] = Field(default=None, description="آدرس IP")


class MQL5DeviceActivateRequest(BaseModel):
    """درخواست فعال‌سازی دستگاه از MT5"""
    license_key: str
    device_id: str
    device_name: Optional[str] = None
    mt5_account: Optional[int] = None
    mt5_build: Optional[int] = None


# =====================================================
# Response Contract
# =====================================================

class MQL5LicenseLimits(BaseModel):
    """محدودیت‌های لایسنس برای MT5"""
    max_accounts: int = Field(default=1, description="حداکثر حساب")
    max_symbols: int = Field(default=1, description="حداکثر نماد (-1 = نامحدود)")
    max_trades_per_day: int = Field(default=10, description="حداکثر معامله روزانه (-1 = نامحدود)")
    max_devices: int = Field(default=1, description="حداکثر دستگاه")
    devices_used: int = Field(default=0, description="دستگاه‌های استفاده شده")


class MQL5Feature(str, Enum):
    """ویژگی‌های قابل استفاده در MT5"""
    SMC_ANALYSIS = "smc_analysis"
    PRICE_ACTION = "price_action"
    MULTI_TIMEFRAME = "multi_timeframe"
    MANUAL_TRADING = "manual_trading"
    AUTO_TRADING = "auto_trading"
    SIGNALS = "signals"
    TELEGRAM_BOT = "telegram_bot"
    CHART_DRAWING = "chart_drawing"


class MQL5LicenseResponse(BaseModel):
    """
    پاسخ اعتبارسنجی لایسنس برای MT5 EA

    فرمت استاندارد خروجی که Backend ارسال می‌کند.
    این فرمت باید دقیقاً با JSON که MQL5 دریافت می‌کند مطابقت داشته باشد.
    """
    allowed: bool = Field(..., description="آیا دسترسی مجاز است")
    user_id: Optional[str] = Field(default=None, description="شناسه کاربر")
    license_id: Optional[str] = Field(default=None, description="شناسه لایسنس")
    plan: Optional[str] = Field(default=None, description="نوع پلن (trial/basic/pro/enterprise/lifetime)")
    status: Optional[str] = Field(default=None, description="وضعیت (active/expired/revoked/suspended)")
    blocked_reasons: List[str] = Field(default_factory=list, description="دلایل مسدودی")
    limits: MQL5LicenseLimits = Field(default_factory=MQL5LicenseLimits, description="محدودیت‌ها")
    enabled_modules: List[str] = Field(default_factory=list,
        description="ماژول‌های فعال (smc_analysis, price_action, auto_trading, ...)")
    expires_at: Optional[datetime] = Field(default=None, description="تاریخ انقضا")
    days_remaining: int = Field(default=0, description="روزهای باقی‌مانده")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="زمان بررسی")

    class Config:
        json_schema_extra = {
            "example": {
                "allowed": True,
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "license_id": "123e4567-e89b-12d3-a456-426614174001",
                "plan": "pro",
                "status": "active",
                "blocked_reasons": [],
                "limits": {
                    "max_accounts": 3,
                    "max_symbols": 10,
                    "max_trades_per_day": 50,
                    "max_devices": 3,
                    "devices_used": 1
                },
                "enabled_modules": [
                    "smc_analysis",
                    "price_action",
                    "multi_timeframe",
                    "manual_trading",
                    "auto_trading",
                    "telegram_bot",
                    "dashboard",
                    "chart_drawing",
                    "daily_reports",
                    "advanced_reports",
                    "api_access",
                    "signals"
                ],
                "expires_at": "2025-12-31T23:59:59Z",
                "days_remaining": 365,
                "checked_at": "2025-01-15T10:30:00Z"
            }
        }


class MQL5DeviceActivateResponse(BaseModel):
    """پاسخ فعال‌سازی دستگاه"""
    success: bool
    device_id: str
    message: str
    devices_remaining: int = Field(description="تعداد دستگاه باقی‌مانده")


# =====================================================
# Error Codes
# =====================================================

MQL5_ERROR_CODES = {
    "LICENSE_NOT_FOUND": {
        "code": 1001,
        "message": "لایسنس یافت نشد",
        "action": "لطفاً کلید لایسنس معتبر وارد کنید"
    },
    "LICENSE_EXPIRED": {
        "code": 1002,
        "message": "لایسنس منقضی شده است",
        "action": "لطفاً لایسنس را تمدید کنید"
    },
    "LICENSE_REVOKED": {
        "code": 1003,
        "message": "لایسنس ابطال شده است",
        "action": "با پشتیبانی تماس بگیرید"
    },
    "LICENSE_SUSPENDED": {
        "code": 1004,
        "message": "لایسنس تعلیق شده است",
        "action": "با پشتیبانی تماس بگیرید"
    },
    "DEVICE_LIMIT_REACHED": {
        "code": 1005,
        "message": "حداکثر دستگاه استفاده شده است",
        "action": "یک دستگاه را غیرفعال کنید یا پلن را ارتقا دهید"
    },
    "FEATURE_NOT_ENABLED": {
        "code": 1006,
        "message": "این ویژگی فعال نیست",
        "action": "پلن خود را ارتقا دهید"
    },
    "LICENSE_INACTIVE": {
        "code": 1007,
        "message": "لایسنس فعال نیست",
        "action": "لطفاً لایسنس را فعال کنید"
    },
    "ACCOUNT_LIMIT_REACHED": {
        "code": 1008,
        "message": "حداکثر حساب استفاده شده است",
        "action": "یک حساب را حذف کنید یا پلن را ارتقا دهید"
    },
    "SYMBOL_LIMIT_REACHED": {
        "code": 1009,
        "message": "حداکثر نماد استفاده شده است",
        "action": "پلن خود را ارتقا دهید"
    },
    "DAILY_TRADE_LIMIT_REACHED": {
        "code": 1010,
        "message": "حداکثر معامله روزانه استفاده شده است",
        "action": "فردا دوباره تلاش کنید یا پلن را ارتقا دهید"
    },
}


# =====================================================
# MT5 EA Constants (برای استفاده در .mqh)
# =====================================================

MT5_CONSTANTS_HEADER = """
//+------------------------------------------------------------------+
//|                                           LicenseContract.mqh     |
//|                                    MT5 Trading System             |
//|                                    قرارداد لایسنس                 |
//+------------------------------------------------------------------+
#property strict

//+
// Error Codes
//+
enum ENUM_LICENSE_ERROR {
   LICENSE_ERROR_NONE = 0,
   LICENSE_ERROR_NOT_FOUND = 1001,
   LICENSE_ERROR_EXPIRED = 1002,
   LICENSE_ERROR_REVOKED = 1003,
   LICENSE_ERROR_SUSPENDED = 1004,
   LICENSE_ERROR_DEVICE_LIMIT = 1005,
   LICENSE_ERROR_FEATURE_DISABLED = 1006,
   LICENSE_ERROR_INACTIVE = 1007,
   LICENSE_ERROR_ACCOUNT_LIMIT = 1008,
   LICENSE_ERROR_SYMBOL_LIMIT = 1009,
   LICENSE_ERROR_DAILY_TRADE_LIMIT = 1010
};

//+
// License Status
//+
enum ENUM_LICENSE_STATUS {
   LICENSE_STATUS_INACTIVE,
   LICENSE_STATUS_ACTIVE,
   LICENSE_STATUS_EXPIRED,
   LICENSE_STATUS_REVOKED,
   LICENSE_STATUS_SUSPENDED
};

//+
// License Plan
//+
enum ENUM_LICENSE_PLAN {
   LICENSE_PLAN_TRIAL,
   LICENSE_PLAN_BASIC,
   LICENSE_PLAN_PRO,
   LICENSE_PLAN_ENTERPRISE,
   LICENSE_PLAN_LIFETIME
};

//+
// Feature Flags
//+
enum ENUM_LICENSE_FEATURE {
   LICENSE_FEATURE_SMC_ANALYSIS,
   LICENSE_FEATURE_PRICE_ACTION,
   LICENSE_FEATURE_MULTI_TIMEFRAME,
   LICENSE_FEATURE_MANUAL_TRADING,
   LICENSE_FEATURE_AUTO_TRADING,
   LICENSE_FEATURE_SIGNALS,
   LICENSE_FEATURE_TELEGRAM_BOT,
   LICENSE_FEATURE_CHART_DRAWING,
   LICENSE_FEATURE_DAILY_REPORTS,
   LICENSE_FEATURE_ADVANCED_REPORTS,
   LICENSE_FEATURE_API_ACCESS
};

//+
// License Result Structure
//+
struct MQL5LicenseResult {
   bool allowed;
   string user_id;
   string license_id;
   string plan;
   ENUM_LICENSE_STATUS status;
   string blocked_reasons[10];
   int blocked_count;

   // Limits
   int max_accounts;
   int max_symbols;
   int max_trades_per_day;
   int max_devices;
   int devices_used;

   // Features
   string enabled_modules[20];
   int enabled_count;

   // Time
   datetime expires_at;
   int days_remaining;
   datetime checked_at;

   // Error
   ENUM_LICENSE_ERROR error_code;
   string error_message;
};

//+
// HTTP Headers for License API
//+
#define LICENSE_HEADER "X-License-Key"
#define DEVICE_HEADER "X-Device-ID"
#define API_VERSION_HEADER "X-API-Version"
#define ACCEPT_HEADER "Accept"

//+
// API Endpoints
//+
string LICENSE_VALIDATE_URL = "/api/license/validate";
string LICENSE_ACTIVATE_URL = "/api/license/activate";
string LICENSE_DEACTIVATE_URL = "/api/license/deactivate";
string LICENSE_STATUS_URL = "/api/license/status";

//+
// Check Feature Enabled
//+
bool IsFeatureEnabled(MQL5LicenseResult &result, ENUM_LICENSE_FEATURE feature) {
   string featureName;
   switch(feature) {
      case LICENSE_FEATURE_SMC_ANALYSIS: featureName = "smc_analysis"; break;
      case LICENSE_FEATURE_PRICE_ACTION: featureName = "price_action"; break;
      case LICENSE_FEATURE_MULTI_TIMEFRAME: featureName = "multi_timeframe"; break;
      case LICENSE_FEATURE_MANUAL_TRADING: featureName = "manual_trading"; break;
      case LICENSE_FEATURE_AUTO_TRADING: featureName = "auto_trading"; break;
      case LICENSE_FEATURE_SIGNALS: featureName = "signals"; break;
      case LICENSE_FEATURE_TELEGRAM_BOT: featureName = "telegram_bot"; break;
      case LICENSE_FEATURE_CHART_DRAWING: featureName = "chart_drawing"; break;
      case LICENSE_FEATURE_DAILY_REPORTS: featureName = "daily_reports"; break;
      case LICENSE_FEATURE_ADVANCED_REPORTS: featureName = "advanced_reports"; break;
      case LICENSE_FEATURE_API_ACCESS: featureName = "api_access"; break;
      default: return false;
   }

   for(int i = 0; i < result.enabled_count; i++) {
      if(result.enabled_modules[i] == featureName) {
         return true;
      }
   }
   return false;
}

//+
// Get Error Message
//+
string GetLicenseErrorMessage(ENUM_LICENSE_ERROR error) {
   switch(error) {
      case LICENSE_ERROR_NOT_FOUND: return "لایسنس یافت نشد";
      case LICENSE_ERROR_EXPIRED: return "لایسنس منقضی شده است";
      case LICENSE_ERROR_REVOKED: return "لایسنس ابطال شده است";
      case LICENSE_ERROR_SUSPENDED: return "لایسنس تعلیق شده است";
      case LICENSE_ERROR_DEVICE_LIMIT: return "حداکثر دستگاه استفاده شده";
      case LICENSE_ERROR_FEATURE_DISABLED: return "این ویژگی فعال نیست";
      case LICENSE_ERROR_INACTIVE: return "لایسنس فعال نیست";
      case LICENSE_ERROR_ACCOUNT_LIMIT: return "حداکثر حساب استفاده شده";
      case LICENSE_ERROR_SYMBOL_LIMIT: return "حداکثر نماد استفاده شده";
      case LICENSE_ERROR_DAILY_TRADE_LIMIT: return "حداکثر معامله روزانه استفاده شده";
      default: return "خطای نامشخص";
   }
}
//+------------------------------------------------------------------+
"""


# =====================================================
# Contract Documentation
# =====================================================

LICENSE_API_CONTRACT = """
# قرارداد API لایسنس برای MT5

## Endpoint: POST /api/license/validate

### درخواست:
```json
{
    "license_key": "MT5-XXXX-XXXX-XXXX-XXXX",
    "device_id": "DEV-XXXXXXXX",
    "mt5_account": 12345678,
    "mt5_build": 4050
}
```

### پاسخ موفق:
```json
{
    "success": true,
    "data": {
        "allowed": true,
        "user_id": "uuid",
        "license_id": "uuid",
        "plan": "pro",
        "status": "active",
        "blocked_reasons": [],
        "limits": {
            "max_accounts": 3,
            "max_symbols": 10,
            "max_trades_per_day": 50,
            "max_devices": 3,
            "devices_used": 1
        },
        "enabled_modules": [
            "smc_analysis",
            "price_action",
            "auto_trading",
            ...
        ],
        "expires_at": "2025-12-31T23:59:59Z",
        "days_remaining": 365,
        "checked_at": "2025-01-15T10:30:00Z"
    }
}
```

### پاسخ خطا:
```json
{
    "success": false,
    "data": {
        "allowed": false,
        "status": "expired",
        "blocked_reasons": ["LICENSE_EXPIRED"]
    },
    "message": "لایسنس منقضی شده است"
}
```

## HTTP Headers:

- `X-License-Key`: کلید لایسنس (الزامی)
- `X-Device-ID`: شناسه دستگاه (الزامی برای بررسی دستگاه)

## Error Codes:

| Code | Name | Description |
|------|------|-------------|
| 1001 | LICENSE_NOT_FOUND | لایسنس یافت نشد |
| 1002 | LICENSE_EXPIRED | لایسنس منقضی شده |
| 1003 | LICENSE_REVOKED | لایسنس ابطال شده |
| 1004 | LICENSE_SUSPENDED | لایسنس تعلیق شده |
| 1005 | DEVICE_LIMIT_REACHED | حداکثر دستگاه |
| 1006 | FEATURE_NOT_ENABLED | ویژگی فعال نیست |
| 1007 | LICENSE_INACTIVE | لایسنس غیرفعال |

## Feature Codes:

| Code | Name | Minimum Plan |
|------|------|--------------|
| smc_analysis | تحلیل SMC | trial |
| price_action | تحلیل PA | trial |
| signals | سیگنال‌ها | trial |
| manual_trading | معامله دستی | basic |
| telegram_bot | ربات تلگرام | basic |
| dashboard | داشبورد | basic |
| multi_timeframe | چند تایم‌فریم | basic |
| auto_trading | معامله خودکار | pro |
| chart_drawing | رسم نمودار | pro |
| api_access | دسترسی API | pro |
| advanced_reports | گزارش پیشرفته | pro |
| custom_strategies | استراتژی سفارشی | enterprise |
| priority_support | پشتیبانی ویژه | enterprise |
"""
