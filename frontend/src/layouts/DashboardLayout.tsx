/**
 * لی‌اوت داشبورد
 *
 * نویسنده: MT5 Trading Team
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Bell,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  Activity,
  Users,
  Key,
  FileCheck,
  CreditCard,
  MessageCircle,
  Brain,
  Heart,
  Shield,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface SidebarItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  badge?: number;
}

function SidebarItem({ to, icon, label, active, badge }: SidebarItemProps) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
        active
          ? 'bg-sky-500/20 text-sky-400'
          : 'text-slate-400 hover:bg-slate-800 hover:text-slate-300'
      }`}
    >
      {icon}
      <span className="font-medium flex-1">{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="px-2 py-0.5 text-xs bg-rose-500/20 text-rose-400 rounded-full">
          {badge}
        </span>
      )}
    </Link>
  );
}

interface SidebarGroupProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

function SidebarGroup({ title, children, defaultOpen = true }: SidebarGroupProps) {
  const [isOpen, setIsOpen] = React.useState(defaultOpen);

  return (
    <div className="mb-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-4 py-2 text-slate-500 text-sm hover:text-slate-400 transition-colors"
      >
        <span>{title}</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-0' : '-rotate-90'}`} />
      </button>
      {isOpen && (
        <nav className="space-y-1 mt-1">
          {children}
        </nav>
      )}
    </div>
  );
}

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, logout, isAdmin, hasRole } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  const navItems = [
    { to: '/', icon: <LayoutDashboard className="w-5 h-5" />, label: 'داشبورد' },
    { to: '/analysis', icon: <Activity className="w-5 h-5" />, label: 'تحلیل' },
    { to: '/signals', icon: <Bell className="w-5 h-5" />, label: 'سیگنال‌ها' },
    { to: '/decisions', icon: <Brain className="w-5 h-5" />, label: 'تصمیم‌ها' },
    { to: '/trades', icon: <TrendingUp className="w-5 h-5" />, label: 'معاملات' },
    { to: '/reports', icon: <FileText className="w-5 h-5" />, label: 'گزارش‌ها' },
  ];

  const accountItems = [
    { to: '/accounts', icon: <CreditCard className="w-5 h-5" />, label: 'حساب‌های معاملاتی' },
  ];

  const settingsItems = [
    { to: '/settings', icon: <Settings className="w-5 h-5" />, label: 'تنظیمات عمومی' },
    { to: '/settings/telegram', icon: <MessageCircle className="w-5 h-5" />, label: 'تلگرام' },
    { to: '/settings/risk', icon: <Shield className="w-5 h-5" />, label: 'مدیریت ریسک' },
  ];

  const adminItems = isAdmin() ? [
    { to: '/admin/users', icon: <Users className="w-5 h-5" />, label: 'مدیریت کاربران' },
    { to: '/admin/licenses', icon: <Key className="w-5 h-5" />, label: 'مدیریت لایسنس' },
    { to: '/admin/audit-logs', icon: <FileCheck className="w-5 h-5" />, label: 'لاگ‌های ممیزی' },
    { to: '/system/health', icon: <Heart className="w-5 h-5" />, label: 'سلامت سیستم' },
  ] : [];

  return (
    <div className="min-h-screen bg-slate-900 flex" dir="rtl">
      {/* Sidebar - Desktop */}
      <aside className="hidden lg:flex w-64 flex-col bg-slate-800/50 border-l border-slate-700/50">
        {/* Logo */}
        <div className="p-6 border-b border-slate-700/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-sky-500 to-blue-600 flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-slate-100">MT5 Trading</h1>
              <p className="text-xs text-slate-500">Enterprise Edition</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 overflow-y-auto">
          {/* منوی اصلی */}
          <div className="space-y-1">
            {navItems.map((item) => (
              <SidebarItem
                key={item.to}
                {...item}
                active={location.pathname === item.to}
              />
            ))}
          </div>

          {/* حساب‌ها */}
          <SidebarGroup title="حساب‌ها">
            {accountItems.map((item) => (
              <SidebarItem
                key={item.to}
                {...item}
                active={location.pathname === item.to}
              />
            ))}
          </SidebarGroup>

          {/* تنظیمات */}
          <SidebarGroup title="تنظیمات" defaultOpen={location.pathname.startsWith('/settings')}>
            {settingsItems.map((item) => (
              <SidebarItem
                key={item.to}
                {...item}
                active={location.pathname === item.to}
              />
            ))}
          </SidebarGroup>

          {/* ادمین */}
          {isAdmin() && (
            <SidebarGroup title="مدیریت" defaultOpen={location.pathname.startsWith('/admin') || location.pathname.startsWith('/system')}>
              {adminItems.map((item) => (
                <SidebarItem
                  key={item.to}
                  {...item}
                  active={location.pathname === item.to}
                />
              ))}
            </SidebarGroup>
          )}
        </nav>

        {/* User */}
        <div className="p-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
              <span className="text-slate-300 font-medium">
                {user?.first_name?.[0] || user?.email?.[0] || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-slate-200 font-medium truncate">
                {user?.first_name || 'کاربر'}
              </p>
              <p className="text-slate-500 text-sm truncate">
                {user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-3 py-2 text-slate-400 hover:text-rose-400 hover:bg-slate-700/50 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">خروج</span>
          </button>
        </div>
      </aside>

      {/* Mobile Sidebar */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setSidebarOpen(false)}>
          <aside
            className="w-64 h-full bg-slate-800 border-l border-slate-700"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 flex justify-between items-center border-b border-slate-700">
              <h2 className="font-bold text-slate-100">منو</h2>
              <button onClick={() => setSidebarOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <nav className="p-4 space-y-1 overflow-y-auto max-h-[calc(100vh-120px)]">
              {navItems.map((item) => (
                <SidebarItem
                  key={item.to}
                  {...item}
                  active={location.pathname === item.to}
                />
              ))}

              <div className="border-t border-slate-700 my-2 pt-2">
                {accountItems.map((item) => (
                  <SidebarItem
                    key={item.to}
                    {...item}
                    active={location.pathname === item.to}
                  />
                ))}
              </div>

              <div className="border-t border-slate-700 my-2 pt-2">
                {settingsItems.map((item) => (
                  <SidebarItem
                    key={item.to}
                    {...item}
                    active={location.pathname === item.to}
                  />
                ))}
              </div>

              {isAdmin() && (
                <div className="border-t border-slate-700 my-2 pt-2">
                  {adminItems.map((item) => (
                    <SidebarItem
                      key={item.to}
                      {...item}
                      active={location.pathname === item.to}
                    />
                  ))}
                </div>
              )}
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="bg-slate-800/50 border-b border-slate-700/50 px-4 py-3 lg:px-6">
          <div className="flex items-center justify-between">
            {/* Mobile Menu */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-slate-400 hover:text-slate-200"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Right side */}
            <div className="flex items-center gap-4">
              {/* Kill Zone indicator */}
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-slate-700/50 rounded-lg">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                <span className="text-sm text-slate-300">Kill Zone: لندن</span>
              </div>

              {/* Role badge */}
              {user && (
                <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-sky-500/10 rounded-lg">
                  <span className="text-sky-400 text-sm">
                    {user.role === 'super_admin' ? 'مدیر ارشد' :
                     user.role === 'admin' ? 'مدیر' :
                     user.role === 'trader' ? 'تریدر' : 'کاربر'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>

        {/* Footer */}
        <footer className="bg-slate-800/30 border-t border-slate-700/50 px-4 py-3 text-center">
          <p className="text-slate-600 text-sm">
            MT5 Trading System v1.0.0 • Enterprise Edition
          </p>
        </footer>
      </div>
    </div>
  );
}
