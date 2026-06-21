/**
 * صفحه حساب‌های معاملاتی
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { CreditCard, Plus, MoveVertical as MoreVertical, RefreshCw, Trash2, CreditCard as Edit3, CircleCheck as CheckCircle, Circle as XCircle, Wifi, WifiOff } from 'lucide-react';
import { tradingAccountService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatRelativeTime } from '@/utils/helpers';
import type { TradingAccount } from '@/types';

const ACCOUNT_TYPE_LABELS = {
  demo: 'دمو',
  live: 'واقعی',
  contest: 'مسابقه'
};

const ACCOUNT_TYPE_COLORS = {
  demo: 'bg-sky-500/20 text-sky-400',
  live: 'bg-emerald-500/20 text-emerald-400',
  contest: 'bg-amber-500/20 text-amber-400'
};

export function TradingAccountsPage() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState<TradingAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testAccountId, setTestAccountId] = useState<string | null>(null);

  // فرم جدید
  const [formData, setFormData] = useState({
    account_number: '',
    broker_name: '',
    account_type: 'demo' as 'demo' | 'live' | 'contest',
    api_key: '',
    api_secret: ''
  });

  useEffect(() => {
    if (user) {
      loadAccounts();
    }
  }, [user]);

  const loadAccounts = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);

    try {
      const data = await tradingAccountService.getMyAccounts(user.id);
      setAccounts(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در دریافت حساب‌ها');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    setSaving(true);
    setError(null);

    try {
      await tradingAccountService.addAccount(user.id, formData);
      await loadAccounts();
      setShowModal(false);
      setFormData({
        account_number: '',
        broker_name: '',
        account_type: 'demo',
        api_key: '',
        api_secret: ''
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در افزودن حساب');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAccount = async (accountId: string) => {
    if (!confirm('آیا از حذف این حساب مطمئن هستید؟')) return;

    try {
      await tradingAccountService.deleteAccount(accountId);
      await loadAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در حذف حساب');
    }
  };

  const handleTestConnection = async (accountId: string) => {
    setTestAccountId(accountId);
    try {
      const result = await tradingAccountService.testConnection(accountId);
      if (result.connected) {
        await loadAccounts();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در تست اتصال');
    } finally {
      setTestAccountId(null);
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
          <h1 className="text-2xl font-bold text-slate-100">حساب‌های معاملاتی</h1>
          <p className="text-slate-500 mt-1">مدیریت حساب‌های MT5 متصل</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={loadAccounts}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            به‌روزرسانی
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-sky-500/20 text-sky-400 rounded-lg hover:bg-sky-500/30 transition-colors"
          >
            <Plus className="w-4 h-4" />
            افزودن حساب
          </button>
        </div>
      </div>

      {/* خطا */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-rose-400">
          {error}
        </div>
      )}

      {/* لیست حساب‌ها */}
      {accounts.length === 0 ? (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-12 text-center">
          <CreditCard className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-300 mb-2">حسابی ثبت نشده</h3>
          <p className="text-slate-500 mb-4">برای شروع معاملات، حساب MT5 خود را اضافه کنید</p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-sky-500/20 text-sky-400 rounded-lg hover:bg-sky-500/30 transition-colors"
          >
            <Plus className="w-4 h-4" />
            افزودن حساب
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6 hover:border-slate-600/50 transition-colors"
            >
              {/* هدر کارت */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    account.is_connected ? 'bg-emerald-500/20' : 'bg-slate-700/50'
                  }`}>
                    {account.is_connected ? (
                      <Wifi className="w-6 h-6 text-emerald-400" />
                    ) : (
                      <WifiOff className="w-6 h-6 text-slate-500" />
                    )}
                  </div>
                  <div>
                    <p className="text-slate-100 font-semibold">{account.broker_name}</p>
                    <p className="text-slate-500 text-sm">{account.account_number}</p>
                  </div>
                </div>

                <div className="relative">
                  <button
                    onClick={() => handleDeleteAccount(account.id)}
                    className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* نوع حساب */}
              <div className="mb-4">
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-medium ${ACCOUNT_TYPE_COLORS[account.account_type]}`}>
                  {ACCOUNT_TYPE_LABELS[account.account_type]}
                </span>
              </div>

              {/* وضعیت اتصال */}
              <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg mb-4">
                <div className="flex items-center gap-2">
                  {account.is_connected ? (
                    <>
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                      <span className="text-emerald-400 text-sm">متصل</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4 text-slate-500" />
                      <span className="text-slate-500 text-sm">قطع</span>
                    </>
                  )}
                </div>
                {account.last_sync && (
                  <span className="text-slate-600 text-xs">
                    آخرین سنک: {formatRelativeTime(account.last_sync)}
                  </span>
                )}
              </div>

              {/* دکمه‌های عملیات */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleTestConnection(account.id)}
                  disabled={testAccountId === account.id}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
                >
                  {testAccountId === account.id ? (
                    <div className="w-4 h-4 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin"></div>
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  تست اتصال
                </button>
                <button
                  className="px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* مودال افزودن حساب */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md" dir="rtl">
            <div className="p-6 border-b border-slate-700">
              <h3 className="text-lg font-semibold text-slate-100">افزودن حساب معاملاتی</h3>
            </div>

            <form onSubmit={handleAddAccount} className="p-6 space-y-4">
              {/* شماره حساب */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">شماره حساب</label>
                <input
                  type="text"
                  value={formData.account_number}
                  onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                  required
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
                  placeholder="12345678"
                  dir="ltr"
                />
              </div>

              {/* نام بروکر */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">نام بروکر</label>
                <input
                  type="text"
                  value={formData.broker_name}
                  onChange={(e) => setFormData({ ...formData, broker_name: e.target.value })}
                  required
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
                  placeholder="Exness, IC Markets, ..."
                />
              </div>

              {/* نوع حساب */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">نوع حساب</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['demo', 'live', 'contest'] as const).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setFormData({ ...formData, account_type: type })}
                      className={`py-2 rounded-lg text-sm font-medium transition-colors ${
                        formData.account_type === type
                          ? ACCOUNT_TYPE_COLORS[type]
                          : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {ACCOUNT_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>
              </div>

              {/* API Key */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">API Key (اختیاری)</label>
                <input
                  type="text"
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
                  placeholder="API Key"
                  dir="ltr"
                />
              </div>

              {/* API Secret */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">API Secret (اختیاری)</label>
                <input
                  type="password"
                  value={formData.api_secret}
                  onChange={(e) => setFormData({ ...formData, api_secret: e.target.value })}
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
                  placeholder="API Secret"
                  dir="ltr"
                />
              </div>

              {/* دکمه‌ها */}
              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-sky-500/20 text-sky-400 py-2 rounded-lg font-medium hover:bg-sky-500/30 transition-colors disabled:opacity-50"
                >
                  {saving ? 'در حال ذخیره...' : 'ذخیره'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-slate-700/50 text-slate-300 py-2 rounded-lg hover:bg-slate-700 transition-colors"
                >
                  انصراف
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
