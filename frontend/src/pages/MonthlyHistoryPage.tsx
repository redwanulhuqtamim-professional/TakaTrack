import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Archive, Trash2, Calendar } from 'lucide-react';

export const MonthlyHistoryPage: React.FC = () => {
  const [months, setMonths] = useState<any[]>([]);
  const [yearFilter, setYearFilter] = useState<string>('');
  const [compareA, setCompareA] = useState<string>('');
  const [compareB, setCompareB] = useState<string>('');

  const fetchMonths = async () => {
    const q = yearFilter ? `?year=${yearFilter}&include_archived=true` : '?include_archived=true';
    const res = await api.get(`/months${q}`);
    setMonths(res.data);
  };

  useEffect(() => {
    fetchMonths();
  }, [yearFilter]);

  const handleArchiveToggle = async (m: any) => {
    await api.patch(`/months/${m.id}`, { is_archived: !m.is_archived });
    fetchMonths();
  };

  const handleDelete = async (m: any) => {
    if (!confirm(`Permanently delete ${m.month_name} ${m.year} and all its records?`)) return;
    await api.delete(`/months/${m.id}?confirm=true`);
    fetchMonths();
  };

  const monthA = months.find((m) => String(m.id) === compareA);
  const monthB = months.find((m) => String(m.id) === compareB);

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Monthly History & Comparison</h2>
          <p className="text-sm text-slate-500">Review all historical Gregorian months, compare periods, or archive old budgets.</p>
        </div>
        <input
          type="number"
          placeholder="Filter by Year (e.g. 2026)"
          value={yearFilter}
          onChange={(e) => setYearFilter(e.target.value)}
          className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm text-slate-800 w-52"
        />
      </div>

      {months.length >= 2 && (
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900">Compare Two Months</h3>
          <div className="flex flex-wrap gap-4">
            <select
              value={compareA}
              onChange={(e) => setCompareA(e.target.value)}
              className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-700"
            >
              <option value="">Select First Month</option>
              {months.map((m) => (
                <option key={m.id} value={m.id}>{m.month_name} {m.year}</option>
              ))}
            </select>
            <select
              value={compareB}
              onChange={(e) => setCompareB(e.target.value)}
              className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-700"
            >
              <option value="">Select Second Month</option>
              {months.map((m) => (
                <option key={m.id} value={m.id}>{m.month_name} {m.year}</option>
              ))}
            </select>
          </div>
          {monthA && monthB && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <p className="text-xs text-slate-400 uppercase font-bold">Budget Comparison</p>
                <p className="text-sm font-semibold text-slate-800 mt-1">
                  {monthA.month_name}: ৳{Number(monthA.budget_amount).toLocaleString('en-BD')} vs {monthB.month_name}: ৳{Number(monthB.budget_amount).toLocaleString('en-BD')}
                </p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <p className="text-xs text-slate-400 uppercase font-bold">Total Expenses</p>
                <p className="text-sm font-semibold text-rose-600 mt-1">
                  {monthA.month_name}: ৳{Number(monthA.total_ordinary_expenses).toLocaleString('en-BD')} vs {monthB.month_name}: ৳{Number(monthB.total_ordinary_expenses).toLocaleString('en-BD')}
                </p>
              </div>
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                <p className="text-xs text-slate-400 uppercase font-bold">Closing Available Cash</p>
                <p className="text-sm font-semibold text-blue-600 mt-1">
                  {monthA.month_name}: ৳{Number(monthA.available_cash).toLocaleString('en-BD')} vs {monthB.month_name}: ৳{Number(monthB.available_cash).toLocaleString('en-BD')}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {months.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-3">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900">No historical months found</h3>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {months.map((m) => (
            <div key={m.id} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold text-slate-900">{m.month_name} {m.year}</h3>
                  <p className="text-xs text-slate-400">{m.days_in_month} days in month {m.is_archived ? '• ARCHIVED' : ''}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleArchiveToggle(m)}
                    className="p-2 text-slate-500 hover:bg-slate-100 rounded-xl"
                    title="Archive / Unarchive"
                  >
                    <Archive className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(m)}
                    className="p-2 text-slate-400 hover:text-rose-600 rounded-xl"
                    title="Delete Month"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-xs text-slate-400 block">Monthly Budget</span>
                  <strong className="text-slate-900">৳{Number(m.budget_amount).toLocaleString('en-BD')}</strong>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-xs text-slate-400 block">Total Expenses</span>
                  <strong className="text-rose-600">৳{Number(m.total_ordinary_expenses).toLocaleString('en-BD')}</strong>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-xs text-slate-400 block">Remaining Budget</span>
                  <strong className="text-emerald-600">৳{Number(m.remaining_budget).toLocaleString('en-BD')}</strong>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl">
                  <span className="text-xs text-slate-400 block">Closing Cash</span>
                  <strong className="text-blue-600">৳{Number(m.available_cash).toLocaleString('en-BD')}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
