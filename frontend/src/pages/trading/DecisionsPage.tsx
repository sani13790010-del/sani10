/**
 * صفحه تصمیم‌های معاملاتی
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { Brain, ListFilter as Filter, RefreshCw, TrendingUp, TrendingDown, Minus, Clock } from 'lucide-react';
import { decisionService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatDate, formatRelativeTime } from '@/utils/helpers';
import type { Decision } from '@/types';

const DECISION_LABELS = {
  BUY: 'خرید',
  SELL: 'فروش',
  NO_TRADE: 'بدون معامله',
  CLOSE_BUY: 'بستن خرید',
  CLOSE_SELL: 'بستن فروش',
  HOLD: 'نگه داشتن'
};

const DECISION_COLORS = {
  BUY: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  SELL: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  NO_TRADE: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  CLOSE_BUY: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  CLOSE_SELL: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  HOLD: 'bg-sky-500/20 text-sky-400 border-sky-500/30'
};

const DECISION_ICONS = {
  BUY: TrendingUp,
  SELL: TrendingDown,
  NO_TRADE: Minus,
  CLOSE_BUY: TrendingDown,
  CLOSE_SELL: TrendingUp,
  HOLD: Minus
};

export function DecisionsPage() {
  const { user } = useAuth();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [symbolFilter, setSymbolFilter] = useState<string>('all');
  const [decisionFilter, setDecisionFilter] = useState<string>('all');

  useEffect(() => {
    if (user) {
      loadDecisions();
    }
  }, [user]);

  const loadDecisions = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);

    try {
      const data = await decisionService.getDecisions(user.id, 100);
      setDecisions(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در دریافت تصمیم‌ها');
    } finally {
      setLoading(false);
    }
  };

  const uniqueSymbols = [...new Set(decisions.map(d => d.symbol))];

  const filteredDecisions = decisions.filter(d => {
    const matchesSymbol = symbolFilter === 'all' || d.symbol === symbolFilter;
    const matchesDecision = decisionFilter === 'all' || d.decision === decisionFilter;
    return matchesSymbol && matchesDecision;
  });

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-emerald-500';
    if (score >= 65) return 'text-sky-500';
    if (score >= 50) return 'text-amber-500';
    return 'text-rose-500';
  };

  const getScoreBg = (score: number): string => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 65) return 'bg-sky-500';
    if (score >= 50) return 'bg-amber-500';
    return 'bg-rose-500';
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
          <h1 className="text-2xl font-bold text-slate-100">تصمیم‌های معاملاتی</h1>
          <p className="text-slate-500 mt-1">خروجی سیستم تصمیم‌گیری</p>
        </div>
        <button
          onClick={loadDecisions}
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

      {/* آمار */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <span className="text-slate-500 text-sm">سیگنال خرید</span>
          </div>
          <p className="text-2xl font-bold text-emerald-500">
            {decisions.filter(d => d.decision === 'BUY').length}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-5 h-5 text-rose-400" />
            <span className="text-slate-500 text-sm">سیگنال فروش</span>
          </div>
          <p className="text-2xl font-bold text-rose-500">
            {decisions.filter(d => d.decision === 'SELL').length}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <Minus className="w-5 h-5 text-slate-400" />
            <span className="text-slate-500 text-sm">بدون معامله</span>
          </div>
          <p className="text-2xl font-bold text-slate-400">
            {decisions.filter(d => d.decision === 'NO_TRADE').length}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-5 h-5 text-sky-400" />
            <span className="text-slate-500 text-sm">کل تصمیم‌ها</span>
          </div>
          <p className="text-2xl font-bold text-slate-100">{decisions.length}</p>
        </div>
      </div>

      {/* فیلترها */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            >
              <option value="all">همه نمادها</option>
              {uniqueSymbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>

          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
          >
            <option value="all">همه تصمیم‌ها</option>
            <option value="BUY">خرید</option>
            <option value="SELL">فروش</option>
            <option value="NO_TRADE">بدون معامله</option>
            <option value="HOLD">نگه داشتن</option>
          </select>
        </div>
      </div>

      {/* لیست تصمیم‌ها */}
      {filteredDecisions.length === 0 ? (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-12 text-center">
          <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-300 mb-2">تصمیمی یافت نشد</h3>
          <p className="text-slate-500">سیستم هنوز تصمیمی تولید نکرده است</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredDecisions.map((decision) => {
            const Icon = DECISION_ICONS[decision.decision];
            return (
              <div
                key={decision.id}
                className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4 hover:border-slate-600/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center border ${DECISION_COLORS[decision.decision]}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-100">{decision.symbol}</span>
                        <span className="text-slate-500 text-sm">• {decision.timeframe}</span>
                      </div>
                      <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-sm font-medium mt-1 ${DECISION_COLORS[decision.decision]}`}>
                        {DECISION_LABELS[decision.decision]}
                      </div>
                    </div>
                  </div>

                  <div className="text-left">
                    <p className={`text-2xl font-bold ${getScoreColor(decision.total_score)}`}>
                      {decision.total_score}
                    </p>
                    <p className="text-slate-500 text-xs">امتیاز کل</p>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mb-4">
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getScoreBg(decision.total_score)} transition-all duration-500`}
                      style={{ width: `${decision.total_score}%` }}
                    />
                  </div>
                </div>

                {/* امتیازهای تفکیکی */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-2 bg-slate-700/30 rounded">
                    <p className="text-slate-500 text-xs">SMC</p>
                    <p className="text-slate-200 font-semibold">{decision.smc_score}</p>
                  </div>
                  <div className="text-center p-2 bg-slate-700/30 rounded">
                    <p className="text-slate-500 text-xs">Price Action</p>
                    <p className="text-slate-200 font-semibold">{decision.pa_score}</p>
                  </div>
                  <div className="text-center p-2 bg-slate-700/30 rounded">
                    <p className="text-slate-500 text-xs">اجازه ورود</p>
                    <p className={decision.entry_allowed ? 'text-emerald-400' : 'text-rose-400'}>
                      {decision.entry_allowed ? 'بله' : 'خیر'}
                    </p>
                  </div>
                </div>

                {/* سطوح */}
                {decision.entry_price && (
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-slate-700/50">
                    <div>
                      <p className="text-slate-500 text-xs mb-1">ورود</p>
                      <p className="text-slate-200 font-medium">{decision.entry_price}</p>
                    </div>
                    <div>
                      <p className="text-slate-500 text-xs mb-1">حد ضرر</p>
                      <p className="text-rose-400 font-medium">{decision.stop_loss}</p>
                    </div>
                    <div>
                      <p className="text-slate-500 text-xs mb-1">حد سود</p>
                      <p className="text-emerald-400 font-medium">{decision.take_profit}</p>
                    </div>
                  </div>
                )}

                {/* علت و زمان */}
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700/50">
                  <p className="text-slate-400 text-sm flex-1 truncate ml-4">{decision.reason}</p>
                  <div className="flex items-center gap-2 text-slate-500 text-sm">
                    <Clock className="w-4 h-4" />
                    {formatRelativeTime(decision.created_at)}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
