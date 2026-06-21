/**
 * انواع TypeScript پروژه
 *
 * نویسنده: MT5 Trading Team
 */

// نقش‌های کاربر
export type UserRole = 'user' | 'trader' | 'admin' | 'super_admin';

// وضعیت کاربر
export type UserStatus = 'active' | 'inactive' | 'suspended';

// کاربر
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  last_login_at?: string;
  updated_at?: string;
}

// تنظیمات کاربر
export interface UserSettings {
  user_id: string;
  default_symbol: string;
  default_lot: number;
  risk_per_trade: number;
  max_daily_trades: number;
  min_entry_score: number;
  telegram_notifications: boolean;
  default_timeframe: string;
}

// معامله
export interface Trade {
  id: string;
  user_id: string;
  symbol: string;
  direction: 'buy' | 'sell';
  status: 'pending' | 'open' | 'closed' | 'cancelled';
  volume: number;
  entry_price: number;
  current_price?: number;
  exit_price?: number;
  stop_loss: number;
  take_profit: number;
  profit_money: number;
  profit_points: number;
  open_reason: string;
  close_reason?: string;
  opened_at: string;
  closed_at?: string;
  signal_id?: string;
}

// سیگنال
export interface Signal {
  id: string;
  user_id: string;
  symbol: string;
  direction: 'buy' | 'sell';
  status: 'generated' | 'sent' | 'executed' | 'expired' | 'skipped';
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  total_score: number;
  smc_score: number;
  pa_score: number;
  reason: string;
  generated_at: string;
  valid_until: string;
  executed_at?: string;
  result?: 'win' | 'loss' | 'breakeven';
}

// تحلیل SMC
export interface SMCAnalysis {
  structure: {
    trend: 'bullish' | 'bearish' | 'ranging' | 'neutral';
    has_bos: boolean;
    has_choch: boolean;
    has_mss: boolean;
  };
  liquidity: {
    has_sweep: boolean;
    sweep_type?: 'wick' | 'impulse';
  };
  order_block: {
    detected: boolean;
    type?: 'bullish' | 'bearish';
    high?: number;
    low?: number;
  };
  fvg: {
    detected: boolean;
    high?: number;
    low?: number;
  };
  score: number;
}

// تحلیل Price Action
export interface PriceActionAnalysis {
  patterns: Pattern[];
  structure: {
    is_breakout: boolean;
    is_compression: boolean;
    is_expansion: boolean;
    momentum: number;
  };
  score: number;
}

// الگو
export interface Pattern {
  name: string;
  bias: 'bullish' | 'bearish' | 'neutral';
  strength: 'weak' | 'moderate' | 'strong';
  bar: number;
}

// تصمیم معاملاتی
export interface TradeDecision {
  symbol: string;
  timeframe: string;
  direction: 'buy' | 'sell' | 'neutral';
  total_score: number;
  entry_allowed: boolean;
  reason: string;
  levels: {
    entry: number;
    sl: number;
    tp: number;
  };
  filters_passed: string[];
  filters_failed: string[];
}

// گزارش
export interface Report {
  date: string;
  summary: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    gross_profit: number;
    gross_loss: number;
    net_profit: number;
  };
  trades?: Trade[];
}

// آمار عملکرد
export interface PerformanceStats {
  period: string;
  metrics: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    profit_factor: number;
    net_profit: number;
    avg_trade: number;
    gross_profit: number;
    gross_loss: number;
  };
}

// پاسخ API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// وضعیت اکانت
export interface AccountState {
  balance: number;
  equity: number;
  margin: number;
  free_margin: number;
  open_pnl: number;
  daily_pnl: number;
}

// Kill Zone
export interface KillZone {
  name: string;
  start: number;
  end: number;
  active: boolean;
}

// نماد
export interface Symbol {
  name: string;
  bid: number;
  ask: number;
  spread: number;
  change: number;
  change_percent: number;
}

// نمودار
export interface ChartData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// لایسنس
export interface License {
  id: string;
  user_id: string;
  plan_id?: string;
  license_key: string;
  status: 'inactive' | 'active' | 'expired' | 'revoked' | 'suspended';
  started_at?: string;
  expires_at?: string;
  created_at: string;
  max_devices: number;
  current_devices: number;
}

// پلن لایسنس
export interface LicensePlan {
  id: string;
  name: string;
  name_fa: string;
  description?: string;
  price: number;
  duration_days: number;
  max_devices: number;
  features: Record<string, boolean>;
  is_active: boolean;
}

// دستگاه لایسنس
export interface LicenseDevice {
  id: string;
  license_id: string;
  device_id: string;
  device_name: string;
  device_info?: string;
  first_seen: string;
  last_seen: string;
}

// حساب معاملاتی
export interface TradingAccount {
  id: string;
  user_id: string;
  account_number: string;
  broker_name: string;
  account_type: 'demo' | 'live' | 'contest';
  api_key?: string;
  api_secret?: string;
  is_connected: boolean;
  last_sync?: string;
  created_at: string;
  updated_at?: string;
}

// تصمیم
export interface Decision {
  id: string;
  user_id?: string;
  symbol: string;
  timeframe: string;
  decision: 'BUY' | 'SELL' | 'NO_TRADE' | 'CLOSE_BUY' | 'CLOSE_SELL' | 'HOLD';
  total_score: number;
  smc_score: number;
  pa_score: number;
  entry_allowed: boolean;
  reason: string;
  entry_price?: number;
  stop_loss?: number;
  take_profit?: number;
  created_at: string;
}

// اعلان
export interface Notification {
  id: string;
  user_id: string;
  type: 'telegram' | 'email' | 'push' | 'in_app';
  title: string;
  message: string;
  data?: Record<string, unknown>;
  read_at?: string;
  created_at: string;
}

// آمار روزانه
export interface DailyStatistics {
  id: string;
  user_id: string;
  date: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  gross_profit: number;
  gross_loss: number;
  net_profit: number;
  max_drawdown: number;
  profit_factor: number;
  created_at: string;
}

// لاگ فعالیت
export interface ActivityLog {
  id: string;
  user_id?: string;
  action: string;
  details: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

// تنظیمات تلگرام
export interface TelegramUser {
  id: string;
  user_id: string;
  telegram_id: string;
  telegram_username?: string;
  is_verified: boolean;
  linked_at: string;
  receive_signals: boolean;
  receive_reports: boolean;
  receive_alerts: boolean;
}

// سشن معاملاتی
export interface TradingSession {
  id: string;
  name: string;
  name_fa: string;
  start_hour: number;
  end_hour: number;
  is_active: boolean;
}

// تنظیمات سیستم
export interface SystemSetting {
  key: string;
  value: string;
  description?: string;
  is_public: boolean;
  updated_at: string;
}
