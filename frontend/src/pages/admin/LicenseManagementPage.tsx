/**
 * صفحه مدیریت لایسنس (ادمین)
 *
 * نویسنده: MT5 Trading Team
 */

import React, { useState, useEffect } from 'react';
import { Key, Search, ListFilter as Filter, MoveVertical as MoreVertical, CircleCheck as CheckCircle, Circle as XCircle, Clock, Calendar, Monitor, ChevronRight, ChevronLeft, Plus } from 'lucide-react';
import { licenseService } from '@/services/api';
import { formatDate, formatRelativeTime } from '@/utils/helpers';
import type { License, LicensePlan, LicenseDevice } from '@/types';

const STATUS_LABELS = {
  inactive: 'غیرفعال',
  active: 'فعال',
  expired: 'منقضی',
  revoked: 'ابطال شده',
  suspended: 'معلق'
};

const STATUS_COLORS = {
  inactive: 'bg-slate-500/20 text-slate-400',
  active: 'bg-emerald-500/20 text-emerald-400',
  expired: 'bg-amber-500/20 text-amber-400',
  revoked: 'bg-rose-500/20 text-rose-400',
  suspended: 'bg-violet-500/20 text-violet-400'
};

export function LicenseManagementPage() {
  const [licenses, setLicenses] = useState<(License & { user_profiles?: { email: string; first_name: string; last_name: string }; license_plans?: LicensePlan })[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedLicense, setSelectedLicense] = useState<typeof licenses[0] | null>(null);
  const [devices, setDevices] = useState<LicenseDevice[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [showDevicesModal, setShowDevicesModal] = useState(false);

  const itemsPerPage = 10;

  useEffect(() => {
    loadLicenses();
  }, [currentPage, statusFilter]);

  const loadLicenses = async () => {
    setLoading(true);
    setError(null);

    try {
      const { data, count } = await licenseService.getAllLicenses(currentPage, itemsPerPage);
      setLicenses(data || []);
      setTotalCount(count || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در دریافت لایسنس‌ها');
    } finally {
      setLoading(false);
    }
  };

  const filteredLicenses = licenses.filter(license => {
    const user = license.user_profiles;
    const matchesSearch =
      license.license_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (user?.email?.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || license.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalPages = Math.ceil(totalCount / itemsPerPage);

  const viewDevices = async (license: typeof licenses[0]) => {
    setSelectedLicense(license);
    try {
      const devicesData = await licenseService.getLicenseDevices(license.id);
      setDevices(devicesData);
    } catch (err) {
      setDevices([]);
    }
    setShowDevicesModal(true);
  };

  const removeDevice = async (deviceId: string) => {
    try {
      await licenseService.removeDevice(deviceId);
      const devicesData = await licenseService.getLicenseDevices(selectedLicense?.id || '');
      setDevices(devicesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطا در حذف دستگاه');
    }
  };

  const getDaysRemaining = (expiresAt: string): number => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    return Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
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
          <h1 className="text-2xl font-bold text-slate-100">مدیریت لایسنس</h1>
          <p className="text-slate-500 mt-1">مشاهده و مدیریت لایسنس‌های صادر شده</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-slate-500">
            <Key className="w-5 h-5" />
            <span>{totalCount} لایسنس</span>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-sky-500/20 text-sky-400 rounded-lg hover:bg-sky-500/30 transition-colors">
            <Plus className="w-4 h-4" />
            لایسنس جدید
          </button>
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
                placeholder="جستجوی لایسنس..."
                className="w-full bg-slate-700/50 border border-slate-600/50 rounded-lg pr-10 pl-4 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500/50"
              />
            </div>
          </div>

          {/* فیلتر وضعیت */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-700/50 border border-slate-600/50 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-sky-500/50"
            >
              <option value="all">همه وضعیت‌ها</option>
              <option value="active">فعال</option>
              <option value="inactive">غیرفعال</option>
              <option value="expired">منقضی</option>
              <option value="revoked">ابطال شده</option>
              <option value="suspended">معلق</option>
            </select>
          </div>
        </div>
      </div>

      {/* جدول لایسنس‌ها */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-700/30 border-b border-slate-700/50">
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">کلید لایسنس</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">کاربر</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">پلن</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">وضعیت</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">دستگاه‌ها</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">تاریخ انقضا</th>
                <th className="text-right text-slate-400 text-sm font-medium px-4 py-3">عملیات</th>
              </tr>
            </thead>
            <tbody>
              {filteredLicenses.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500">
                    لاینس یافت نشد
                  </td>
                </tr>
              ) : (
                filteredLicenses.map((license) => {
                  const daysRemaining = license.expires_at ? getDaysRemaining(license.expires_at) : null;
                  const user = license.user_profiles;

                  return (
                    <tr
                      key={license.id}
                      className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                    >
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <Key className="w-4 h-4 text-sky-500" />
                          <code className="text-slate-300 font-mono text-sm">
                            {license.license_key.slice(0, 8)}...{license.license_key.slice(-4)}
                          </code>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        {user ? (
                          <div>
                            <p className="text-slate-200">{user.first_name} {user.last_name}</p>
                            <p className="text-slate-500 text-sm">{user.email}</p>
                          </div>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        {license.license_plans ? (
                          <span className="text-slate-300">{license.license_plans.name_fa}</span>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${STATUS_COLORS[license.status]}`}>
                          {license.status === 'active' ? <CheckCircle className="w-3 h-3" /> :
                           license.status === 'expired' ? <Clock className="w-3 h-3" /> :
                           <XCircle className="w-3 h-3" />}
                          {STATUS_LABELS[license.status]}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <button
                          onClick={() => viewDevices(license)}
                          className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
                        >
                          <Monitor className="w-4 h-4" />
                          <span>{license.current_devices}/{license.max_devices}</span>
                        </button>
                      </td>
                      <td className="px-4 py-4">
                        {license.expires_at ? (
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-slate-500" />
                            <div>
                              <p className="text-slate-300 text-sm">
                                {formatDate(license.expires_at)}
                              </p>
                              {daysRemaining !== null && (
                                <p className={`text-xs ${
                                  daysRemaining > 7 ? 'text-emerald-400' :
                                  daysRemaining > 0 ? 'text-amber-400' : 'text-rose-400'
                                }`}>
                                  {daysRemaining > 0 ? `${daysRemaining} روز باقی‌مانده` : 'منقضی شده'}
                                </p>
                              )}
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-500">نامحدود</span>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <button
                          onClick={() => {
                            setSelectedLicense(license);
                            setShowModal(true);
                          }}
                          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-700 rounded-lg transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
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

      {/* مودال دستگاه‌ها */}
      {showDevicesModal && selectedLicense && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md" dir="rtl">
            <div className="p-6 border-b border-slate-700">
              <h3 className="text-lg font-semibold text-slate-100">دستگاه‌های ثبت شده</h3>
              <p className="text-slate-500 text-sm mt-1">
                {selectedLicense.current_devices} از {selectedLicense.max_devices} دستگاه
              </p>
            </div>

            <div className="p-6 max-h-96 overflow-y-auto">
              {devices.length === 0 ? (
                <p className="text-slate-500 text-center py-8">دستگاهی ثبت نشده</p>
              ) : (
                <div className="space-y-3">
                  {devices.map((device) => (
                    <div
                      key={device.id}
                      className="bg-slate-700/30 rounded-lg p-4 flex items-center justify-between"
                    >
                      <div>
                        <p className="text-slate-200 font-medium">{device.device_name}</p>
                        <p className="text-slate-500 text-sm">{device.device_id}</p>
                        <p className="text-slate-600 text-xs mt-1">
                          آخرین بازدید: {formatRelativeTime(device.last_seen)}
                        </p>
                      </div>
                      <button
                        onClick={() => removeDevice(device.id)}
                        className="px-3 py-1 text-rose-400 text-sm hover:bg-rose-500/10 rounded transition-colors"
                      >
                        حذف
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-700">
              <button
                onClick={() => setShowDevicesModal(false)}
                className="w-full bg-slate-700/50 text-slate-300 py-2 rounded-lg hover:bg-slate-700 transition-colors"
              >
                بستن
              </button>
            </div>
          </div>
        </div>
      )}

      {/* مودال لایسنس */}
      {showModal && selectedLicense && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md" dir="rtl">
            <div className="p-6 border-b border-slate-700">
              <h3 className="text-lg font-semibold text-slate-100">جزئیات لایسنس</h3>
            </div>

            <div className="p-6 space-y-4">
              <div className="bg-slate-700/30 rounded-lg p-4">
                <p className="text-slate-500 text-sm mb-1">کلید لایسنس</p>
                <code className="text-slate-200 font-mono break-all">{selectedLicense.license_key}</code>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <p className="text-slate-500 text-sm mb-1">وضعیت</p>
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${STATUS_COLORS[selectedLicense.status]}`}>
                    {STATUS_LABELS[selectedLicense.status]}
                  </span>
                </div>

                <div className="bg-slate-700/30 rounded-lg p-4">
                  <p className="text-slate-500 text-sm mb-1">دستگاه‌ها</p>
                  <p className="text-slate-200">{selectedLicense.current_devices}/{selectedLicense.max_devices}</p>
                </div>
              </div>

              {selectedLicense.started_at && (
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <p className="text-slate-500 text-sm mb-1">تاریخ شروع</p>
                  <p className="text-slate-200">{formatDate(selectedLicense.started_at)}</p>
                </div>
              )}

              {selectedLicense.expires_at && (
                <div className="bg-slate-700/30 rounded-lg p-4">
                  <p className="text-slate-500 text-sm mb-1">تاریخ انقضا</p>
                  <p className="text-slate-200">{formatDate(selectedLicense.expires_at)}</p>
                </div>
              )}
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
