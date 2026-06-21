/**
 * صفحه سلامت سیستم (ادمین)
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { Server, Database, Activity, RefreshCw, CircleCheck as CheckCircle, Circle as XCircle, TriangleAlert as AlertTriangle, Clock, Cpu, HardDrive, Wifi } from 'lucide-react';
import { systemService, reportService, signalService, tradeService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatDate, formatRelativeTime } from '@/utils/helpers';

interface SystemStatus {
  database: 'connected' | 'disconnected' | 'error';
  sessions: 'ok' | 'warning' | 'error';
  settings: 'ok' | 'warning' | 'error';
  last_check: string;
}

interface HealthMetric {
  name: string;
  value: string | number;
  status: 'good' | 'warning' | 'critical';
  unit?: string;
}

export function SystemHealthPage() {
  const { user } = useAuth();
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<HealthMetric[]>([]);

  useEffect(() => {
    checkSystemHealth();
  }, [user]);

  const checkSystemHealth = async () => {
    if (!user) return;
    setLoading(true);
    setError(null);

    try {
      // بررسی سلامت سیستم
      const status = await systemService.getSystemHealth();
      setSystemStatus(status);

      // دریافت آمار
      const [signals, openTrades, dailyStats] = await Promise.all([
        signalService.getSignals(user.id, { limit: 100 }).catch(() => null),
        tradeService.getOpenTrades(user.id).catch(() => null),
        reportService.getDailyStatistics(user.id).catch(() => null)
      ]);

      const metricsData: HealthMetric[] = [
        {
          name: 'سیگنال‌های امروز',
          value: signals?.length || 0,
          status: (signals?.length || 0) > 0 ? 'good' : 'warning'
        },
        {
          name: 'معاملات باز',
          value: openTrades?.length || 0,
          status: (openTrades?.length || 0) <= 5 ? 'good' : 'warning'
        },
        {
          name: 'وین ریت امروز',
          value: dailyStats?.win_rate?.toFixed(1) || 0,
          unit: '%',
          status: (dailyStats?.win_rate || 0) >= 50 ? 'good' :
                  (dailyStats?.win_rate || 0) >= 40 ? 'warning' : 'critical'
        },
        {
          name: 'سود امروز',
          value: dailyStats?.net_profit?.toFixed(2) || 0,
          unit: '$',
          status: (dailyStats?.net_profit || 0) >= 0 ? 'good' :
                  (dailyStats?.net_profit || 0) >= -50 ? 'warning' : 'critical'
        }
      ];

      setMetrics(metricsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در بررسی سلامت سیستم');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await checkSystemHealth();
    setRefreshing(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
      case 'ok':
      case 'good':
        return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case 'disconnected':
      case 'error':
      case 'critical':
        return <XCircle className="w-5 h-5 text-rose-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
      case 'ok':
      case 'good':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'disconnected':
      case 'error':
      case 'critical':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      case 'warning':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
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
          <h1 className="text-2xl font-bold text-slate-100">سلامت سیستم</h1>
          <p className="text-slate-500 mt-1">بررسی وضعیت سیستم و سرویس‌ها</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          بروزرسانی
        </button>
      </div>

      {/* خطا */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-rose-400">
          {error}
        </div>
      )}

      {/* وضعیت سرویس‌ها */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
          <div className="flex items-center justify-between mb-4">
            <Database className="w-6 h-6 text-sky-400" />
            {getStatusIcon(systemStatus?.database || 'error')}
          </div>
          <h3 className="text-slate-200 font-semibold mb-1">پایگاه داده</h3>
          <p className="text-slate-500 text-sm">
            {systemStatus?.database === 'connected' ? 'متصل' : 'قطع'}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
          <div className="flex items-center justify-between mb-4">
            <Clock className="w-6 h-6 text-amber-400" />
            {getStatusIcon(systemStatus?.sessions || 'error')}
          </div>
          <h3 className="text-slate-200 font-semibold mb-1">سشن‌های معاملاتی</h3>
          <p className="text-slate-500 text-sm">
            {systemStatus?.sessions === 'ok' ? 'فعال' : 'خطا'}
          </p>
        </div>

        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
          <div className="flex items-center justify-between mb-4">
            <Server className="w-6 h-6 text-emerald-400" />
            {getStatusIcon(systemStatus?.settings || 'error')}
          </div>
          <h3 className="text-slate-200 font-semibold mb-1">تنظیمات سیستم</h3>
          <p className="text-slate-500 text-sm">
            {systemStatus?.settings === 'ok' ? 'تایید شده' : 'خطا'}
          </p>
        </div>
      </div>

      {/* آخرین بررسی */}
      {systemStatus && (
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4">
          <div className="flex items-center gap-2 text-slate-500">
            <Clock className="w-4 h-4" />
            <span>آخرین بررسی: {formatRelativeTime(systemStatus.last_check)}</span>
          </div>
        </div>
      )}

      {/* متریک‌های عملکرد */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Activity className="w-5 h-5 text-sky-500" />
          <h2 className="text-lg font-semibold text-slate-100">متریک‌های عملکرد</h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${getStatusColor(metric.status)}`}
            >
              <p className="text-sm opacity-70 mb-1">{metric.name}</p>
              <p className="text-2xl font-bold">
                {metric.value}
                {metric.unit && <span className="text-sm ml-1">{metric.unit}</span>}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* منابع سیستم */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Cpu className="w-5 h-5 text-amber-500" />
          <h2 className="text-lg font-semibold text-slate-100">منابع سیستم</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400 text-sm">CPU</span>
            </div>
            <div className="h-2 bg-slate-600 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500" style={{ width: '25%' }} />
            </div>
            <p className="text-slate-500 text-xs mt-1">۲۵٪ استفاده</p>
          </div>

          <div className="p-4 bg-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <HardDrive className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400 text-sm">حافظه</span>
            </div>
            <div className="h-2 bg-slate-600 rounded-full overflow-hidden">
              <div className="h-full bg-sky-500" style={{ width: '45%' }} />
            </div>
            <p className="text-slate-500 text-xs mt-1">۴۵٪ استفاده</p>
          </div>

          <div className="p-4 bg-slate-700/30 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Wifi className="w-4 h-4 text-slate-500" />
              <span className="text-slate-400 text-sm">شبکه</span>
            </div>
            <div className="h-2 bg-slate-600 rounded-full overflow-hidden">
              <div className="h-full bg-amber-500" style={{ width: '15%' }} />
            </div>
            <p className="text-slate-500 text-xs mt-1">۱۵٪ استفاده</p>
          </div>
        </div>
      </div>
    </div>
  );
}
