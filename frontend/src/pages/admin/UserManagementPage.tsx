/**
 * صفحه مدیریت کاربران (ادمین)
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { Users, Search, ListFilter as Filter, MoveVertical as MoreVertical, UserCheck, UserX, Shield, Mail, Calendar, ChevronRight, ChevronLeft } from 'lucide-react';
import { userService } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { formatDate, getDirectionText } from '@/utils/helpers';
import type { User, UserRole, UserStatus } from '@/types';

const ROLE_LABELS: Record<UserRole, string> = {
  user: 'کاربر',
  trader: 'تریدر',
  admin: 'مدیر',
  super_admin: 'مدیر ارشد'
};

const STATUS_LABELS: Record<UserStatus, string> = {
  active: 'فعال',
  inactive: 'غیرفعال',
  suspended: 'معلق'
};

export function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<UserRole | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<UserStatus | 'all'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);

  const itemsPerPage = 10;

  useEffect(() => {
    loadUsers();
  }, [currentPage, roleFilter, statusFilter]);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);

    try {
      const { data, count } = await userService.getAllUsers(currentPage, itemsPerPage);
      setUsers(data || []);
      setTotalCount(count || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در دریافت کاربران');
    } finally {
      setLoading(false);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user.first_name?.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (user.last_name?.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  const handleStatusChange = async (userId: string, newStatus: UserStatus) => {
    setSaving(true);
    try {
      await userService.updateUserStatus(userId, newStatus);
      await loadUsers();
      setShowModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در به‌روزرسانی وضعیت');
    } finally {
      setSaving(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    setSaving(true);
    try {
      await userService.updateUserRole(userId, newRole);
      await loadUsers();
      setShowModal(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در به‌روزرسانی نقش');
    } finally {
      setSaving(false);
    }
  };

  const openUserModal = (user: User) => {
    setSelectedUser(user);
    setShowModal(true);
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
          <h1 className="text-2xl font-bold text-slate-100">مدیریت کاربران</h1>
          <p className="text-slate-500 mt-1">مشاهده و مدیریت کاربران سیستم</p>
        </div>
        <div className="flex items-center gap-2 text-slate-500">
          <Users className="w-5 h-5" />
          <span>{totalCount} کاربر</span>
        </div>
      </div>

      {/* خطا */}
      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 text-rose-400">
          {error}
        </div>
      )}

      {/* فیلترها */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* جستجو */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="جستجوی کاربر..."
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg pr-10 pl-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
              />
            </div>
          </div>

          {/* فیلتر نقش */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as UserRole | 'all')}
              className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            >
              <option value="all">همه نقش‌ها</option>
              <option value="user">کاربر</option>
              <option value="trader">تریدر</option>
              <option value="admin">مدیر</option>
              <option value="super_admin">مدیر ارشد</option>
            </select>
          </div>

          {/* فیلتر وضعیت */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as UserStatus | 'all')}
            className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
          >
            <option value="all">همه وضعیت‌ها</option>
            <option value="active">فعال</option>
            <option value="inactive">غیرفعال</option>
            <option value="suspended">معلق</option>
          </select>
        </div>
      </div>

      {/* جدول کاربران */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-700/30 border-b border-slate-700/50">
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">کاربر</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">ایمیل</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">نقش</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">وضعیت</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">تاریخ عضویت</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-slate-500">
                    کاربری یافت نشد
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr
                    key={user.id}
                    className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                  >
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
                          <span className="text-slate-300 font-medium">
                            {user.first_name?.[0] || user.email[0].toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="text-slate-200 font-medium">
                            {user.first_name} {user.last_name}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2 text-slate-300">
                        <Mail className="w-4 h-4 text-slate-500" />
                        {user.email}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                        user.role === 'super_admin' ? 'bg-violet-500/20 text-violet-400' :
                        user.role === 'admin' ? 'bg-amber-500/20 text-amber-400' :
                        user.role === 'trader' ? 'bg-sky-500/20 text-sky-400' :
                        'bg-slate-500/20 text-slate-400'
                      }`}>
                        <Shield className="w-3 h-3" />
                        {ROLE_LABELS[user.role]}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${
                        user.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                        user.status === 'suspended' ? 'bg-rose-500/20 text-rose-400' :
                        'bg-slate-500/20 text-slate-400'
                      }`}>
                        {user.status === 'active' ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                        {STATUS_LABELS[user.status]}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2 text-slate-400 text-sm">
                        <Calendar className="w-4 h-4" />
                        {formatDate(user.created_at)}
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <button
                        onClick={() => openUserModal(user)}
                        className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* صفحهبندی */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700/50">
            <p className="text-slate-500 text-sm">
              نمایش {(currentPage - 1) * itemsPerPage + 1} تا {Math.min(currentPage * itemsPerPage, totalCount)} از {totalCount}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <span className="text-slate-400">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* مودال */}
      {showModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md" dir="rtl">
            <div className="p-6 border-b border-slate-700">
              <h3 className="text-lg font-semibold text-slate-100">ویرایش کاربر</h3>
            </div>

            <div className="p-6 space-y-4">
              {/* اطلاعات کاربر */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-slate-700 flex items-center justify-center">
                  <span className="text-slate-300 text-xl font-medium">
                    {selectedUser.first_name?.[0] || selectedUser.email[0].toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-slate-200 font-medium">
                    {selectedUser.first_name} {selectedUser.last_name}
                  </p>
                  <p className="text-slate-500 text-sm">{selectedUser.email}</p>
                </div>
              </div>

              {/* تغییر نقش */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">نقش</label>
                <select
                  value={selectedUser.role}
                  onChange={(e) => handleRoleChange(selectedUser.id, e.target.value as UserRole)}
                  disabled={saving}
                  className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg px-4 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50 disabled:opacity-50"
                >
                  <option value="user">کاربر</option>
                  <option value="trader">تریدر</option>
                  <option value="admin">مدیر</option>
                  {currentUser?.role === 'super_admin' && (
                    <option value="super_admin">مدیر ارشد</option>
                  )}
                </select>
              </div>

              {/* تغییر وضعیت */}
              <div>
                <label className="block text-slate-400 text-sm mb-2">وضعیت</label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleStatusChange(selectedUser.id, 'active')}
                    disabled={saving || selectedUser.status === 'active'}
                    className={`py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedUser.status === 'active'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    فعال
                  </button>
                  <button
                    onClick={() => handleStatusChange(selectedUser.id, 'inactive')}
                    disabled={saving || selectedUser.status === 'inactive'}
                    className={`py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedUser.status === 'inactive'
                        ? 'bg-slate-500/20 text-slate-400'
                        : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    غیرفعال
                  </button>
                  <button
                    onClick={() => handleStatusChange(selectedUser.id, 'suspended')}
                    disabled={saving || selectedUser.status === 'suspended'}
                    className={`py-2 rounded-lg text-sm font-medium transition-colors ${
                      selectedUser.status === 'suspended'
                        ? 'bg-rose-500/20 text-rose-400'
                        : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    تعلیق
                  </button>
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-slate-700">
              <button
                onClick={() => setShowModal(false)}
                className="w-full bg-slate-700/50 text-slate-300 py-2 rounded-lg hover:bg-slate-700 transition-colors"
              >
                بستن
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
