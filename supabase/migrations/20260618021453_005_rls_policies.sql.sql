-- =====================================================
-- Migration: RLS Policies
-- =====================================================

-- user_settings policies
DROP POLICY IF EXISTS select_own_settings ON public.user_settings;
DROP POLICY IF EXISTS insert_own_settings ON public.user_settings;
DROP POLICY IF EXISTS update_own_settings ON public.user_settings;

CREATE POLICY select_own_settings ON public.user_settings FOR SELECT
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_own_settings ON public.user_settings FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_settings ON public.user_settings FOR UPDATE
    TO authenticated USING (auth.uid() = user_id);

-- trading_accounts policies
DROP POLICY IF EXISTS select_own_accounts ON public.trading_accounts;
DROP POLICY IF EXISTS insert_own_accounts ON public.trading_accounts;
DROP POLICY IF EXISTS update_own_accounts ON public.trading_accounts;
DROP POLICY IF EXISTS delete_own_accounts ON public.trading_accounts;

CREATE POLICY select_own_accounts ON public.trading_accounts FOR SELECT
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_own_accounts ON public.trading_accounts FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_accounts ON public.trading_accounts FOR UPDATE
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY delete_own_accounts ON public.trading_accounts FOR DELETE
    TO authenticated USING (auth.uid() = user_id);

-- signals policies
DROP POLICY IF EXISTS select_own_signals ON public.signals;
DROP POLICY IF EXISTS insert_own_signals ON public.signals;
DROP POLICY IF EXISTS update_own_signals ON public.signals;

CREATE POLICY select_own_signals ON public.signals FOR SELECT
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_own_signals ON public.signals FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id OR user_id IS NULL);
CREATE POLICY update_own_signals ON public.signals FOR UPDATE
    TO authenticated USING (auth.uid() = user_id);

-- decisions policies
DROP POLICY IF EXISTS select_own_decisions ON public.decisions;
DROP POLICY IF EXISTS insert_own_decisions ON public.decisions;

CREATE POLICY select_own_decisions ON public.decisions FOR SELECT
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_own_decisions ON public.decisions FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- trades policies
DROP POLICY IF EXISTS select_own_trades ON public.trades;
DROP POLICY IF EXISTS insert_own_trades ON public.trades;
DROP POLICY IF EXISTS update_own_trades ON public.trades;
DROP POLICY IF EXISTS delete_own_trades ON public.trades;

CREATE POLICY select_own_trades ON public.trades FOR SELECT
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY insert_own_trades ON public.trades FOR INSERT
    TO authenticated WITH CHECK (auth.uid() = user_id);
CREATE POLICY update_own_trades ON public.trades FOR UPDATE
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY delete_own_trades ON public.trades FOR DELETE
    TO authenticated USING (auth.uid() = user_id);

-- notifications policies
DROP POLICY IF EXISTS select_own_notifications ON public.notifications;
DROP POLICY IF EXISTS update_own_notifications ON public.notifications;

CREATE POLICY select_own_notifications ON public.notifications FOR SELECT
    TO authenticated USING (auth.uid() = user_id);
CREATE POLICY update_own_notifications ON public.notifications FOR UPDATE
    TO authenticated USING (auth.uid() = user_id);

-- daily_statistics policies
DROP POLICY IF EXISTS select_own_stats ON public.daily_statistics;
CREATE POLICY select_own_stats ON public.daily_statistics FOR SELECT
    TO authenticated USING (auth.uid() = user_id);

-- trading_sessions policies (عمومی)
DROP POLICY IF EXISTS select_sessions_all ON public.trading_sessions;
CREATE POLICY select_sessions_all ON public.trading_sessions FOR SELECT
    TO authenticated USING (TRUE);

-- system_settings policies
DROP POLICY IF EXISTS select_public_settings ON public.system_settings;
CREATE POLICY select_public_settings ON public.system_settings FOR SELECT
    TO authenticated USING (is_public = TRUE);

-- Admin policies
DROP POLICY IF EXISTS admin_all_access ON public.user_profiles;
CREATE POLICY admin_all_access ON public.user_profiles FOR ALL
    TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.user_id = auth.uid() AND up.role IN ('admin', 'super_admin')
        )
    );

DROP POLICY IF EXISTS admin_licenses_all ON public.licenses;
CREATE POLICY admin_licenses_all ON public.licenses FOR ALL
    TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.user_id = auth.uid() AND up.role IN ('admin', 'super_admin')
        )
    );

DROP POLICY IF EXISTS admin_logs_all ON public.activity_logs;
CREATE POLICY admin_logs_all ON public.activity_logs FOR SELECT
    TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.user_id = auth.uid() AND up.role IN ('admin', 'super_admin')
        )
    );

DROP POLICY IF EXISTS admin_settings_all ON public.system_settings;
CREATE POLICY admin_settings_all ON public.system_settings FOR ALL
    TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up 
            WHERE up.user_id = auth.uid() AND up.role IN ('admin', 'super_admin')
        )
    );

-- تابع محاسبه آمار روزانه
CREATE OR REPLACE FUNCTION calculate_daily_statistics(
    p_user_id UUID,
    p_date DATE
) RETURNS void AS $$
DECLARE
    v_total_trades INTEGER;
    v_winning_trades INTEGER;
    v_losing_trades INTEGER;
    v_gross_profit DECIMAL(12,4);
    v_gross_loss DECIMAL(12,4);
    v_net_profit DECIMAL(12,4);
    v_win_rate DECIMAL(5,2);
BEGIN
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE profit_money > 0),
        COUNT(*) FILTER (WHERE profit_money < 0),
        COALESCE(SUM(profit_money) FILTER (WHERE profit_money > 0), 0),
        COALESCE(SUM(profit_money) FILTER (WHERE profit_money < 0), 0),
        COALESCE(SUM(profit_money), 0)
    INTO v_total_trades, v_winning_trades, v_losing_trades, v_gross_profit, v_gross_loss, v_net_profit
    FROM public.trades
    WHERE user_id = p_user_id
      AND status = 'closed'
      AND DATE(closed_at) = p_date;

    v_win_rate := CASE WHEN v_total_trades > 0 
                       THEN ROUND((v_winning_trades::DECIMAL / v_total_trades) * 100, 2)
                       ELSE 0 END;

    INSERT INTO public.daily_statistics (
        user_id, stat_date, total_trades, winning_trades, losing_trades,
        gross_profit, gross_loss, net_profit, win_rate
    ) VALUES (
        p_user_id, p_date, v_total_trades, v_winning_trades, v_losing_trades,
        v_gross_profit, v_gross_loss, v_net_profit, v_win_rate
    )
    ON CONFLICT (user_id, stat_date) DO UPDATE SET
        total_trades = EXCLUDED.total_trades,
        winning_trades = EXCLUDED.winning_trades,
        losing_trades = EXCLUDED.losing_trades,
        gross_profit = EXCLUDED.gross_profit,
        gross_loss = EXCLUDED.gross_loss,
        net_profit = EXCLUDED.net_profit,
        win_rate = EXCLUDED.win_rate;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- تابع دریافت لایسنس فعال
CREATE OR REPLACE FUNCTION get_user_active_license(p_user_id UUID)
RETURNS TABLE (
    license_id UUID,
    license_key VARCHAR(64),
    license_type VARCHAR(30),
    status VARCHAR(20),
    expires_at TIMESTAMPTZ,
    days_remaining INTEGER,
    enabled_features JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id,
        l.license_key,
        l.license_type,
        l.status,
        l.expires_at,
        EXTRACT(DAY FROM (l.expires_at - NOW()))::INTEGER,
        COALESCE(lp.enabled_features, '[]'::jsonb)
    FROM public.licenses l
    LEFT JOIN public.license_plans lp ON lp.code = l.license_type
    WHERE l.user_id = p_user_id
      AND l.status = 'active'
      AND l.expires_at > NOW()
    ORDER BY l.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Seed تنظیمات سیستم
INSERT INTO public.system_settings (key, value, description, category, is_public)
VALUES
    ('system.version', '"2.0"'::jsonb, 'نسخه سیستم', 'system', TRUE),
    ('system.maintenance_mode', '"false"'::jsonb, 'حالت نگهداری', 'system', FALSE),
    ('trading.default_sl_pips', '"50"'::jsonb, 'SL پیش‌فرض', 'trading', TRUE),
    ('trading.default_tp_pips', '"100"'::jsonb, 'TP پیش‌فرض', 'trading', TRUE),
    ('trading.default_risk_percent', '"1"'::jsonb, 'ریسک پیش‌فرض', 'trading', TRUE),
    ('license.trial_days', '"7"'::jsonb, 'روزهای آزمایشی', 'license', TRUE)
ON CONFLICT (key) DO NOTHING;