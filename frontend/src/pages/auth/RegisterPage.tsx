/**
 * صفحه ثبت‌نام
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, CircleAlert as AlertCircle, CircleCheck as CheckCircle, Activity } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError('');
  };

  const validateEmail = (value: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(value);
  };

  const validatePassword = (value: string): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    if (value.length < 6) errors.push('حداقل ۶ کاراکتر');
    if (!/[A-Z]/.test(value)) errors.push('یک حرف بزرگ');
    if (!/[0-9]/.test(value)) errors.push('یک عدد');
    return { valid: errors.length === 0, errors };
  };

  const passwordValidation = validatePassword(formData.password);
  const passwordsMatch = formData.password === formData.confirmPassword;
  const isFormValid =
    validateEmail(formData.email) &&
    passwordValidation.valid &&
    passwordsMatch &&
    formData.firstName.trim().length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await register(
        formData.email,
        formData.password,
        formData.firstName,
        formData.lastName
      );
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در ثبت‌نام');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4" dir="rtl">
      <div className="w-full max-w-md">
        {/* لوگو */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center mx-auto mb-4">
            <Activity className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">MT5 Trading</h1>
          <p className="text-slate-500 mt-2">ایجاد حساب کاربری جدید</p>
        </div>

        {/* فرم */}
        <form onSubmit={handleSubmit} className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-lg font-semibold text-slate-100 mb-6 text-center">ثبت‌نام</h2>

          {error && (
            <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
              <p className="text-rose-400 text-sm">{error}</p>
            </div>
          )}

          <div className="space-y-4">
            {/* نام و نام خانوادگی */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-slate-400 text-sm mb-2">نام</label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleChange('firstName', e.target.value)}
                  required
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 transition-colors"
                  placeholder="نام"
                />
              </div>
              <div>
                <label className="block text-slate-400 text-sm mb-2">نام خانوادگی</label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleChange('lastName', e.target.value)}
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 transition-colors"
                  placeholder="نام خانوادگی"
                />
              </div>
            </div>

            {/* ایمیل */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">ایمیل</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                required
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 transition-colors"
                placeholder="email@example.com"
                dir="ltr"
              />
              {formData.email && !validateEmail(formData.email) && (
                <p className="text-rose-400 text-xs mt-1">فرمت ایمیل نامعتبر است</p>
              )}
            </div>

            {/* رمز عبور */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">رمز عبور</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleChange('password', e.target.value)}
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

              {/* نمایش الزامات رمز عبور */}
              {formData.password && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    {formData.password.length >= 6 ? (
                      <CheckCircle className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-slate-500" />
                    )}
                    <span className={formData.password.length >= 6 ? 'text-emerald-400' : 'text-slate-500'}>
                      حداقل ۶ کاراکتر
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    {/[A-Z]/.test(formData.password) ? (
                      <CheckCircle className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-slate-500" />
                    )}
                    <span className={/[A-Z]/.test(formData.password) ? 'text-emerald-400' : 'text-slate-500'}>
                      یک حرف بزرگ
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    {/[0-9]/.test(formData.password) ? (
                      <CheckCircle className="w-3 h-3 text-emerald-500" />
                    ) : (
                      <AlertCircle className="w-3 h-3 text-slate-500" />
                    )}
                    <span className={/[0-9]/.test(formData.password) ? 'text-emerald-400' : 'text-slate-500'}>
                      یک عدد
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* تکرار رمز عبور */}
            <div>
              <label className="block text-slate-400 text-sm mb-2">تکرار رمز عبور</label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                required
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50 transition-colors"
                placeholder="تکرار رمز عبور"
                dir="ltr"
              />
              {formData.confirmPassword && !passwordsMatch && (
                <p className="text-rose-400 text-xs mt-1">رمز عبور مطابقت ندارد</p>
              )}
            </div>

            {/* دکمه ثبت‌نام */}
            <button
              type="submit"
              disabled={!isFormValid || isLoading}
              className="w-full bg-sky-500/20 text-sky-400 py-3 rounded-lg font-medium hover:bg-sky-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-sky-400/30 border-t-sky-400 rounded-full animate-spin"></div>
                  در حال ثبت‌نام...
                </span>
              ) : (
                'ثبت‌نام'
              )}
            </button>
          </div>

          {/* لینک ورود */}
          <div className="mt-6 text-center">
            <span className="text-slate-500">حساب کاربری دارید؟</span>
            <Link to="/login" className="text-sky-400 hover:text-sky-300 mr-2">
              وارد شوید
            </Link>
          </div>
        </form>

        {/* فوتر */}
        <p className="text-slate-600 text-center text-sm mt-6">
          با ثبت‌نام، شرایط استفاده را می‌پذیرید
        </p>
      </div>
    </div>
  );
}
