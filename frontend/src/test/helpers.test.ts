/**
 * تست توابع کمکی
 */

import { describe, it, expect } from 'vitest';
import {
  formatNumber,
  formatPercent,
  calculateWinRate,
  calculateProfitFactor,
  calculateAvgProfit,
  getTradeStatusText,
  getDirectionText,
  getActiveKillZone,
  getScoreClass,
  truncateText,
  deepClone,
  debounce
} from '@/utils/helpers';

describe('توابع فرمت', () => {
  it('formatNumber عدد را با جداکننده فارسی برمی‌گرداند', () => {
    expect(formatNumber(1234.56)).toMatch(/۱٬۲۳۴/);
    expect(formatNumber(100)).toMatch(/۱۰۰/);
  });

  it('formatPercent درصد را با علامت برمی‌گرداند', () => {
    expect(formatPercent(10.5)).toBe('+10.50%');
    expect(formatPercent(-5.25)).toBe('-5.25%');
  });
});

describe('توابع محاسبات معاملات', () => {
  const trades = [
    { id: '1', symbol: 'EURUSD', direction: 'buy', status: 'closed', entry_price: 1.1, profit_money: 100, stop_loss: 1.09, take_profit: 1.12, opened_at: '2024-01-01' },
    { id: '2', symbol: 'GBPUSD', direction: 'sell', status: 'closed', entry_price: 1.25, profit_money: -50, stop_loss: 1.26, take_profit: 1.23, opened_at: '2024-01-02' },
    { id: '3', symbol: 'USDJPY', direction: 'buy', status: 'closed', entry_price: 150, profit_money: 200, stop_loss: 149, take_profit: 152, opened_at: '2024-01-03' },
  ] as const;

  it('calculateWinRate وین ریت را محاسبه می‌کند', () => {
    expect(calculateWinRate([...trades])).toBeCloseTo(66.67, 1);
  });

  it('calculateWinRate با آرایه خالی 0 برمی‌گرداند', () => {
    expect(calculateWinRate([])).toBe(0);
  });

  it('calculateProfitFactor فاکتور سود را محاسبه می‌کند', () => {
    const result = calculateProfitFactor([...trades]);
    expect(result).toBeCloseTo(6, 1); // 300 / 50
  });

  it('calculateAvgProfit میانگین سود را محاسبه می‌کند', () => {
    const result = calculateAvgProfit([...trades]);
    expect(result).toBeCloseTo(83.33, 1); // (100 - 50 + 200) / 3
  });
});

describe('توابع متن وضعیت', () => {
  it('getTradeStatusText متن فارسی وضعیت را برمی‌گرداند', () => {
    expect(getTradeStatusText('open')).toBe('باز');
    expect(getTradeStatusText('closed')).toBe('بسته شده');
    expect(getTradeStatusText('pending')).toBe('در انتظار');
    expect(getTradeStatusText('cancelled')).toBe('لغو شده');
  });

  it('getDirectionText متن فارسی جهت را برمی‌گرداند', () => {
    expect(getDirectionText('buy')).toBe('خرید');
    expect(getDirectionText('sell')).toBe('فروش');
  });
});

describe('تابع Kill Zone', () => {
  it('getActiveKillZone یک رشته برمی‌گرداند', () => {
    const result = getActiveKillZone();
    expect(typeof result).toBe('string');
    expect(['لندن', 'نیویورک', 'توکیو', 'سیدنی', 'خارج از Kill Zone']).toContain(result);
  });
});

describe('توابع امتیاز', () => {
  it('getScoreClass کلاس مناسب برای امتیاز بالا برمی‌گرداند', () => {
    expect(getScoreClass(85)).toContain('emerald');
    expect(getScoreClass(70)).toContain('sky');
    expect(getScoreClass(55)).toContain('amber');
    expect(getScoreClass(40)).toContain('rose');
  });
});

describe('توابع متن', () => {
  it('truncateText متن را کوتاه می‌کند', () => {
    expect(truncateText('Hello World', 5)).toBe('Hello...');
    expect(truncateText('Hi', 10)).toBe('Hi');
  });
});

describe('توابع عمومی', () => {
  it('deepClone یک کپی عمیق ایجاد می‌کند', () => {
    const original = { a: 1, b: { c: 2 } };
    const cloned = deepClone(original);

    expect(cloned).toEqual(original);
    expect(cloned).not.toBe(original);
    expect(cloned.b).not.toBe(original.b);
  });

  it('debounce تابع را با تاخیر فراخوانی می‌کند', async () => {
    let counter = 0;
    const increment = debounce(() => counter++, 10);

    increment();
    increment();
    increment();

    expect(counter).toBe(0);

    await new Promise(resolve => setTimeout(resolve, 20));
    expect(counter).toBe(1);
  });
});
