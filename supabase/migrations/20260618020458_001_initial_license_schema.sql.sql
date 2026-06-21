-- =====================================================
-- اسکیمای اولیه اکوسیستم معامله‌گری MT5
-- نسخه: 1.0
-- =====================================================

-- فعال‌سازی پسوند UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- جدول پروفایل کاربران (در کنار auth.users)
-- =====================================================
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    telegram_id BIGINT UNIQUE,
    telegram_username VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    country VARCHAR(50),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'fa',
    avatar_url TEXT,
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'trader', 'admin', 'super_admin')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'banned', 'deleted')),
    mt5_account_linked BOOLEAN DEFAULT FALSE,
    mt5_account_number BIGINT,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- جدول لایسنس‌ها
-- =====================================================
CREATE TABLE public.licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key VARCHAR(64) UNIQUE NOT NULL,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    
    license_type VARCHAR(30) NOT NULL CHECK (license_type IN (
        'trial', 'basic', 'pro', 'enterprise', 'lifetime', 'developer'
    )),
    
    status VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('inactive', 'active', 'expired', 'revoked', 'suspended')),
    
    activated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    last_validated_at TIMESTAMPTZ,
    
    max_accounts INTEGER DEFAULT 1,
    max_symbols INTEGER DEFAULT 1,
    max_trades_per_day INTEGER DEFAULT 10,
    max_devices INTEGER DEFAULT 1,
    
    hardware_id VARCHAR(255),
    mt5_account_binding BIGINT[],
    
    notes TEXT,
    status_reason TEXT,
    revoked_at TIMESTAMPTZ,
    suspended_at TIMESTAMPTZ,
    suspended_by UUID REFERENCES public.user_profiles(id),
    revoked_by UUID REFERENCES public.user_profiles(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- جدول پلن‌های لایسنس
-- =====================================================
CREATE TABLE public.license_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_days INTEGER NOT NULL DEFAULT 30,
    max_accounts INTEGER DEFAULT 1,
    max_symbols INTEGER DEFAULT 1,
    max_trades_per_day INTEGER DEFAULT 10,
    max_devices INTEGER DEFAULT 1,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    enabled_features JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- پلن‌های پیش‌فرض
INSERT INTO public.license_plans (code, name, description, duration_days, max_accounts, max_symbols, max_trades_per_day, max_devices, enabled_features, sort_order) VALUES
('trial', 'Trial', '7-day trial license', 7, 1, 1, 5, 1, '["smc_analysis", "price_action", "signals"]'::jsonb, 1),
('basic', 'Basic', 'Monthly basic license', 30, 1, 3, 10, 2, '["smc_analysis", "price_action", "multi_timeframe", "manual_trading", "telegram_bot", "dashboard", "signals"]'::jsonb, 2),
('pro', 'Professional', '3-month professional license', 90, 3, 10, 50, 3, '["smc_analysis", "price_action", "multi_timeframe", "manual_trading", "auto_trading", "telegram_bot", "dashboard", "daily_reports", "advanced_reports", "api_access", "signals"]'::jsonb, 3),
('enterprise', 'Enterprise', 'Annual enterprise license', 365, 10, -1, -1, 10, '["smc_analysis", "price_action", "multi_timeframe", "manual_trading", "auto_trading", "telegram_bot", "dashboard", "daily_reports", "advanced_reports", "custom_strategies", "api_access", "signals", "priority_support"]'::jsonb, 4),
('lifetime', 'Lifetime', 'Lifetime license', 36500, 5, -1, -1, 5, '["smc_analysis", "price_action", "multi_timeframe", "manual_trading", "auto_trading", "telegram_bot", "dashboard", "daily_reports", "advanced_reports", "custom_strategies", "api_access", "signals"]'::jsonb, 5);

-- =====================================================
-- جدول دستگاه‌های لایسنس
-- =====================================================
CREATE TABLE public.license_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID NOT NULL REFERENCES public.licenses(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    device_name VARCHAR(100),
    device_type VARCHAR(50) DEFAULT 'mt5',
    hardware_id VARCHAR(255),
    mt5_account BIGINT,
    ip_address INET,
    user_agent TEXT,
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(license_id, device_id)
);

-- =====================================================
-- جدول اعتبارسنجی‌های لایسنس
-- =====================================================
CREATE TABLE public.license_validations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID REFERENCES public.licenses(id) ON DELETE SET NULL,
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    license_key VARCHAR(64),
    device_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    requested_features JSONB,
    is_valid BOOLEAN NOT NULL,
    status VARCHAR(20),
    blocked_reasons JSONB DEFAULT '[]'::jsonb,
    enabled_features JSONB DEFAULT '[]'::jsonb,
    limits JSONB DEFAULT '{}'::jsonb,
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- جدول activity logs
-- =====================================================
CREATE TABLE public.activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- ایندکس‌ها
-- =====================================================
CREATE INDEX idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX idx_licenses_license_key ON public.licenses(license_key);
CREATE INDEX idx_licenses_user_id ON public.licenses(user_id);
CREATE INDEX idx_licenses_status ON public.licenses(status);
CREATE INDEX idx_licenses_expires_at ON public.licenses(expires_at);
CREATE INDEX idx_license_devices_license_id ON public.license_devices(license_id);
CREATE INDEX idx_license_devices_device_id ON public.license_devices(device_id);
CREATE INDEX idx_license_validations_license_id ON public.license_validations(license_id);
CREATE INDEX idx_license_validations_created_at ON public.license_validations(created_at);
CREATE INDEX idx_activity_logs_user_id ON public.activity_logs(user_id);
CREATE INDEX idx_activity_logs_created_at ON public.activity_logs(created_at);

-- =====================================================
-- فعال‌سازی RLS
-- =====================================================
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.license_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- سیاست‌های RLS
-- =====================================================
CREATE POLICY "select_own_profile" ON public.user_profiles FOR SELECT TO authenticated USING (auth.uid() = user_id);
CREATE POLICY "insert_own_profile" ON public.user_profiles FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY "update_own_profile" ON public.user_profiles FOR UPDATE TO authenticated USING (auth.uid() = user_id);

CREATE POLICY "select_own_licenses" ON public.licenses FOR SELECT TO authenticated USING (user_id = auth.uid());
CREATE POLICY "license_plans_select_all" ON public.license_plans FOR SELECT TO authenticated USING (TRUE);

CREATE POLICY "select_own_devices" ON public.license_devices FOR SELECT TO authenticated USING (
    license_id IN (SELECT id FROM public.licenses WHERE user_id = auth.uid())
);

-- =====================================================
-- تابع به‌روزرسانی updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_licenses_updated_at BEFORE UPDATE ON public.licenses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- تابع اعتبارسنجی لایسنس
-- =====================================================
CREATE OR REPLACE FUNCTION validate_license(
    p_license_key VARCHAR(64),
    p_device_id VARCHAR(255) DEFAULT NULL,
    p_user_id UUID DEFAULT NULL,
    p_ip_address INET DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    v_license RECORD;
    v_plan RECORD;
    v_device_count INTEGER;
    v_days_remaining INTEGER;
    v_blocked_reasons JSONB := '[]'::jsonb;
    v_is_valid BOOLEAN := TRUE;
    v_status VARCHAR(20);
BEGIN
    SELECT * INTO v_license FROM public.licenses WHERE license_key = p_license_key;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'allowed', FALSE,
            'status', 'not_found',
            'blocked_reasons', '["LICENSE_NOT_FOUND"]'::jsonb,
            'checked_at', NOW()
        );
    END IF;
    
    v_status := v_license.status;
    
    IF v_license.expires_at < NOW() THEN
        v_blocked_reasons := v_blocked_reasons || '"LICENSE_EXPIRED"'::jsonb;
        v_is_valid := FALSE;
        v_status := 'expired';
    END IF;
    
    IF v_license.status = 'revoked' THEN
        v_blocked_reasons := v_blocked_reasons || '"LICENSE_REVOKED"'::jsonb;
        v_is_valid := FALSE;
    END IF;
    
    IF v_license.status = 'suspended' THEN
        v_blocked_reasons := v_blocked_reasons || '"LICENSE_SUSPENDED"'::jsonb;
        v_is_valid := FALSE;
    END IF;
    
    SELECT * INTO v_plan FROM public.license_plans WHERE code = v_license.license_type LIMIT 1;
    IF NOT FOUND THEN
        v_plan := ROW(NULL, NULL, NULL, NULL, 30, 1, 1, 10, 1, NULL, NULL, '[]'::jsonb, TRUE, 0, NOW(), NOW())::license_plans;
    END IF;
    
    IF p_device_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_device_count FROM public.license_devices WHERE license_id = v_license.id AND is_active = TRUE;
        
        IF NOT EXISTS (SELECT 1 FROM public.license_devices WHERE license_id = v_license.id AND device_id = p_device_id AND is_active = TRUE) THEN
            IF v_device_count >= COALESCE(v_plan.max_devices, v_license.max_devices, 1) THEN
                v_blocked_reasons := v_blocked_reasons || '"DEVICE_LIMIT_REACHED"'::jsonb;
                v_is_valid := FALSE;
            END IF;
        END IF;
    END IF;
    
    v_days_remaining := EXTRACT(DAY FROM (v_license.expires_at - NOW()));
    IF v_days_remaining < 0 THEN v_days_remaining := 0; END IF;
    
    INSERT INTO public.license_validations (
        license_id, user_id, license_key, device_id, ip_address,
        is_valid, status, blocked_reasons, enabled_features, limits
    ) VALUES (
        v_license.id, p_user_id, p_license_key, p_device_id, p_ip_address,
        v_is_valid, v_status, v_blocked_reasons,
        COALESCE(v_plan.enabled_features, '[]'::jsonb),
        jsonb_build_object(
            'max_accounts', COALESCE(v_license.max_accounts, v_plan.max_accounts, 1),
            'max_symbols', COALESCE(v_license.max_symbols, v_plan.max_symbols, 1),
            'max_trades_per_day', COALESCE(v_license.max_trades_per_day, v_plan.max_trades_per_day, 10),
            'max_devices', COALESCE(v_license.max_devices, v_plan.max_devices, 1)
        )
    );
    
    UPDATE public.licenses SET last_validated_at = NOW() WHERE id = v_license.id;
    
    RETURN jsonb_build_object(
        'allowed', v_is_valid,
        'user_id', v_license.user_id,
        'license_id', v_license.id,
        'plan', v_license.license_type,
        'status', v_status,
        'blocked_reasons', v_blocked_reasons,
        'limits', jsonb_build_object(
            'max_accounts', COALESCE(v_license.max_accounts, v_plan.max_accounts, 1),
            'max_symbols', COALESCE(v_license.max_symbols, v_plan.max_symbols, 1),
            'max_trades_per_day', COALESCE(v_license.max_trades_per_day, v_plan.max_trades_per_day, 10),
            'max_devices', COALESCE(v_license.max_devices, v_plan.max_devices, 1),
            'devices_used', COALESCE(v_device_count, 0)
        ),
        'enabled_modules', COALESCE(v_plan.enabled_features, '[]'::jsonb),
        'expires_at', v_license.expires_at,
        'days_remaining', v_days_remaining,
        'checked_at', NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;