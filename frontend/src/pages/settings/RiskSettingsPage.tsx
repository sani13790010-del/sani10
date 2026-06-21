/**
 * صفحه تنظیمات ریسک
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { Shield, Save, RefreshCw, TriangleAlert as AlertTriangle, CircleCheck as CheckCircle, Percent, DollarSign } from 'lucide-react';
import { userService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

export function RiskSettingsPage() {
  const { user, settings, updateSettings } = useAuth();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    risk_per_trade: 1.0,
    max_daily_loss: 5.0,
    max_daily_trades: 5,
    max_open_trades: 3,
    min_entry_score: 65,
    default_lot: 0.1,
    max_lot: 5.0,
    default_sl: 500,
    default_tp: 1000,
    min_sl: 100,
    max_sl: 2000,
    trailing_stop: 200,
    trailing_step: 20,
    break_even_trigger: 150,
    break_even_offset: 10
  });

  useEffect(() => {
    if (settings) {
      setFormData({
        ...formData,
        risk_per_trade: settings.risk_per_trade || 1.0,
        max_daily_trades: settings.max_daily_trades || 5,
        min_entry_score: settings.min_entry_score || 65,
        default_lot: settings.default_lot || 0.1
      });
    }
  }, [settings]);

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    setError(null);

    try {
      await updateSettings({
        risk_per_trade: formData.risk_per_trade,
        max_daily_trades: formData.max_daily_trades,
        min_entry_score: formData.min_entry_score,
        default_lot: formData.default_lot
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در ذخیره تنظیمات');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* هدر */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">تنظیمات ریسک</h1>
          <p className="text-slate-500 mt-1">مدیریت ریسک و سرمایه</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-sky-500/20 text-sky-400 rounded-lg hover:bg-sky-500/30 transition-colors disabled:opacity-50"
        >
          {saving ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          <span>{saving ? 'در حال ذخیره...' : 'ذخیره تغییرات'}</span>
        </button>
      </div>

      {/* پیام موفقیت */}
      {saved && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <span className="text-emerald-400">تنظیمات با موفقیت ذخیره شد</span>
        </div>
      )}

      {/* خطا */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          <span className="text-rose-400">{error}</span>
        </div>
      )}

      {/* مدیریت سرمایه */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <DollarSign className="w-5 h-5 text-emerald-500" />
          <h2 className="text-lg font-semibold text-slate-100">مدیریت سرمایه</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-slate-400 text-sm mb-2">ریسک هر معامله (%)</label>
            <input
              type="number"
              step="0.5"
              min="0.5"
              max="10"
              value={formData.risk_per_trade}
              onChange={(e) => setFormData({ ...formData, risk_per_trade: parseFloat(e.target.value) || 1 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            />
            <p className="text-slate-500 text-xs mt-1">پیشنهاد: ۱-۲٪</p>
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداکثر ضرر روزانه (%)</label>
            <input
              type="number"
              step="0.5"
              min="1"
              max="20"
              value={formData.max_daily_loss}
              onChange={(e) => setFormData({ ...formData, max_daily_loss: parseFloat(e.target.value) || 5 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            />
            <p className="text-slate-500 text-xs mt-1">پیشنهاد: ۳-۵٪</p>
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداکثر معاملات روزانه</label>
            <input
              type="number"
              min="1"
              max="20"
              value={formData.max_daily_trades}
              onChange={(e) => setFormData({ ...formData, max_daily_trades: parseInt(e.target.value) || 5 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداکثر معاملات همزمان</label>
            <input
              type="number"
              min="1"
              max="10"
              value={formData.max_open_trades}
              onChange={(e) => setFormData({ ...formData, max_open_trades: parseInt(e.target.value) || 3 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            />
            <p className="text-slate-500 text-xs mt-1">پیشنهاد: ۲-۳</p>
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">لات پیش‌فرض</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              max="10"
              value={formData.default_lot}
              onChange={(e) => setFormData({ ...formData, default_lot: parseFloat(e.target.value) || 0.1 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداکثر لات</label>
            <input
              type="number"
              step="0.1"
              min="0.1"
              max="100"
              value={formData.max_lot}
              onChange={(e) => setFormData({ ...formData, max_lot: parseFloat(e.target.value) || 5 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>
        </div>
      </div>

      {/* حد ضرر و سود */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Percent className="w-5 h-5 text-sky-500" />
          <h2 className="text-lg font-semibold text-slate-100">حد ضرر و سود</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-slate-400 text-sm mb-2">حد ضرر پیش‌فرض (پوینت)</label>
            <input
              type="number"
              step="50"
              min="50"
              max="5000"
              value={formData.default_sl}
              onChange={(e) => setFormData({ ...formData, default_sl: parseInt(e.target.value) || 500 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حد سود پیش‌فرض (پوینت)</label>
            <input
              type="number"
              step="100"
              min="100"
              max="10000"
              value={formData.default_tp}
              onChange={(e) => setFormData({ ...formData, default_tp: parseInt(e.target.value) || 1000 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداقل حد ضرر (پوینت)</label>
            <input
              type="number"
              step="10"
              min="10"
              max="500"
              value={formData.min_sl}
              onChange={(e) => setFormData({ ...formData, min_sl: parseInt(e.target.value) || 100 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداکثر حد ضرر (پوینت)</label>
            <input
              type="number"
              step="100"
              min="100"
              max="10000"
              value={formData.max_sl}
              onChange={(e) => setFormData({ ...formData, max_sl: parseInt(e.target.value) || 2000 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>
        </div>
      </div>

      {/* مدیریت پوزیشن */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="w-5 h-5 text-amber-500" />
          <h2 className="text-lg font-semibold text-slate-100">مدیریت پوزیشن</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-slate-400 text-sm mb-2">تریلینگ استاپ (پوینت)</label>
            <input
              type="number"
              step="10"
              min="10"
              max="1000"
              value={formData.trailing_stop}
              onChange={(e) => setFormData({ ...formData, trailing_stop: parseInt(e.target.value) || 200 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">گام تریلینگ (پوینت)</label>
            <input
              type="number"
              step="5"
              min="5"
              max="100"
              value={formData.trailing_step}
              onChange={(e) => setFormData({ ...formData, trailing_step: parseInt(e.target.value) || 20 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">تریگر بریک ایون (پوینت)</label>
            <input
              type="number"
              step="10"
              min="10"
              max="500"
              value={formData.break_even_trigger}
              onChange={(e) => setFormData({ ...formData, break_even_trigger: parseInt(e.target.value) || 150 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">آفست بریک ایون (پوینت)</label>
            <input
              type="number"
              step="5"
              min="0"
              max="100"
              value={formData.break_even_offset}
              onChange={(e) => setFormData({ ...formData, break_even_offset: parseInt(e.target.value) || 10 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
              dir="ltr"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-sm mb-2">حداقل امتیاز ورود</label>
            <input
              type="number"
              min="50"
              max="90"
              value={formData.min_entry_score}
              onChange={(e) => setFormData({ ...formData, min_entry_score: parseInt(e.target.value) || 65 })}
              className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            />
            <p className="text-slate-500 text-xs mt-1">امتیاز ۰ تا ۱۰۰</p>
          </div>
        </div>
      </div>
    </div>
  );
}
