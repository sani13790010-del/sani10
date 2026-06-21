/**
 * صفحه لاگ‌های ممیزی (ادمین)
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { FileText, Search, ListFilter as Filter, Calendar, User, Activity, RefreshCw } from 'lucide-react';
import { auditService } from '@/services/api';
import { formatDate, formatRelativeTime } from '@/utils/helpers';
import type { ActivityLog } from '@/types';

const ACTION_LABELS: Record<string, string> = {
  login: 'ورود به سیستم',
  logout: 'خروج از سیستم',
  register: 'ثبت‌نام',
  password_change: 'تغییر رمز عبور',
  license_activate: 'فعال‌سازی لایسنس',
  license_deactivate: 'غیرفعال‌سازی لایسنس',
  settings_update: 'به‌روزرسانی تنظیمات',
  trade_open: 'باز کردن معامله',
  trade_close: 'بستن معامله',
  user_create: 'ایجاد کاربر',
  user_update: 'به‌روزرسانی کاربر',
  user_delete: 'حذف کاربر'
};

const ACTION_COLORS: Record<string, string> = {
  login: 'bg-sky-500/20 text-sky-400',
  logout: 'bg-slate-500/20 text-slate-400',
  register: 'bg-emerald-500/20 text-emerald-400',
  password_change: 'bg-amber-500/20 text-amber-400',
  license_activate: 'bg-emerald-500/20 text-emerald-400',
  license_deactivate: 'bg-rose-500/20 text-rose-400',
  settings_update: 'bg-violet-500/20 text-violet-400',
  trade_open: 'bg-sky-500/20 text-sky-400',
  trade_close: 'bg-amber-500/20 text-amber-400',
  user_create: 'bg-emerald-500/20 text-emerald-400',
  user_update: 'bg-amber-500/20 text-amber-400',
  user_delete: 'bg-rose-500/20 text-rose-400'
};

export function AuditLogsPage() {
  const [logs, setLogs] = useState<(ActivityLog & { user_profiles?: { email: string; first_name: string; last_name: string } })[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState<string>('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  useEffect(() => {
    loadLogs();
  }, [actionFilter, startDate, endDate]);

  const loadLogs = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await auditService.getLogs({
        action: actionFilter !== 'all' ? actionFilter : undefined,
        startDate: startDate ? new Date(startDate) : undefined,
        endDate: endDate ? new Date(endDate) : undefined,
        limit: 100
      });
      setLogs(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در دریافت لاگ‌ها');
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => {
    const user = log.user_profiles;
    const matchesSearch =
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user?.email?.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (user?.first_name?.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-12 h-12 border-4 border-sky-500/30 border-t-sky-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* هدر */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">لاگ‌های ممیزی</h1>
          <p className="text-slate-500 mt-1">تاریخچه فعالیت‌های سیستم</p>
        </div>
        <button
          onClick={loadLogs}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          به‌روزرسانی
        </button>
      </div>

      {/* خطا */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-rose-400">
          {error}
        </div>
      )}

      {/* فیلترها */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* جستجو */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="جستجو..."
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg pr-10 pl-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
              />
            </div>
          </div>

          {/* فیلتر عملیات */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            >
              <option value="all">همه عملیات</option>
              <option value="login">ورود</option>
              <option value="logout">خروج</option>
              <option value="register">ثبت‌نام</option>
              <option value="license_activate">فعال‌سازی لایسنس</option>
              <option value="settings_update">تغییر تنظیمات</option>
              <option value="trade_open">باز کردن معامله</option>
              <option value="trade_close">بستن معامله</option>
            </select>
          </div>

          {/* تاریخ شروع */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-500" />
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            />
          </div>

          {/* تاریخ پایان */}
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
          />
        </div>
      </div>

      {/* جدول لاگ‌ها */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-700/30 border-b border-slate-700/50">
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">زمان</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">کاربر</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">عملیات</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">جزئیات</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-12 text-slate-500">
                    لاگی یافت نشد
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const user = log.user_profiles;
                  return (
                    <tr
                      key={log.id}
                      className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                    >
                      <td className="px-4 py-4">
                        <div className="text-slate-300 text-sm">
                          {formatRelativeTime(log.created_at)}
                        </div>
                        <div className="text-slate-500 text-xs">
                          {formatDate(log.created_at, 'long')}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        {user ? (
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                              <User className="w-4 h-4 text-slate-400" />
                            </div>
                            <div>
                              <p className="text-slate-200 text-sm">
                                {user.first_name} {user.last_name}
                              </p>
                              <p className="text-slate-500 text-xs">{user.email}</p>
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-500">سیستم</span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${ACTION_COLORS[log.action] || 'bg-slate-500/20 text-slate-400'}`}>
                          <Activity className="w-3 h-3" />
                          {ACTION_LABELS[log.action] || log.action}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="max-w-xs">
                          {Object.keys(log.details || {}).length > 0 ? (
                            <code className="text-slate-400 text-xs font-mono block truncate">
                              {JSON.stringify(log.details)}
                            </code>
                          ) : (
                            <span className="text-slate-600">-</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className="text-slate-500 text-sm font-mono">
                          {log.ip_address || '0.0.0.0'}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
