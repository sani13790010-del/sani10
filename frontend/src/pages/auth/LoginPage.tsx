/**
 * صفحه ورود
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, CircleAlert as AlertCircle, Activity } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در ورود');
    } finally {
      setIsLoading(false);
    }
  };

  const validateEmail = (value: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(value);
  };

  const isFormValid = email && password && password.length >= 6 && validateEmail(email);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4" dir="rtl">
      <div className="w-full max-w-md">
        {/* لوگو */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center mx-auto mb-4">
            <Activity className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">MT5 Trading</h1>
          <p className="text-slate-500 mt-2">سیستم معاملاتی پیشرفته</p>
        </div>

        {/* فرم */}
        <form onSubmit={handleSubmit} className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-lg font-semibold text-slate-100 mb-6 text-center">ورود به حساب کاربری</h2>

          {error && (
            <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
              <p className="text-rose-400 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            {/* ایمیل */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">ایمیل</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 transition-colors"
                placeholder="email@example.com"
                dir="ltr"
              />
              {email && !validateEmail(email) && (
                <p className="text-rose-400 text-xs mt-1">فرمت ایمیل نامعتبر است</p>
              )}
            </div>

            {/* رمز عبور */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">رمز عبور</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 transition-colors"
                  placeholder="حداقل ۶ کاراکتر"
                  dir="ltr"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {password && password.length < 6 && (
                <p className="text-rose-400 text-xs mt-1">رمز عبور باید حداقل ۶ کاراکتر باشد</p>
              )}
            </div>

            {/* دکمه ورود */}
            <button
              type="submit"
              disabled={!isFormValid || isLoading}
              className="w-full bg-sky-500/20 text-sky-400 py-3 rounded-lg font-medium hover:bg-sky-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin"></div>
                  در حال ورود...
                </span>
              ) : (
                'ورود'
              )}
            </button>
          </div>

          {/* لینک ثبت‌نام */}
          <div className="mt-6 text-center">
            <span className="text-slate-500">حساب کاربری ندارید؟</span>
            <Link to="/register" className="text-sky-400 hover:text-sky-300 mr-2">
              ثبت‌نام کنید
            </Link>
          </div>
        </form>

        {/* فوتر */}
        <p className="text-slate-600 text-center text-sm mt-6">
          نسخه 1.0.0 • MT5 Trading Team
        </p>
      </div>
    </div>
  );
}
