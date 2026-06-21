/**
 * اپلیکیشن اصلی React
 *
 * نویسنده: MT5 Trading Team
 */

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import type { UserRole } from '@/types';

// لود تنبل صفحات برای بهبود عملکرد
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const TradesPage = lazy(() => import('@/pages/TradesPage').then(m => ({ default: m.TradesPage })));
const SignalsPage = lazy(() => import('@/pages/SignalsPage').then(m => ({ default: m.SignalsPage })));
const ReportsPage = lazy(() => import('@/pages/ReportsPage').then(m => ({ default: m.ReportsPage })));
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const AnalysisPage = lazy(() => import('@/pages/AnalysisPage').then(m => ({ default: m.AnalysisPage })));

// صفحات جدید
const LoginPage = lazy(() => import('@/pages/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage').then(m => ({ default: m.RegisterPage })));
const UserManagementPage = lazy(() => import('@/pages/admin/UserManagementPage').then(m => ({ default: m.UserManagementPage })));
const LicenseManagementPage = lazy(() => import('@/pages/admin/LicenseManagementPage').then(m => ({ default: m.LicenseManagementPage })));
const AuditLogsPage = lazy(() => import('@/pages/admin/AuditLogsPage').then(m => ({ default: m.AuditLogsPage })));
const TradingAccountsPage = lazy(() => import('@/pages/accounts/TradingAccountsPage').then(m => ({ default: m.TradingAccountsPage })));
const DecisionsPage = lazy(() => import('@/pages/trading/DecisionsPage').then(m => ({ default: m.DecisionsPage })));
const TelegramSettingsPage = lazy(() => import('@/pages/settings/TelegramSettingsPage').then(m => ({ default: m.TelegramSettingsPage })));
const RiskSettingsPage = lazy(() => import('@/pages/settings/RiskSettingsPage').then(m => ({ default: m.RiskSettingsPage })));
const SystemHealthPage = lazy(() => import('@/pages/system/SystemHealthPage').then(m => ({ default: m.SystemHealthPage })));

// کامپوننت لودینگ
function LoadingSpinner() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center" dir="rtl">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-sky-500/30 border-t-sky-500 rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-slate-400">در حال بارگذاری...</p>
      </div>
    </div>
  );
}

// کامپوننت محافظت شده
function ProtectedRoute({
  children,
  requiredRoles
}: {
  children: React.ReactNode;
  requiredRoles?: UserRole[];
}) {
  const { isAuthenticated, isLoading, hasRole } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRoles && !hasRole(requiredRoles)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return (
    <Suspense fallback={<LoadingSpinner />}>
      {children}
    </Suspense>
  );
}

// صفحه عدم دسترسی
function UnauthorizedPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4" dir="rtl">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-slate-700 mb-4">403</h1>
        <h2 className="text-2xl font-bold text-slate-100 mb-2">عدم دسترسی</h2>
        <p className="text-slate-400 mb-6">شما اجازه دسترسی به این صفحه را ندارید</p>
        <a href="/" className="text-sky-400 hover:text-sky-300">بازگشت به داشبورد</a>
      </div>
    </div>
  );
}

// صفحه خطای 404
function NotFoundPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4" dir="rtl">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-slate-700 mb-4">404</h1>
        <h2 className="text-2xl font-bold text-slate-100 mb-2">صفحه یافت نشد</h2>
        <p className="text-slate-400 mb-6">صفحه مورد نظر وجود ندارد</p>
        <a href="/" className="text-sky-400 hover:text-sky-300">بازگشت به داشبورد</a>
      </div>
    </div>
  );
}

// روتینگ اصلی
function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Routes>
      {/* صفحات احراز هویت */}
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : (
            <Suspense fallback={<LoadingSpinner />}>
              <LoginPage />
            </Suspense>
          )
        }
      />
      <Route
        path="/register"
        element={
          isAuthenticated ? <Navigate to="/" replace /> : (
            <Suspense fallback={<LoadingSpinner />}>
              <RegisterPage />
            </Suspense>
          )
        }
      />

      {/* صفحات اصلی */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <DashboardPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/trades"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <TradesPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/signals"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <SignalsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/decisions"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <DecisionsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ReportsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/analysis"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <AnalysisPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/accounts"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <TradingAccountsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <SettingsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/settings/telegram"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <TelegramSettingsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/settings/risk"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <RiskSettingsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      {/* صفحات ادمین */}
      <Route
        path="/admin/users"
        element={
          <ProtectedRoute requiredRoles={['admin', 'super_admin']}>
            <DashboardLayout>
              <UserManagementPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin/licenses"
        element={
          <ProtectedRoute requiredRoles={['admin', 'super_admin']}>
            <DashboardLayout>
              <LicenseManagementPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin/audit-logs"
        element={
          <ProtectedRoute requiredRoles={['admin', 'super_admin']}>
            <DashboardLayout>
              <AuditLogsPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/system/health"
        element={
          <ProtectedRoute requiredRoles={['admin', 'super_admin']}>
            <DashboardLayout>
              <SystemHealthPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />

      {/* صفحات خطا */}
      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

// اپلیکیشن اصلی
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
