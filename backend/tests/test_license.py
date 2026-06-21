"""
تست‌های سیستم لایسنس

تست کامل برای سناریوهای مختلف:
- Active license
- Expired license
- Revoked license
- Suspended license
- Device limit exceeded
- Feature check
- Plan limits

نویسنده: MT5 Trading Team
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from backend.models.license import (
    LicenseType,
    LicenseStatus,
    LicenseValidationResult,
    LicenseLimits,
    BlockedReason,
    PLAN_FEATURES,
)
from backend.services.license_service import LicenseService


# =====================================================
# Mock Fixtures
# =====================================================

@pytest.fixture
def mock_db():
    """Mock دیتابیس"""
    db = MagicMock()
    db.select_one = AsyncMock()
    db.select_many = AsyncMock(return_value=[])
    db.insert = AsyncMock(return_value={"id": "test-id"})
    db.update = AsyncMock(return_value=[{"id": "test-id"}])
    return db


@pytest.fixture
def license_service():
    """نمونه LicenseService بدون دیتابیس واقعی"""
    return LicenseService()


@pytest.fixture
def active_license_data():
    """لایسنس فعال نمونه"""
    return {
        "id": "license-123",
        "license_key": "MT5-A1B2-C3D4-E5F6-7890",
        "user_id": "user-123",
        "license_type": "pro",
        "status": "active",
        "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        "max_accounts": 3,
        "max_symbols": 10,
        "max_trades_per_day": 50,
        "max_devices": 3,
        "activated_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def expired_license_data():
    """لایسنس منقضی نمونه"""
    return {
        "id": "license-expired",
        "license_key": "MT5-EXPIRED-1234-5678",
        "user_id": "user-123",
        "license_type": "basic",
        "status": "expired",
        "expires_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "max_accounts": 1,
        "max_symbols": 3,
        "max_trades_per_day": 10,
        "max_devices": 2,
    }


@pytest.fixture
def revoked_license_data():
    """لایسنس ابطال شده نمونه"""
    return {
        "id": "license-revoked",
        "license_key": "MT5-REVOKED-1234-5678",
        "user_id": "user-123",
        "license_type": "pro",
        "status": "revoked",
        "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        "max_accounts": 3,
        "max_symbols": 10,
        "max_trades_per_day": 50,
        "max_devices": 3,
        "revoked_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def suspended_license_data():
    """لایسنس تعلیق شده نمونه"""
    return {
        "id": "license-suspended",
        "license_key": "MT5-SUSPENDED-1234-5678",
        "user_id": "user-123",
        "license_type": "pro",
        "status": "suspended",
        "expires_at": (datetime.utcnow() + timedelta(days=90)).isoformat(),
        "max_accounts": 3,
        "max_symbols": 10,
        "max_trades_per_day": 50,
        "max_devices": 3,
        "suspended_at": datetime.utcnow().isoformat(),
    }


# =====================================================
# Test Active License
# =====================================================

class TestActiveLicense:
    """تست لایسنس فعال"""

    @pytest.mark.asyncio
    async def test_validate_active_license(
        self, license_service, active_license_data, mock_db
    ):
        """تست اعتبارسنجی لایسنس فعال"""
        mock_db.select_one.return_value = active_license_data
        mock_db.select_many.return_value = []

        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key=active_license_data["license_key"]
                )

        assert result.allowed is True
        assert result.status == "active"
        assert len(result.blocked_reasons) == 0
        assert result.plan == "pro"

    @pytest.mark.asyncio
    async def test_active_license_has_correct_features(
        self, license_service, active_license_data
    ):
        """تست ویژگی‌های لایسنس Pro"""
        features = license_service._get_enabled_modules("pro")

        assert "smc_analysis" in features
        assert "price_action" in features
        assert "auto_trading" in features
        assert "api_access" in features

    @pytest.mark.asyncio
    async def test_active_license_limits(
        self, license_service, active_license_data
    ):
        """تست محدودیت‌های لایسنس"""
        limits = LicenseLimits(
            max_accounts=active_license_data["max_accounts"],
            max_symbols=active_license_data["max_symbols"],
            max_trades_per_day=active_license_data["max_trades_per_day"],
            max_devices=active_license_data["max_devices"],
            devices_used=0
        )

        assert limits.max_accounts == 3
        assert limits.max_symbols == 10
        assert limits.max_trades_per_day == 50


# =====================================================
# Test Expired License
# =====================================================

class TestExpiredLicense:
    """تست لایسنس منقضی"""

    @pytest.mark.asyncio
    async def test_validate_expired_license(
        self, license_service, expired_license_data
    ):
        """تست اعتبارسنجی لایسنس منقضی"""
        with patch.object(license_service, '_get_license', return_value=expired_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key=expired_license_data["license_key"]
                )

        assert result.allowed is False
        assert BlockedReason.LICENSE_EXPIRED.value in result.blocked_reasons
        assert result.days_remaining == 0

    @pytest.mark.asyncio
    async def test_expired_license_status(
        self, license_service, expired_license_data
    ):
        """تست وضعیت لایسنس منقضی"""
        with patch.object(license_service, '_get_license', return_value=expired_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key=expired_license_data["license_key"]
                )

        assert result.status == "expired"

    @pytest.mark.asyncio
    async def test_license_expires_today(
        self, license_service
    ):
        """تست لایسنس که امروز منقضی می‌شود"""
        expiring_license = {
            "id": "license-expiring",
            "license_key": "MT5-EXPIRING-1234",
            "user_id": "user-123",
            "license_type": "basic",
            "status": "active",
            "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
            "max_devices": 1,
        }

        with patch.object(license_service, '_get_license', return_value=expiring_license):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key=expiring_license["license_key"]
                )

        assert result.allowed is True  # هنوز معتبر است
        assert result.days_remaining == 0  # کمتر از یک روز


# =====================================================
# Test Revoked License
# =====================================================

class TestRevokedLicense:
    """تست لایسنس ابطال شده"""

    @pytest.mark.asyncio
    async def test_validate_revoked_license(
        self, license_service, revoked_license_data
    ):
        """تست اعتبارسنجی لایسنس ابطال شده"""
        with patch.object(license_service, '_get_license', return_value=revoked_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key=revoked_license_data["license_key"]
                )

        assert result.allowed is False
        assert BlockedReason.LICENSE_REVOKED.value in result.blocked_reasons

    @pytest.mark.asyncio
    async def test_revoked_license_message(
        self, revoked_license_data
    ):
        """تست پیام خطای لایسنس ابطال شده"""
        result = LicenseValidationResult(
            allowed=False,
            blocked_reasons=[BlockedReason.LICENSE_REVOKED.value]
        )

        message = result.get_block_message()
        assert "ابطال" in message


# =====================================================
# Test Suspended License
# =====================================================

class TestSuspendedLicense:
    """تست لایسنس تعلیق شده"""

    @pytest.mark.asyncio
    async def test_validate_suspended_license(
        self, license_service, suspended_license_data
    ):
        """تست اعتبارسنجی لایسنس تعلیق شده"""
        with patch.object(license_service, '_get_license', return_value=suspended_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key=suspended_license_data["license_key"]
                )

        assert result.allowed is False
        assert BlockedReason.LICENSE_SUSPENDED.value in result.blocked_reasons


# =====================================================
# Test Device Limit
# =====================================================

class TestDeviceLimit:
    """تست محدودیت دستگاه"""

    @pytest.mark.asyncio
    async def test_device_limit_reached(
        self, license_service, active_license_data
    ):
        """تست رسیدن به محدودیت دستگاه"""
        # 3 دستگاه از قبل ثبت شده
        existing_devices = [
            {"device_id": "DEV-001", "is_active": True},
            {"device_id": "DEV-002", "is_active": True},
            {"device_id": "DEV-003", "is_active": True},
        ]

        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch.object(license_service, '_check_device_limit', return_value=BlockedReason.DEVICE_LIMIT_REACHED.value):
                with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                    result = await license_service.validate(
                        license_key=active_license_data["license_key"],
                        device_id="DEV-004"  # دستگاه جدید
                    )

        assert result.allowed is False
        assert BlockedReason.DEVICE_LIMIT_REACHED.value in result.blocked_reasons

    @pytest.mark.asyncio
    async def test_existing_device_allowed(
        self, license_service, active_license_data
    ):
        """تست دستگاه موجود مجاز است"""
        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch.object(license_service, '_check_device_limit', return_value=None):
                with patch.object(license_service, '_update_device_usage', new_callable=AsyncMock):
                    with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                        result = await license_service.validate(
                            license_key=active_license_data["license_key"],
                            device_id="DEV-001"  # دستگاه موجود
                        )

        assert result.allowed is True


# =====================================================
# Test Features
# =====================================================

class TestLicenseFeatures:
    """تست ویژگی‌های لایسنس"""

    @pytest.mark.asyncio
    async def test_trial_features(self):
        """تست ویژگی‌های لایسنس آزمایشی"""
        features = PLAN_FEATURES.get(LicenseType.TRIAL, [])

        assert LicenseType.TRIAL in PLAN_FEATURES
        assert len(features) < len(PLAN_FEATURES[LicenseType.PRO])

    @pytest.mark.asyncio
    async def test_pro_has_auto_trading(self):
        """تست دسترسی Pro به معامله خودکار"""
        features = PLAN_FEATURES.get(LicenseType.PRO, [])
        feature_values = [f.value for f in features]

        assert "auto_trading" in feature_values

    @pytest.mark.asyncio
    async def test_trial_no_auto_trading(self):
        """تست عدم دسترسی Trial به معامله خودکار"""
        features = PLAN_FEATURES.get(LicenseType.TRIAL, [])
        feature_values = [f.value for f in features]

        assert "auto_trading" not in feature_values

    @pytest.mark.asyncio
    async def test_has_feature_method(
        self, license_service, active_license_data
    ):
        """تست متد has_feature"""
        with patch.object(license_service, 'validate', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = LicenseValidationResult(
                allowed=True,
                enabled_modules=["smc_analysis", "price_action", "auto_trading"]
            )

            has_feature = await license_service.has_feature(
                license_key="test-key",
                feature="auto_trading"
            )

            assert has_feature is True


# =====================================================
# Test Plan Limits
# =====================================================

class TestPlanLimits:
    """تست محدودیت‌های پلن"""

    @pytest.mark.asyncio
    async def test_check_limits_within_range(
        self, license_service, active_license_data
    ):
        """تست محدودیت‌ها در محدوده مجاز"""
        with patch.object(license_service, 'validate', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = LicenseValidationResult(
                allowed=True,
                limits=LicenseLimits(
                    max_accounts=3,
                    max_symbols=10,
                    max_trades_per_day=50
                )
            )

            result = await license_service.check_limits(
                license_key="test-key",
                account_count=2,
                symbol_count=5,
                trade_count_today=10
            )

            assert result["allowed"] is True
            assert len(result["reasons"]) == 0

    @pytest.mark.asyncio
    async def test_check_limits_exceeded(
        self, license_service, active_license_data
    ):
        """تست عبور از محدودیت"""
        with patch.object(license_service, 'validate', new_callable=AsyncMock) as mock_validate:
            mock_validate.return_value = LicenseValidationResult(
                allowed=True,
                limits=LicenseLimits(
                    max_trades_per_day=50
                )
            )

            result = await license_service.check_limits(
                license_key="test-key",
                trade_count_today=60  # بیشتر از حد
            )

            assert result["allowed"] is False
            assert BlockedReason.DAILY_TRADE_LIMIT_REACHED.value in result["reasons"]


# =====================================================
# Test License Not Found
# =====================================================

class TestLicenseNotFound:
    """تست لایسنس یافت نشد"""

    @pytest.mark.asyncio
    async def test_license_not_found(
        self, license_service
    ):
        """تست لایسنس ناموجود"""
        with patch.object(license_service, '_get_license', return_value=None):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result = await license_service.validate(
                    license_key="MT5-NOTFOUND-1234"
                )

        assert result.allowed is False
        assert BlockedReason.LICENSE_NOT_FOUND.value in result.blocked_reasons


# =====================================================
# Test License Management
# =====================================================

class TestLicenseManagement:
    """تست مدیریت لایسنس"""

    @pytest.mark.asyncio
    async def test_revoke_license(
        self, license_service, active_license_data
    ):
        """تست ابطال لایسنس"""
        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch('backend.services.license_service.db') as mock_db:
                mock_db.update = AsyncMock(return_value=[active_license_data])
                mock_db.insert = AsyncMock()

                result = await license_service.revoke_license(
                    license_key=active_license_data["license_key"],
                    reason="تست ابطال"
                )

        assert result is True

    @pytest.mark.asyncio
    async def test_extend_license(
        self, license_service, active_license_data
    ):
        """تست تمدید لایسنس"""
        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch('backend.services.license_service.db') as mock_db:
                mock_db.update = AsyncMock(return_value=[active_license_data])

                result = await license_service.extend_license(
                    license_key=active_license_data["license_key"],
                    days=30
                )

        assert "new_expiry" in result


# =====================================================
# Test Audit Logging
# =====================================================

class TestAuditLogging:
    """تست ثبت لاگ عملیات"""

    @pytest.mark.asyncio
    async def test_validation_logged(
        self, license_service, active_license_data
    ):
        """تست ثبت لاگ اعتبارسنجی"""
        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock) as mock_log:
                with patch('backend.services.license_service.audit_service') as mock_audit:
                    mock_audit.log_license = AsyncMock()

                    await license_service.validate(
                        license_key=active_license_data["license_key"]
                    )

                    # بررسی ثبت audit
                    mock_audit.log_license.assert_called_once()


# =====================================================
# Test Caching
# =====================================================

class TestCaching:
    """تست کش کردن"""

    @pytest.mark.asyncio
    async def test_cache_used(
        self, license_service, active_license_data
    ):
        """تست استفاده از کش"""
        # اولین درخواست
        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch.object(license_service, '_log_validation', new_callable=AsyncMock):
                result1 = await license_service.validate(
                    license_key=active_license_data["license_key"]
                )

        # کش باید ذخیره شده باشد
        assert active_license_data["license_key"] in license_service._cache

    @pytest.mark.asyncio
    async def test_cache_cleared_on_revoke(
        self, license_service, active_license_data
    ):
        """تست پاک شدن کش هنگام ابطال"""
        # اضافه کردن به کش
        license_service._cache[active_license_data["license_key"]] = {"test": "data"}

        with patch.object(license_service, '_get_license', return_value=active_license_data):
            with patch('backend.services.license_service.db') as mock_db:
                mock_db.update = AsyncMock(return_value=[active_license_data])
                mock_db.insert = AsyncMock()

                await license_service.revoke_license(
                    license_key=active_license_data["license_key"]
                )

        # کش باید پاک شده باشد
        assert active_license_data["license_key"] not in license_service._cache


# =====================================================
# Run Tests
# =====================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
