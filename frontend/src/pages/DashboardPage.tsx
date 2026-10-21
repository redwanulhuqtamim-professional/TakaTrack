import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Plus, Calendar } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [selectedMonth, setSelectedMonth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBudget, setNewBudget] = useState('20000');
  const [newOpeningCash, setNewOpeningCash] = useState('0');

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const fetchMonths = async () => {
    try {
      const res = await api.get('/months');
      const current = res.data.find((m: any) => m.year === year && m.month === month) || res.data[0];
      setSelectedMonth(current || null);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonths();
  }, [year, month]);

  const handleCreateMonth = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/months', {
        year,
        month,
        budget_amount: newBudget,
        opening_cash: newOpeningCash,
      });
      setShowAddModal(false);
      fetchMonths();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create month.');
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading financial dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Financial Overview</h2>
          <p className="text-sm text-slate-500">Manage your monthly budget, expenses & available cash in BDT (৳).</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-700"
          >
            {['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'].map((m, idx) => (
              <option key={m} value={idx + 1}>{m}</option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-sm font-semibold text-slate-700"
          />
          {!selectedMonth && (
            <button
              onClick={() => setShowAddModal(true)}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-xl text-sm flex items-center space-x-2"
            >
              <Plus className="w-4 h-4" />
              <span>Set Up Month</span>
            </button>
          )}
        </div>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Set Up Month ({month}/{year})</h3>
            <form onSubmit={handleCreateMonth} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Monthly Budget (BDT)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newBudget}
                  onChange={(e) => setNewBudget(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 font-semibold"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">Opening Cash Balance (BDT)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={newOpeningCash}
                  onChange={(e) => setNewOpeningCash(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-slate-900 font-semibold"
                />
              </div>
              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold py-2.5 rounded-xl text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm"
                >
                  Create Month
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedMonth ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Monthly Budget</p>
            <p className="text-3xl font-bold text-slate-900 mt-2">৳{Number(selectedMonth.budget_amount).toLocaleString('en-BD')}</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Expenses</p>
            <p className="text-3xl font-bold text-rose-600 mt-2">৳{Number(selectedMonth.total_ordinary_expenses).toLocaleString('en-BD')}</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Remaining Budget</p>
            <p className={`text-3xl font-bold mt-2 ${selectedMonth.is_over_budget ? 'text-rose-600' : 'text-emerald-600'}`}>
              ৳{Number(selectedMonth.remaining_budget).toLocaleString('en-BD')}
            </p>
          </div>
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Available Cash</p>
            <p className="text-3xl font-bold text-blue-600 mt-2">৳{Number(selectedMonth.available_cash).toLocaleString('en-BD')}</p>
          </div>
        </div>
      ) : (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-4">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900">No budget created for {month}/{year}</h3>
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-6 py-2.5 rounded-xl text-sm"
          >
            Set Up Month Now
          </button>
        </div>
      )}
    </div>
  );
};