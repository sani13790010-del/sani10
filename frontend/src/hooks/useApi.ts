/**
 * هوک‌های API - استفاده از Supabase
 *
 * نویسنده: MT5 Trading Team
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  signalService,
  tradeService,
  decisionService,
  reportService,
  notificationService
} from '@/services/api';

// ============ هوک عمومی API ============

interface UseApiOptions<T> {
  fetchFn: () => Promise<T>;
  enabled?: boolean;
  initialData?: T;
}

interface UseApiReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useApi<T>(options: UseApiOptions<T>): UseApiReturn<T> {
  const { fetchFn, enabled = true, initialData } = options;
  const { user } = useAuth();

  const [data, setData] = useState<T | null>(initialData || null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled || !user) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطای ناشناخته');
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, enabled, user]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData
  };
}

// ============ هوک سیگنال‌ها ============

export function useSignals(filters?: {
  status?: string;
  symbol?: string;
  limit?: number;
}) {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve([]);
      return signalService.getSignals(user.id, filters);
    },
    enabled: !!user
  });
}

export function useActiveSignals() {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve([]);
      return signalService.getActiveSignals(user.id);
    },
    enabled: !!user
  });
}

// ============ هوک معاملات ============

export function useTrades(filters?: {
  status?: string;
  symbol?: string;
  direction?: string;
  limit?: number;
}) {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve([]);
      return tradeService.getTrades(user.id, filters);
    },
    enabled: !!user
  });
}

export function useOpenTrades() {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve([]);
      return tradeService.getOpenTrades(user.id);
    },
    enabled: !!user
  });
}

// ============ هوک تصمیم‌ها ============

export function useDecisions(limit = 50) {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve([]);
      return decisionService.getDecisions(user.id, limit);
    },
    enabled: !!user
  });
}

// ============ هوک گزارش‌ها ============

export function useDailyReport(date?: string) {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve(null);
      const targetDate = date ? new Date(date) : new Date();
      return reportService.getDailyStatistics(user.id, targetDate);
    },
    enabled: !!user
  });
}

export function useWeeklyReport() {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve(null);
      const now = new Date();
      const startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      return reportService.getStatisticsRange(user.id, startDate, now);
    },
    enabled: !!user
  });
}

export function useMonthlyReport(year?: number, month?: number) {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve(null);
      const now = new Date();
      const targetYear = year || now.getFullYear();
      const targetMonth = month || now.getMonth() + 1;
      const startDate = new Date(targetYear, targetMonth - 1, 1);
      const endDate = new Date(targetYear, targetMonth, 0);
      return reportService.getStatisticsRange(user.id, startDate, endDate);
    },
    enabled: !!user
  });
}

export function usePerformance(period: 'week' | 'month' | 'year' | 'all' = 'month') {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve(null);
      return reportService.getPerformanceReport(user.id, period);
    },
    enabled: !!user
  });
}

// ============ هوک اعلان‌ها ============

export function useNotifications(limit = 20) {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve([]);
      return notificationService.getNotifications(user.id, limit);
    },
    enabled: !!user
  });
}

export function useUnreadNotificationCount() {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve(0);
      return notificationService.getUnreadCount(user.id);
    },
    enabled: !!user
  });
}

// ============ هوک عملکرد نماد ============

export function useSymbolPerformance(symbol: string, period: 'week' | 'month' | 'year' = 'month') {
  const { user } = useAuth();

  return useApi({
    fetchFn: async () => {
      if (!user || !symbol) return null;

      const trades = await tradeService.getTrades(user.id, { symbol, limit: 100 });
      const closedTrades = trades.filter(t => t.status === 'closed');
      const wins = closedTrades.filter(t => (t.profit_money || 0) > 0);
      const losses = closedTrades.filter(t => (t.profit_money || 0) < 0);

      return {
        total: closedTrades.length,
        wins: wins.length,
        losses: losses.length,
        win_rate: closedTrades.length > 0 ? (wins.length / closedTrades.length) * 100 : 0,
        gross_profit: wins.reduce((sum, t) => sum + (t.profit_money || 0), 0),
        gross_loss: Math.abs(losses.reduce((sum, t) => sum + (t.profit_money || 0), 0)),
        net_profit: closedTrades.reduce((sum, t) => sum + (t.profit_money || 0), 0)
      };
    },
    enabled: !!user && !!symbol
  });
}

// ============ هوک آمار معاملات ============

export function useTradeStats() {
  const { user } = useAuth();

  return useApi({
    fetchFn: () => {
      if (!user) return Promise.resolve(null);
      return tradeService.getTradeStats(user.id);
    },
    enabled: !!user
  });
}
