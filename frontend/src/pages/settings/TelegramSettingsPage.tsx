/**
 * صفحه تنظیمات تلگرام
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { MessageCircle, Link, Unlink, Bell, ChartBar as BarChart3, TriangleAlert as AlertTriangle, Save, RefreshCw, CircleCheck as CheckCircle, Circle as XCircle } from 'lucide-react';
import { telegramService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import type { TelegramUser } from '@/types';

export function TelegramSettingsPage() {
  const { user } = useAuth();
  const [telegramUser, setTelegramUser] = useState<TelegramUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [settings, setSettings] = useState({
    receive_signals: true,
    receive_reports: true,
    receive_alerts: true
  });

  useEffect(() => {
    if (user) {
      loadTelegramData();
    }
  }, [user]);

  const loadTelegramData = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);

    try {
      const data = await telegramService.getUserTelegram(user.id);
      if (data) {
        setTelegramUser(data);
        setSettings({
          receive_signals: data.receive_signals ?? true,
          receive_reports: data.receive_reports ?? true,
          receive_alerts: data.receive_alerts ?? true
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در دریافت داده‌ها');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    if (!user || !telegramUser) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await telegramService.updateTelegramSettings(user.id, settings);
      setSuccess('تنظیمات با موفقیت ذخیره شد');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در ذخیره تنظیمات');
    } finally {
      setSaving(false);
    }
  };

  const handleUnlink = async () => {
    if (!user) return;
    if (!confirm('آیا از قطع اتصال تلگرام مطمئن هستید؟')) return;

    try {
      await telegramService.unlinkTelegram(user.id);
      setTelegramUser(null);
      setSuccess('اتصال تلگرام قطع شد');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در قطع اتصال');
    }
  };

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
          <h1 className="text-2xl font-bold text-slate-100">تنظیمات تلگرام</h1>
          <p className="text-slate-500 mt-1">اتصال و پیکربندی ربات تلگرام</p>
        </div>
      </div>

      {/* پیام‌ها */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 flex items-center gap-2">
          <XCircle className="w-5 h-5 text-rose-400" />
          <span className="text-rose-400">{error}</span>
        </div>
      )}

      {success && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <span className="text-emerald-400">{success}</span>
        </div>
      )}

      {/* وضعیت اتصال */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <MessageCircle className="w-5 h-5 text-sky-500" />
          <h2 className="text-lg font-semibold text-slate-100">وضعیت اتصال</h2>
        </div>

        {telegramUser ? (
          <div className="space-y-4">
            {/* اطلاعات حساب */}
            <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-sky-500/20 flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-sky-400" />
                </div>
                <div>
                  <p className="text-slate-200 font-medium">
                    {telegramUser.telegram_username ? `@${telegramUser.telegram_username}` : 'متصل'}
                  </p>
                  <p className="text-slate-500 text-sm">ID: {telegramUser.telegram_id}</p>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/20 rounded-lg">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="text-emerald-400 text-sm">
                    {telegramUser.is_verified ? 'تایید شده' : 'متصل'}
                  </span>
                </div>
                <button
                  onClick={handleUnlink}
                  className="flex items-center gap-2 px-3 py-2 text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                >
                  <Unlink className="w-4 h-4" />
                  قطع اتصال
                </button>
              </div>
            </div>

            {/* تنظیمات اعلان‌ها */}
            <div className="space-y-3">
              <h3 className="text-slate-400 text-sm font-medium">نوع اعلان‌ها</h3>

              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <Bell className="w-5 h-5 text-amber-400" />
                  <div>
                    <p className="text-slate-200 font-medium">سیگنال‌های معاملاتی</p>
                    <p className="text-slate-500 text-sm">دریافت سیگنال‌های جدید</p>
                  </div>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, receive_signals: !settings.receive_signals })}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings.receive_signals ? 'bg-sky-500' : 'bg-slate-600'
                  }`}
                >
                  <div
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${
                      settings.receive_signals ? 'right-1' : 'left-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <BarChart3 className="w-5 h-5 text-emerald-400" />
                  <div>
                    <p className="text-slate-200 font-medium">گزارش‌های روزانه</p>
                    <p className="text-slate-500 text-sm">خلاصه عملکرد روزانه</p>
                  </div>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, receive_reports: !settings.receive_reports })}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings.receive_reports ? 'bg-sky-500' : 'bg-slate-600'
                  }`}
                >
                  <div
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${
                      settings.receive_reports ? 'right-1' : 'left-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-rose-400" />
                  <div>
                    <p className="text-slate-200 font-medium">هشدارهای مهم</p>
                    <p className="text-slate-500 text-sm">هشدارهای ریسک و امنیت</p>
                  </div>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, receive_alerts: !settings.receive_alerts })}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings.receive_alerts ? 'bg-sky-500' : 'bg-slate-600'
                  }`}
                >
                  <div
                    className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${
                      settings.receive_alerts ? 'right-1' : 'left-1'
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* دکمه ذخیره */}
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="w-full flex items-center justify-center gap-2 bg-sky-500/20 text-sky-400 py-3 rounded-lg hover:bg-sky-500/30 transition-colors disabled:opacity-50"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  در حال ذخیره...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  ذخیره تنظیمات
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="w-20 h-20 rounded-full bg-slate-700/50 flex items-center justify-center mx-auto mb-4">
              <Link className="w-10 h-10 text-slate-500" />
            </div>
            <h3 className="text-lg font-semibold text-slate-300 mb-2">تلگرام متصل نیست</h3>
            <p className="text-slate-500 mb-6">
              برای دریافت سیگنال‌ها و گزارش‌ها، تلگرام خود را متصل کنید
            </p>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <p className="text-slate-400 text-sm mb-2">راهنمای اتصال:</p>
              <ol className="text-slate-500 text-sm text-right space-y-2">
                <li>۱. به ربات @MT5TradingBot در تلگرام بروید</li>
                <li>۲. دستور /start را ارسال کنید</li>
                <li>۳. دستور /link را ارسال کرده و کد دریافتی را وارد کنید</li>
              </ol>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
