/**
 * تست‌های احراز هویت
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';

// Wrapper for components that need router and auth context
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
);

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('فرم ورود را نمایش می‌دهد', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    expect(screen.getByText('ورود به حساب کاربری')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('email@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/حداقل ۶ کاراکتر/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'ورود' })).toBeInTheDocument();
  });

  it('دکمه ورود با فرم خالی غیرفعال است', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: 'ورود' });
    expect(submitButton).toBeDisabled();
  });

  it('خطای فرمت ایمیل نامعتبر را نمایش می‌دهد', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const emailInput = screen.getByPlaceholderText('email@example.com');
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    expect(screen.getByText('فرمت ایمیل نامعتبر است')).toBeInTheDocument();
  });

  it('خطای رمز عبور کوتاه را نمایش می‌دهد', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    const passwordInput = screen.getByPlaceholderText(/حداقل ۶ کاراکتر/);
    fireEvent.change(passwordInput, { target: { value: '123' } });

    expect(screen.getByText('رمز عبور باید حداقل ۶ کاراکتر باشد')).toBeInTheDocument();
  });

  it('لینک به صفحه ثبت‌نام وجود دارد', () => {
    render(
      <TestWrapper>
        <LoginPage />
      </TestWrapper>
    );

    expect(screen.getByText('ثبت‌نام کنید')).toBeInTheDocument();
  });
});

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('فرم ثبت‌نام را نمایش می‌دهد', () => {
    render(
      <TestWrapper>
        <RegisterPage />
      </TestWrapper>
    );

    expect(screen.getByText('ایجاد حساب کاربری جدید')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('نام')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('نام خانوادگی')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('email@example.com')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'ثبت‌نام' })).toBeInTheDocument();
  });

  it('الزامات رمز عبور را نمایش می‌دهد', () => {
    render(
      <TestWrapper>
        <RegisterPage />
      </TestWrapper>
    );

    const passwordInputs = screen.getAllByPlaceholderText(/حداقل ۶ کاراکتر/);
    const passwordInput = passwordInputs[0];

    fireEvent.change(passwordInput, { target: { value: 'test' } });

    expect(screen.getByText('حداقل ۶ کاراکتر')).toBeInTheDocument();
  });

  it('خطای عدم تطابق رمز عبور را نمایش می‌دهد', () => {
    render(
      <TestWrapper>
        <RegisterPage />
      </TestWrapper>
    );

    const passwordInputs = screen.getAllByPlaceholderText(/حداقل ۶ کاراکتر/);
    const passwordInput = passwordInputs[0];
    const confirmPasswordInput = screen.getByPlaceholderText('تکرار رمز عبور');

    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.change(confirmPasswordInput, { target: { value: 'differentPassword' } });

    expect(screen.getByText('رمز عبور مطابقت ندارد')).toBeInTheDocument();
  });

  it('دکمه ثبت‌نام با فرم ناقص غیرفعال است', () => {
    render(
      <TestWrapper>
        <RegisterPage />
      </TestWrapper>
    );

    const submitButton = screen.getByRole('button', { name: 'ثبت‌نام' });
    expect(submitButton).toBeDisabled();
  });

  it('لینک به صفحه ورود وجود دارد', () => {
    render(
      <TestWrapper>
        <RegisterPage />
      </TestWrapper>
    );

    expect(screen.getByText('وارد شوید')).toBeInTheDocument();
  });
});
