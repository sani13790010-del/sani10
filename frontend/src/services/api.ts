/**
 * سرویس API - اتصال به Supabase
 *
 * نویسنده: MT5 Trading Team
 */

import { supabase } from '@/lib/supabase';
import type { User, UserSettings, Trade, Signal } from '@/types';

// ============ احراز هویت ============

export const authService = {
  async login(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });

    if (error) {
      if (error.message.includes('Invalid login credentials')) {
        throw new Error('ایمیل یا رمز عبور اشتباه است');
      }
      if (error.message.includes('Email not confirmed')) {
        throw new Error('ایمیل تایید نشده است');
      }
      throw new Error('خطا در ورود به سیستم');
    }

    return data;
  },

  async register(email: string, password: string, firstName?: string, lastName?: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          first_name: firstName,
          last_name: lastName
        }
      }
    });

    if (error) {
      if (error.message.includes('already registered')) {
        throw new Error('این ایمیل قبلاً ثبت شده است');
      }
      if (error.message.includes('Password')) {
        throw new Error('رمز عبور باید حداقل ۶ کاراکتر باشد');
      }
      throw new Error('خطا در ثبت‌نام');
    }

    return data;
  },

  async logout() {
    const { error } = await supabase.auth.signOut();
    if (error) throw new Error('خطا در خروج');
  },

  async getCurrentUser() {
    const { data: { user }, error } = await supabase.auth.getUser();
    if (error) throw new Error('خطا در دریافت کاربر');
    return user;
  },

  async getSession() {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error) throw new Error('خطا در دریافت نشست');
    return session;
  },

  onAuthStateChange(callback: (event: string, session: unknown) => void) {
    return supabase.auth.onAuthStateChange(callback);
  }
};

// ============ پروفایل کاربر ============

export const userService = {
  async getProfile(userId: string) {
    const { data, error } = await supabase
      .from('user_profiles')
      .select('*')
      .eq('id', userId)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error('خطا در دریافت پروفایل');
    }

    return data;
  },

  async updateProfile(userId: string, updates: Partial<User>) {
    const { data, error } = await supabase
      .from('user_profiles')
      .update(updates)
      .eq('id', userId)
      .select()
      .single();

    if (error) throw new Error('خطا در به‌روزرسانی پروفایل');
    return data;
  },

  async getSettings(userId: string): Promise<UserSettings | null> {
    const { data, error } = await supabase
      .from('user_settings')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error('خطا در دریافت تنظیمات');
    }

    return data;
  },

  async updateSettings(userId: string, settings: Partial<UserSettings>) {
    const { data, error } = await supabase
      .from('user_settings')
      .upsert({
        user_id: userId,
        ...settings,
        updated_at: new Date().toISOString()
      })
      .select()
      .single();

    if (error) throw new Error('خطا در ذخیره تنظیمات');
    return data;
  },

  // مدیریت کاربران (فقط ادمین)
  async getAllUsers(page = 1, limit = 20) {
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    const { data, error, count } = await supabase
      .from('user_profiles')
      .select('*', { count: 'exact' })
      .range(from, to)
      .order('created_at', { ascending: false });

    if (error) throw new Error('خطا در دریافت کاربران');
    return { data, count };
  },

  async updateUserStatus(userId: string, status: 'active' | 'inactive' | 'suspended') {
    const { data, error } = await supabase
      .from('user_profiles')
      .update({ status, updated_at: new Date().toISOString() })
      .eq('id', userId)
      .select()
      .single();

    if (error) throw new Error('خطا در به‌روزرسانی وضعیت کاربر');
    return data;
  },

  async updateUserRole(userId: string, role: 'user' | 'trader' | 'admin' | 'super_admin') {
    const { data, error } = await supabase
      .from('user_profiles')
      .update({ role, updated_at: new Date().toISOString() })
      .eq('id', userId)
      .select()
      .single();

    if (error) throw new Error('خطا در به‌روزرسانی نقش کاربر');
    return data;
  }
};

// ============ لایسنس ============

export const licenseService = {
  async getMyLicense(userId: string) {
    const { data, error } = await supabase
      .from('licenses')
      .select(`
        *,
        license_plans (*)
      `)
      .eq('user_id', userId)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error('خطا در دریافت لایسنس');
    }

    return data;
  },

  async getAllLicenses(page = 1, limit = 20) {
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    const { data, error, count } = await supabase
      .from('licenses')
      .select(`
        *,
        user_profiles (email, first_name, last_name),
        license_plans (*)
      `, { count: 'exact' })
      .range(from, to)
      .order('created_at', { ascending: false });

    if (error) throw new Error('خطا در دریافت لایسنس‌ها');
    return { data, count };
  },

  async activateLicense(userId: string, licenseKey: string) {
    const { data, error } = await supabase
      .rpc('activate_license', {
        p_user_id: userId,
        p_license_key: licenseKey
      });

    if (error) {
      if (error.message.includes('not found')) {
        throw new Error('لایسنس یافت نشد');
      }
      if (error.message.includes('expired')) {
        throw new Error('لایسنس منقضی شده است');
      }
      if (error.message.includes('already activated')) {
        throw new Error('لایسنس قبلاً فعال شده است');
      }
      throw new Error('خطا در فعال‌سازی لایسنس');
    }

    return data;
  },

  async checkLicenseStatus(userId: string) {
    const { data, error } = await supabase
      .rpc('get_user_active_license', { p_user_id: userId });

    if (error) throw new Error('خطا در بررسی وضعیت لایسنس');
    return data;
  },

  async getLicensePlans() {
    const { data, error } = await supabase
      .from('license_plans')
      .select('*')
      .eq('is_active', true)
      .order('price', { ascending: true });

    if (error) throw new Error('خطا در دریافت پلن‌ها');
    return data;
  },

  async getLicenseDevices(licenseId: string) {
    const { data, error } = await supabase
      .from('license_devices')
      .select('*')
      .eq('license_id', licenseId);

    if (error) throw new Error('خطا در دریافت دستگاه‌ها');
    return data;
  },

  async removeDevice(deviceId: string) {
    const { error } = await supabase
      .from('license_devices')
      .delete()
      .eq('id', deviceId);

    if (error) throw new Error('خطا در حذف دستگاه');
  }
};

// ============ حساب‌های معاملاتی ============

export const tradingAccountService = {
  async getMyAccounts(userId: string) {
    const { data, error } = await supabase
      .from('trading_accounts')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false });

    if (error) throw new Error('خطا در دریافت حساب‌ها');
    return data;
  },

  async addAccount(userId: string, account: {
    account_number: string;
    broker_name: string;
    account_type: 'demo' | 'live' | 'contest';
    api_key?: string;
    api_secret?: string;
  }) {
    const { data, error } = await supabase
      .from('trading_accounts')
      .insert({
        user_id: userId,
        ...account,
        is_connected: false
      })
      .select()
      .single();

    if (error) {
      if (error.message.includes('duplicate')) {
        throw new Error('این حساب قبلاً ثبت شده است');
      }
      throw new Error('خطا در افزودن حساب');
    }

    return data;
  },

  async updateAccount(accountId: string, updates: Partial<{
    broker_name: string;
    api_key: string;
    api_secret: string;
    is_connected: boolean;
  }>) {
    const { data, error } = await supabase
      .from('trading_accounts')
      .update({
        ...updates,
        updated_at: new Date().toISOString()
      })
      .eq('id', accountId)
      .select()
      .single();

    if (error) throw new Error('خطا در به‌روزرسانی حساب');
    return data;
  },

  async deleteAccount(accountId: string) {
    const { error } = await supabase
      .from('trading_accounts')
      .delete()
      .eq('id', accountId);

    if (error) throw new Error('خطا در حذف حساب');
  },

  async testConnection(accountId: string) {
    const { data, error } = await supabase
      .rpc('test_trading_account_connection', { p_account_id: accountId });

    if (error) throw new Error('خطا در تست اتصال');
    return data;
  }
};

// ============ سیگنال‌ها ============

export const signalService = {
  async getSignals(userId: string, filters?: {
    status?: string;
    symbol?: string;
    limit?: number;
  }) {
    let query = supabase
      .from('signals')
      .select('*')
      .eq('user_id', userId)
      .order('generated_at', { ascending: false });

    if (filters?.status) {
      query = query.eq('status', filters.status);
    }
    if (filters?.symbol) {
      query = query.eq('symbol', filters.symbol);
    }
    if (filters?.limit) {
      query = query.limit(filters.limit);
    }

    const { data, error } = await query;

    if (error) throw new Error('خطا در دریافت سیگنال‌ها');
    return data;
  },

  async getActiveSignals(userId: string) {
    const { data, error } = await supabase
      .from('signals')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'approved')
      .gte('valid_until', new Date().toISOString())
      .order('generated_at', { ascending: false });

    if (error) throw new Error('خطا در دریافت سیگنال‌های فعال');
    return data;
  },

  async getSignalById(signalId: string) {
    const { data, error } = await supabase
      .from('signals')
      .select('*')
      .eq('id', signalId)
      .single();

    if (error) throw new Error('خطا در دریافت سیگنال');
    return data;
  },

  async executeSignal(signalId: string) {
    const { data, error } = await supabase
      .from('signals')
      .update({
        status: 'executed',
        executed_at: new Date().toISOString()
      })
      .eq('id', signalId)
      .select()
      .single();

    if (error) throw new Error('خطا در اجرای سیگنال');
    return data;
  },

  async skipSignal(signalId: string, reason?: string) {
    const { data, error } = await supabase
      .from('signals')
      .update({
        status: 'rejected',
        reason: reason || 'رد شده توسط کاربر'
      })
      .eq('id', signalId)
      .select()
      .single();

    if (error) throw new Error('خطا در رد سیگنال');
    return data;
  }
};

// ============ تصمیم‌ها ============

export const decisionService = {
  async getDecisions(userId: string, limit = 50) {
    const { data, error } = await supabase
      .from('decisions')
      .select('*')
      .or(`user_id.eq.${userId},user_id.is.null`)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw new Error('خطا در دریافت تصمیم‌ها');
    return data;
  },

  async getLatestDecision(symbol: string, timeframe: string) {
    const { data, error } = await supabase
      .from('decisions')
      .select('*')
      .eq('symbol', symbol)
      .eq('timeframe', timeframe)
      .order('created_at', { ascending: false })
      .limit(1)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error('خطا در دریافت تصمیم');
    }

    return data;
  }
};

// ============ معاملات ============

export const tradeService = {
  async getTrades(userId: string, filters?: {
    status?: string;
    symbol?: string;
    direction?: string;
    limit?: number;
  }) {
    let query = supabase
      .from('trades')
      .select('*')
      .eq('user_id', userId)
      .order('opened_at', { ascending: false });

    if (filters?.status) {
      query = query.eq('status', filters.status);
    }
    if (filters?.symbol) {
      query = query.eq('symbol', filters.symbol);
    }
    if (filters?.direction) {
      query = query.eq('direction', filters.direction);
    }
    if (filters?.limit) {
      query = query.limit(filters.limit);
    }

    const { data, error } = await query;

    if (error) throw new Error('خطا در دریافت معاملات');
    return data;
  },

  async getOpenTrades(userId: string) {
    const { data, error } = await supabase
      .from('trades')
      .select('*')
      .eq('user_id', userId)
      .eq('status', 'open')
      .order('opened_at', { ascending: false });

    if (error) throw new Error('خطا در دریافت معاملات باز');
    return data;
  },

  async getTradeById(tradeId: string) {
    const { data, error } = await supabase
      .from('trades')
      .select('*')
      .eq('id', tradeId)
      .single();

    if (error) throw new Error('خطا در دریافت معامله');
    return data;
  },

  async closeTrade(tradeId: string, exitPrice: number, reason?: string) {
    const { data, error } = await supabase
      .from('trades')
      .update({
        status: 'closed',
        exit_price: exitPrice,
        close_reason: reason || 'بسته شده توسط کاربر',
        closed_at: new Date().toISOString()
      })
      .eq('id', tradeId)
      .select()
      .single();

    if (error) throw new Error('خطا در بستن معامله');
    return data;
  },

  async updateTrade(tradeId: string, updates: Partial<Trade>) {
    const { data, error } = await supabase
      .from('trades')
      .update(updates)
      .eq('id', tradeId)
      .select()
      .single();

    if (error) throw new Error('خطا در به‌روزرسانی معامله');
    return data;
  },

  async getTradeStats(userId: string, startDate?: Date, endDate?: Date) {
    let query = supabase
      .from('trades')
      .select('profit_money, status')
      .eq('user_id', userId)
      .eq('status', 'closed');

    if (startDate) {
      query = query.gte('closed_at', startDate.toISOString());
    }
    if (endDate) {
      query = query.lte('closed_at', endDate.toISOString());
    }

    const { data, error } = await query;

    if (error) throw new Error('خطا در دریافت آمار');

    const trades = data || [];
    const wins = trades.filter(t => (t.profit_money || 0) > 0);
    const losses = trades.filter(t => (t.profit_money || 0) < 0);

    return {
      total: trades.length,
      wins: wins.length,
      losses: losses.length,
      win_rate: trades.length > 0 ? (wins.length / trades.length) * 100 : 0,
      gross_profit: wins.reduce((sum, t) => sum + (t.profit_money || 0), 0),
      gross_loss: Math.abs(losses.reduce((sum, t) => sum + (t.profit_money || 0), 0)),
      net_profit: trades.reduce((sum, t) => sum + (t.profit_money || 0), 0)
    };
  }
};

// ============ گزارش‌ها و آمار ============

export const reportService = {
  async getDailyStatistics(userId: string, date?: Date) {
    const targetDate = date || new Date();
    const dateStr = targetDate.toISOString().split('T')[0];

    const { data, error } = await supabase
      .from('daily_statistics')
      .select('*')
      .eq('user_id', userId)
      .eq('date', dateStr)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error('خطا در دریافت آمار روزانه');
    }

    return data;
  },

  async getStatisticsRange(userId: string, startDate: Date, endDate: Date) {
    const { data, error } = await supabase
      .from('daily_statistics')
      .select('*')
      .eq('user_id', userId)
      .gte('date', startDate.toISOString().split('T')[0])
      .lte('date', endDate.toISOString().split('T')[0])
      .order('date', { ascending: true });

    if (error) throw new Error('خطا در دریافت آمار');
    return data;
  },

  async getPerformanceReport(userId: string, period: 'week' | 'month' | 'year' | 'all') {
    const now = new Date();
    let startDate: Date;

    switch (period) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'month':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'year':
        startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        startDate = new Date(0);
    }

    const stats = await this.getStatisticsRange(userId, startDate, now);
    const trades = await tradeService.getTradeStats(userId, startDate, now);

    // محاسبه میانگین‌ها
    const avgValues = stats.length > 0 ? {
      avg_win_rate: stats.reduce((sum, s) => sum + (s.win_rate || 0), 0) / stats.length,
      avg_trades_per_day: stats.reduce((sum, s) => sum + (s.total_trades || 0), 0) / stats.length,
      avg_profit_per_day: stats.reduce((sum, s) => sum + (s.net_profit || 0), 0) / stats.length
    } : {
      avg_win_rate: 0,
      avg_trades_per_day: 0,
      avg_profit_per_day: 0
    };

    return {
      ...trades,
      ...avgValues,
      days_traded: stats.length,
      period
    };
  }
};

// ============ اعلان‌ها ============

export const notificationService = {
  async getNotifications(userId: string, limit = 20) {
    const { data, error } = await supabase
      .from('notifications')
      .select('*')
      .eq('user_id', userId)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw new Error('خطا در دریافت اعلان‌ها');
    return data;
  },

  async markAsRead(notificationId: string) {
    const { error } = await supabase
      .from('notifications')
      .update({ read_at: new Date().toISOString() })
      .eq('id', notificationId);

    if (error) throw new Error('خطا در به‌روزرسانی اعلان');
  },

  async markAllAsRead(userId: string) {
    const { error } = await supabase
      .from('notifications')
      .update({ read_at: new Date().toISOString() })
      .eq('user_id', userId)
      .is('read_at', null);

    if (error) throw new Error('خطا در به‌روزرسانی اعلان‌ها');
  },

  async getUnreadCount(userId: string) {
    const { count, error } = await supabase
      .from('notifications')
      .select('*', { count: 'exact', head: true })
      .eq('user_id', userId)
      .is('read_at', null);

    if (error) throw new Error('خطا در دریافت تعداد اعلان‌ها');
    return count || 0;
  }
};

// ============ لاگ‌های ممیزی (ادمین) ============

export const auditService = {
  async getLogs(filters?: {
    userId?: string;
    action?: string;
    startDate?: Date;
    endDate?: Date;
    limit?: number;
  }) {
    let query = supabase
      .from('activity_logs')
      .select(`
        *,
        user_profiles (email, first_name, last_name)
      `)
      .order('created_at', { ascending: false });

    if (filters?.userId) {
      query = query.eq('user_id', filters.userId);
    }
    if (filters?.action) {
      query = query.eq('action', filters.action);
    }
    if (filters?.startDate) {
      query = query.gte('created_at', filters.startDate.toISOString());
    }
    if (filters?.endDate) {
      query = query.lte('created_at', filters.endDate.toISOString());
    }
    if (filters?.limit) {
      query = query.limit(filters.limit);
    }

    const { data, error } = await query;

    if (error) throw new Error('خطا در دریافت لاگ‌ها');
    return data;
  },

  async logAction(userId: string, action: string, details?: Record<string, unknown>) {
    const { error } = await supabase
      .from('activity_logs')
      .insert({
        user_id: userId,
        action,
        details: details || {},
        ip_address: '0.0.0.0',
        user_agent: navigator.userAgent
      });

    if (error) console.error('خطا در ثبت لاگ:', error);
  }
};

// ============ تنظیمات سیستم ============

export const systemService = {
  async getSettings() {
    const { data, error } = await supabase
      .from('system_settings')
      .select('*')
      .eq('is_public', true);

    if (error) throw new Error('خطا در دریافت تنظیمات سیستم');
    return data;
  },

  async updateSetting(key: string, value: string) {
    const { error } = await supabase
      .from('system_settings')
      .update({ value, updated_at: new Date().toISOString() })
      .eq('key', key);

    if (error) throw new Error('خطا در به‌روزرسانی تنظیمات');
  },

  async getTradingSessions() {
    const { data, error } = await supabase
      .from('trading_sessions')
      .select('*')
      .order('start_hour', { ascending: true });

    if (error) throw new Error('خطا در دریافت سشن‌های معاملاتی');
    return data;
  },

  async getSystemHealth() {
    const [sessionsResult, settingsResult] = await Promise.allSettled([
      this.getTradingSessions(),
      this.getSettings()
    ]);

    return {
      database: 'connected',
      sessions: sessionsResult.status === 'fulfilled' ? 'ok' : 'error',
      settings: settingsResult.status === 'fulfilled' ? 'ok' : 'error',
      last_check: new Date().toISOString()
    };
  }
};

// ============ تنظیمات تلگرام ============

export const telegramService = {
  async getUserTelegram(userId: string) {
    const { data, error } = await supabase
      .from('telegram_users')
      .select('*')
      .eq('user_id', userId)
      .single();

    if (error && error.code !== 'PGRST116') {
      throw new Error('خطا در دریافت اطلاعات تلگرام');
    }

    return data;
  },

  async linkTelegram(userId: string, telegramId: string, telegramUsername?: string) {
    const { data, error } = await supabase
      .from('telegram_users')
      .upsert({
        user_id: userId,
        telegram_id: telegramId,
        telegram_username: telegramUsername,
        is_verified: true,
        linked_at: new Date().toISOString()
      })
      .select()
      .single();

    if (error) throw new Error('خطا در اتصال تلگرام');
    return data;
  },

  async unlinkTelegram(userId: string) {
    const { error } = await supabase
      .from('telegram_users')
      .delete()
      .eq('user_id', userId);

    if (error) throw new Error('خطا در قطع اتصال تلگرام');
  },

  async updateTelegramSettings(userId: string, settings: {
    receive_signals?: boolean;
    receive_reports?: boolean;
    receive_alerts?: boolean;
  }) {
    const { data, error } = await supabase
      .from('telegram_users')
      .update(settings)
      .eq('user_id', userId)
      .select()
      .single();

    if (error) throw new Error('خطا در به‌روزرسانی تنظیمات تلگرام');
    return data;
  }
};

// ============ خذیره‌سازی داده‌ها (CRUD عمومی) ============

export const db = {
  from: (table: string) => supabase.from(table),

  rpc: async <T>(fn: string, params?: Record<string, unknown>): Promise<T> => {
    const { data, error } = await supabase.rpc(fn, params || {});
    if (error) throw error;
    return data;
  },

  storage: {
    from: (bucket: string) => supabase.storage.from(bucket)
  }
};
