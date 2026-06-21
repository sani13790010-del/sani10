-- =====================================================
-- Migration: Create Missing Tables
-- =====================================================

-- جدول تنظیمات کاربر
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    
    default_symbol VARCHAR(20) DEFAULT 'XAUUSD',
    default_lot DECIMAL(10,4) DEFAULT 0.01,
    max_lot DECIMAL(10,4) DEFAULT 1.0,
    risk_per_trade DECIMAL(5,2) DEFAULT 2.0 CHECK (risk_per_trade > 0 AND risk_per_trade <= 10),
    max_daily_trades INTEGER DEFAULT 5,
    max_daily_loss DECIMAL(10,2) DEFAULT 5.0,
    max_drawdown DECIMAL(10,2) DEFAULT 20.0,
    default_sl_pips DECIMAL(10,2) DEFAULT 50.0,
    default_tp_pips DECIMAL(10,2) DEFAULT 100.0,
    use_trailing_stop BOOLEAN DEFAULT TRUE,
    trailing_stop_pips DECIMAL(10,2) DEFAULT 30.0,
    
    enabled_timeframes JSONB DEFAULT '["M15", "H1", "H4", "D1"]'::jsonb,
    primary_timeframe VARCHAR(10) DEFAULT 'H1',
    min_entry_score DECIMAL(5,2) DEFAULT 65.0,
    
    telegram_notifications BOOLEAN DEFAULT TRUE,
    notify_on_entry BOOLEAN DEFAULT TRUE,
    notify_on_exit BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id)
);

-- جدول حساب‌های معاملاتی
CREATE TABLE IF NOT EXISTS public.trading_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    
    mt5_account BIGINT NOT NULL,
    mt5_server VARCHAR(100) NOT NULL,
    account_name VARCHAR(100),
    account_type VARCHAR(20) DEFAULT 'demo' CHECK (account_type IN ('demo', 'live', 'contest')),
    broker VARCHAR(100),
    currency VARCHAR(10) DEFAULT 'USD',
    leverage INTEGER DEFAULT 100,
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    is_primary BOOLEAN DEFAULT FALSE,
    
    balance DECIMAL(15,2) DEFAULT 0,
    equity DECIMAL(15,2) DEFAULT 0,
    margin DECIMAL(15,2) DEFAULT 0,
    
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    
    UNIQUE(user_id, mt5_account)
);

-- جدول سیگنال‌ها
CREATE TABLE IF NOT EXISTS public.signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('entry', 'exit', 'close', 'modify')),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('buy', 'sell', 'neutral')),
    strength VARCHAR(20) DEFAULT 'moderate' CHECK (strength IN ('weak', 'moderate', 'strong', 'very_strong')),
    
    suggested_entry DECIMAL(20,8),
    suggested_sl DECIMAL(20,8),
    suggested_tp1 DECIMAL(20,8),
    stop_loss_pips DECIMAL(10,2),
    take_profit_pips DECIMAL(10,2),
    
    total_score DECIMAL(5,2) NOT NULL,
    smc_score DECIMAL(5,2),
    price_action_score DECIMAL(5,2),
    
    trigger_reasons JSONB DEFAULT '[]'::jsonb,
    smc_data JSONB DEFAULT '{}'::jsonb,
    price_action_data JSONB DEFAULT '{}'::jsonb,
    
    status VARCHAR(20) DEFAULT 'generated' CHECK (status IN ('generated', 'sent', 'executed', 'expired', 'cancelled')),
    trade_id UUID,
    
    sent_to_telegram BOOLEAN DEFAULT FALSE,
    telegram_message_id BIGINT,
    
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول تصمیم‌ها
CREATE TABLE IF NOT EXISTS public.decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.user_profiles(id) ON DELETE SET NULL,
    signal_id UUID REFERENCES public.signals(id) ON DELETE SET NULL,
    
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    
    decision VARCHAR(20) NOT NULL CHECK (decision IN ('BUY', 'SELL', 'NO_TRADE', 'CLOSE_BUY', 'CLOSE_SELL', 'HOLD')),
    direction VARCHAR(20) CHECK (direction IN ('bullish', 'bearish', 'neutral')),
    
    confidence_score INTEGER CHECK (confidence_score >= 0 AND confidence_score <= 100),
    quality_score INTEGER CHECK (quality_score >= 0 AND quality_score <= 100),
    
    allowed BOOLEAN DEFAULT TRUE,
    blocked BOOLEAN DEFAULT FALSE,
    blocked_reasons JSONB DEFAULT '[]'::jsonb,
    
    entry_zone DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    take_profit_1 DECIMAL(20,8),
    risk_reward DECIMAL(5,2),
    
    reason_codes JSONB DEFAULT '[]'::jsonb,
    reasons JSONB DEFAULT '[]'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول معاملات
CREATE TABLE IF NOT EXISTS public.trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    signal_id UUID REFERENCES public.signals(id) ON DELETE SET NULL,
    decision_id UUID REFERENCES public.decisions(id) ON DELETE SET NULL,
    
    mt5_ticket BIGINT UNIQUE,
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('buy', 'sell')),
    trade_type VARCHAR(20) DEFAULT 'market' CHECK (trade_type IN ('market', 'limit', 'stop')),
    
    entry_price DECIMAL(20,8) NOT NULL,
    exit_price DECIMAL(20,8),
    lot_size DECIMAL(10,4) NOT NULL,
    
    initial_sl DECIMAL(20,8),
    initial_tp DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    take_profit DECIMAL(20,8),
    
    profit_pips DECIMAL(10,2),
    profit_money DECIMAL(12,4),
    commission DECIMAL(10,4) DEFAULT 0,
    swap DECIMAL(10,4) DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'open', 'closed', 'cancelled')),
    close_reason VARCHAR(30) CHECK (close_reason IN ('manual', 'sl', 'tp', 'trailing_stop', 'stop_out', 'timeout')),
    
    entry_score DECIMAL(5,2),
    smc_score DECIMAL(5,2),
    total_score DECIMAL(5,2),
    
    analysis_summary JSONB,
    
    session VARCHAR(20) CHECK (session IN ('sydney', 'tokyo', 'london', 'new_york')),
    opened_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    duration_minutes INTEGER,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول اعلان‌ها
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    
    notification_type VARCHAR(30) NOT NULL CHECK (notification_type IN ('signal', 'trade_open', 'trade_close', 'trade_sl', 'trade_tp', 'system', 'license', 'risk')),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    channel VARCHAR(20) DEFAULT 'telegram' CHECK (channel IN ('telegram', 'email', 'push', 'in_app')),
    
    data JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    telegram_message_id BIGINT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول آمار روزانه
CREATE TABLE IF NOT EXISTS public.daily_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,
    
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2),
    
    gross_profit DECIMAL(12,4) DEFAULT 0,
    gross_loss DECIMAL(12,4) DEFAULT 0,
    net_profit DECIMAL(12,4) DEFAULT 0,
    
    max_drawdown DECIMAL(10,2) DEFAULT 0,
    
    signals_generated INTEGER DEFAULT 0,
    signals_executed INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, stat_date)
);

-- جدول تنظیمات سیستم
CREATE TABLE IF NOT EXISTS public.system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    key VARCHAR(100) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    
    is_public BOOLEAN DEFAULT FALSE,
    is_editable BOOLEAN DEFAULT TRUE,
    
    updated_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- جدول جلسات معاملاتی
CREATE TABLE IF NOT EXISTS public.trading_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(30) UNIQUE NOT NULL CHECK (session_name IN ('sydney', 'tokyo', 'london', 'new_york')),
    
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    
    killzone_start TIME,
    killzone_end TIME,
    
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 1,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed جلسات معاملاتی
INSERT INTO public.trading_sessions (session_name, open_time, close_time, killzone_start, killzone_end, priority)
VALUES
    ('sydney', '22:00', '07:00', '22:30', '23:30', 1),
    ('tokyo', '00:00', '09:00', '00:30', '02:00', 2),
    ('london', '08:00', '17:00', '08:00', '11:00', 3),
    ('new_york', '13:00', '22:00', '13:30', '16:00', 4)
ON CONFLICT (session_name) DO NOTHING;

-- ایندکس‌ها
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON public.trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON public.trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_status ON public.trades(status);
CREATE INDEX IF NOT EXISTS idx_trades_opened_at ON public.trades(opened_at);
CREATE INDEX IF NOT EXISTS idx_trades_mt5_ticket ON public.trades(mt5_ticket);

CREATE INDEX IF NOT EXISTS idx_signals_user_id ON public.signals(user_id);
CREATE INDEX IF NOT EXISTS idx_signals_status ON public.signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_generated_at ON public.signals(generated_at);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON public.notifications(status);

CREATE INDEX IF NOT EXISTS idx_daily_statistics_user_date ON public.daily_statistics(user_id, stat_date);

CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_id ON public.trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON public.user_settings(user_id);

-- RLS
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trading_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.daily_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trading_sessions ENABLE ROW LEVEL SECURITY;