/**
 * کانتکست احراز هویت - متصل به Supabase
 *
 * نویسنده: MT5 Trading Team
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { authService, userService } from '@/services/api';
import type { User, UserSettings, UserRole } from '@/types';

interface AuthContextType {
  user: User | null;
  settings: UserSettings | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateSettings: (settings: Partial<UserSettings>) => Promise<void>;
  refreshUser: () => Promise<void>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
  isAdmin: () => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // بررسی نشست فعال
  useEffect(() => {
    let mounted = true;

    const initAuth = async () => {
      try {
        const session = await authService.getSession();
        if (session?.user && mounted) {
          await loadUserData(session.user.id);
        }
      } catch (error) {
        console.error('خطا در بررسی نشست:', error);
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();

    // گوش دادن به تغییرات احراز هویت
    const { data: { subscription } } = authService.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          await loadUserData((session as { user: { id: string } }).user.id);
        } else if (event === 'SIGNED_OUT') {
          setUser(null);
          setSettings(null);
        }
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  // بارگذاری داده‌های کاربر
  const loadUserData = async (authUserId: string) => {
    try {
      const profile = await userService.getProfile(authUserId);
      if (profile) {
        setUser(profile);
      } else {
        // ایجاد پروفایل پیش‌فرض
        const authUser = await authService.getCurrentUser();
        const newProfile = await createDefaultProfile(authUserId, authUser.email || '');
        setUser(newProfile);
      }

      const userSettings = await userService.getSettings(authUserId);
      setSettings(userSettings);
    } catch (error) {
      console.error('خطا در بارگذاری داده‌های کاربر:', error);
    }
  };

  // ایجاد پروفایل پیش‌فرض
  const createDefaultProfile = async (userId: string, email: string): Promise<User> => {
    const { data, error } = await supabase
      .from('user_profiles')
      .insert({
        id: userId,
        email: email,
        role: 'user',
        status: 'active'
      })
      .select()
      .single();

    if (error) throw error;
    return data;
  };

  // ورود
  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);

    try {
      const { user: authUser } = await authService.login(email, password);
      if (authUser) {
        await loadUserData(authUser.id);
      }
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ثبت‌نام
  const register = useCallback(async (
    email: string,
    password: string,
    firstName?: string,
    lastName?: string
  ) => {
    setIsLoading(true);

    try {
      const { user: authUser } = await authService.register(email, password, firstName, lastName);
      if (authUser) {
        // ایجاد پروفایل
        await createDefaultProfile(authUser.id, email);
        // ورود خودکار
        await login(email, password);
      }
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  // خروج
  const logout = useCallback(async () => {
    try {
      await authService.logout();
      setUser(null);
      setSettings(null);
    } catch (error) {
      console.error('خطا در خروج:', error);
    }
  }, []);

  // به‌روزرسانی تنظیمات
  const updateSettings = useCallback(async (newSettings: Partial<UserSettings>) => {
    if (!user) return;

    try {
      const updated = await userService.updateSettings(user.id, newSettings);
      setSettings(updated);
    } catch (error) {
      throw error;
    }
  }, [user]);

  // رفرش کاربر
  const refreshUser = useCallback(async () => {
    const currentUser = await authService.getCurrentUser();
    if (currentUser) {
      await loadUserData(currentUser.id);
    }
  }, []);

  // بررسی نقش
  const hasRole = useCallback((roles: UserRole | UserRole[]): boolean => {
    if (!user) return false;
    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(user.role);
  }, [user]);

  // بررسی ادمین بودن
  const isAdmin = useCallback((): boolean => {
    return hasRole(['admin', 'super_admin']);
  }, [hasRole]);

  const value: AuthContextType = {
    user,
    settings,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    updateSettings,
    refreshUser,
    hasRole,
    isAdmin
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth باید داخل AuthProvider استفاده شود');
  }
  return context;
}
