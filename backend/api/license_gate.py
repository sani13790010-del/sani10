"""
درگاه لایسنس برای API

Middleware و dependencies برای بررسی لایسنس در endpointها.
جلوگیری از دسترسی غیرمجاز به API.

نویسنده: MT5 Trading Team
"""

from typing import Optional, List, Callable
from functools import wraps
from fastapi import HTTPException, Request, Depends, Header
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ..core.logger import get_logger
from ..core.exceptions import LicenseError
from ..services.license_service import license_service
from ..models.license import LicenseValidationResult, BlockedReason, LicenseType

logger = get_logger("license_gate")


# =====================================================
# Constants
# =====================================================

LICENSE_HEADER = "X-License-Key"
DEVICE_HEADER = "X-Device-ID"

# Endpointهایی که نیازی به لایسنس ندارند
PUBLIC_ENDPOINTS = [
    "/health",
    "/api/health",
    "/api/license/validate",
    "/api/license/activate",
    "/docs",
    "/openapi.json",
    "/redoc",
]

# Endpointهایی که نیازمند لایسنس حداقل پایه هستند
MINIMUM_LICENSE_ENDPOINTS = {
    "/api/decision": LicenseType.BASIC,
    "/api/signals": LicenseType.BASIC,
    "/api/trades": LicenseType.BASIC,
}

# ویژگی‌های مورد نیاز endpointها
ENDPOINT_FEATURES = {
    "/api/decision": ["api_access", "signals"],
    "/api/signals/generate": ["signals", "smc_analysis"],
    "/api/trades/auto": ["auto_trading"],
    "/api/trades/manual": ["manual_trading"],
    "/api/analysis/smc": ["smc_analysis"],
    "/api/analysis/pa": ["price_action"],
    "/api/analysis/mtf": ["multi_timeframe"],
    "/api/reports/advanced": ["advanced_reports"],
}


# =====================================================
# License Gate Exception
# =====================================================

class LicenseGateError(HTTPException):
    """خطای درگاه لایسنس"""
    def __init__(
        self,
        detail: str,
        blocked_reasons: Optional[List[str]] = None,
        status_code: int = 403
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.blocked_reasons = blocked_reasons or []


# =====================================================
# Middleware
# =====================================================

class LicenseGateMiddleware(BaseHTTPMiddleware):
    """
    Middleware برای بررسی لایسنس

    بررسی تمام درخواست‌ها به API و جلوگیری از دسترسی غیرمجاز.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # رفع از endpointهای عمومی
        if self._is_public_endpoint(path):
            return await call_next(request)

        # دریافت هدرهای لایسنس
        license_key = request.headers.get(LICENSE_HEADER)
        device_id = request.headers.get(DEVICE_HEADER)

        # بررسی لایسنس
        if not license_key:
            return self._license_required_response(request)

        try:
            result = await license_service.validate(
                license_key=license_key,
                device_id=device_id,
                ip_address=request.client.host if request.client else None
            )

            if not result.allowed:
                return self._license_denied_response(request, result)

            # بررسی ویژگی‌های مورد نیاز
            required_features = self._get_required_features(path)
            if required_features:
                missing = [f for f in required_features if f not in result.enabled_modules]
                if missing:
                    return self._feature_denied_response(request, result, missing)

            # ذخیره نتیجه در state
            request.state.license_result = result

            return await call_next(request)

        except Exception as e:
            logger.error(f"خطا در درگاه لایسنس: {e}")
            return self._error_response(request, str(e))


    def _is_public_endpoint(self, path: str) -> bool:
        """بررسی endpoint عمومی"""
        for public in PUBLIC_ENDPOINTS:
            if path.startswith(public):
                return True
        return False

    def _get_required_features(self, path: str) -> List[str]:
        """دریافت ویژگی‌های مورد نیاز"""
        for endpoint, features in ENDPOINT_FEATURES.items():
            if path.startswith(endpoint):
                return features
        return []

    def _license_required_response(self, request: Request) -> JSONResponse:
        """پاسخ لایسنس الزامی"""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "LICENSE_REQUIRED",
                "message": "لطفاً هدر X-License-Key را ارسال کنید",
                "blocked_reasons": ["LICENSE_REQUIRED"]
            }
        )

    def _license_denied_response(self, request: Request, result: LicenseValidationResult) -> JSONResponse:
        """پاسخ لایسنس نامعتبر"""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "LICENSE_DENIED",
                "message": result.get_block_message(),
                "blocked_reasons": result.blocked_reasons,
                "status": result.status,
                "expires_at": result.expires_at.isoformat() if result.expires_at else None
            }
        )

    def _feature_denied_response(self, request: Request, result: LicenseValidationResult, missing: List[str]) -> JSONResponse:
        """پاسخ ویژگی غیرفعال"""
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "FEATURE_NOT_LICENSED",
                "message": "این ویژگی در پلن شما فعال نیست",
                "missing_features": missing,
                "current_plan": result.plan,
                "enabled_features": result.enabled_modules
            }
        )

    def _error_response(self, request: Request, error: str) -> JSONResponse:
        """پاسخ خطا (بدون افشای اطلاعات حساس)"""
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "خطای داخلی سرور"
            }
        )


# =====================================================
# Dependencies
# =====================================================

async def get_license_key(
    x_license_key: Optional[str] = Header(None, alias="X-License-Key")
) -> str:
    """
    Dependency برای دریافت کلید لایسنس

    Raises:
        HTTPException: اگر لایسنس ارسال نشده باشد
    """
    if not x_license_key:
        raise LicenseGateError(
            detail="هدر X-License-Key الزامی است",
            blocked_reasons=["LICENSE_REQUIRED"]
        )
    return x_license_key


async def validate_license(
    request: Request,
    license_key: str = Depends(get_license_key),
    device_id: Optional[str] = Header(None, alias="X-Device-ID")
) -> LicenseValidationResult:
    """
    Dependency برای اعتبارسنجی لایسنس

    Returns:
        LicenseValidationResult

    Raises:
        HTTPException: اگر لایسنس نامعتبر باشد
    """
    try:
        result = await license_service.validate(
            license_key=license_key,
            device_id=device_id,
            ip_address=request.client.host if request.client else None
        )

        if not result.allowed:
            raise LicenseGateError(
                detail=result.get_block_message(),
                blocked_reasons=result.blocked_reasons
            )

        return result

    except LicenseGateError:
        raise
    except Exception as e:
        logger.error(f"خطا در اعتبارسنجی لایسنس: {e}")
        raise LicenseGateError(
            detail="خطا در اعتبارسنجی لایسنس",
            blocked_reasons=["INTERNAL_ERROR"]
        )


async def validate_license_optional(
    request: Request,
    license_key: Optional[str] = Header(None, alias="X-License-Key"),
    device_id: Optional[str] = Header(None, alias="X-Device-ID")
) -> Optional[LicenseValidationResult]:
    """
    Dependency برای اعتبارسنجی اختیاری لایسنس

    Returns licesne result or None (بدون خطا)
    """
    if not license_key:
        return None

    try:
        return await license_service.validate(
            license_key=license_key,
            device_id=device_id,
            ip_address=request.client.host if request.client else None
        )
    except Exception:
        return None


def require_feature(feature: str):
    """
    Decorator برای بررسی دسترسی به ویژژی

    Usage:
        @router.get("/advanced")
        @require_feature("advanced_reports")
        async def get_advanced_reports(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, license_result: LicenseValidationResult = Depends(validate_license), **kwargs):
            if feature not in license_result.enabled_modules:
                raise LicenseGateError(
                    detail=f"دسترسی به {feature} در پلن شما فعال نیست",
                    blocked_reasons=[BlockedReason.FEATURE_NOT_ENABLED.value]
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_plan(minimum_plan: LicenseType):
    """
    Decorator برای بررسی حداقل پلن

    Usage:
        @router.get("/auto-trade")
        @require_plan(LicenseType.PRO)
        async def auto_trade(...):
            ...
    """
    PLAN_LEVELS = {
        LicenseType.TRIAL: 1,
        LicenseType.BASIC: 2,
        LicenseType.PRO: 3,
        LicenseType.ENTERPRISE: 4,
        LicenseType.LIFETIME: 5,
        LicenseType.DEVELOPER: 6,
    }

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, license_result: LicenseValidationResult = Depends(validate_license), **kwargs):
            current_level = PLAN_LEVELS.get(LicenseType(license_result.plan), 0)
            required_level = PLAN_LEVELS.get(minimum_plan, 0)

            if current_level < required_level:
                raise LicenseGateError(
                    detail=f"این قابلیت نیاز به پلن {minimum_plan.value} یا بالاتر دارد",
                    blocked_reasons=["PLAN_UPGRADE_REQUIRED"]
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_features(features: List[str]):
    """
    Decorator برای بررسی چند ویژگی

    Usage:
        @router.get("/analysis")
        @require_features(["smc_analysis", "price_action"])
        async def get_analysis(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, license_result: LicenseValidationResult = Depends(validate_license), **kwargs):
            missing = [f for f in features if f not in license_result.enabled_modules]
            if missing:
                raise LicenseGateError(
                    detail=f"ویژگی‌های {', '.join(missing)} در پلن شما فعال نیست",
                    blocked_reasons=[BlockedReason.FEATURE_NOT_ENABLED.value]
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =====================================================
# Rate Limiting بر اساس لایسنس
# =====================================================

async def check_rate_limit(
    request: Request,
    license_result: LicenseValidationResult = Depends(validate_license)
) -> LicenseValidationResult:
    """
    بررسی محدودیت نرخ بر اساس نوع لایسنس

    پلن‌های بالاتر نرخ بیشتر مجاز هستند.
    """
    # محدودیت‌ها بر اساس پلن
    RATE_LIMITS = {
        LicenseType.TRIAL.value: 10,      # 10 درخواست در دقیقه
        LicenseType.BASIC.value: 30,
        LicenseType.PRO.value: 100,
        LicenseType.ENTERPRISE.value: 500,
        LicenseType.LIFETIME.value: 200,
        LicenseType.DEVELOPER.value: 1000,
    }

    # TODO: پیاده‌سازی real rate limiting با Redis
    # فعلاً فقط license_result را برمی‌گردانیم

    return license_result


# =====================================================
# Audit Helper
# =====================================================

async def log_api_access(
    request: Request,
    license_result: LicenseValidationResult = Depends(validate_license)
) -> LicenseValidationResult:
    """
    ثبت دسترسی API
    """
    from ..services.audit_service import audit_service, AuditAction

    await audit_service.log(
        action=AuditAction.DECISION_REQUEST,
        user_id=license_result.user_id,
        resource_type="api",
        resource_id=request.url.path,
        ip_address=request.client.host if request.client else None,
        details={
            "license_plan": license_result.plan,
            "endpoint": request.url.path,
            "method": request.method
        }
    )

    return license_result
