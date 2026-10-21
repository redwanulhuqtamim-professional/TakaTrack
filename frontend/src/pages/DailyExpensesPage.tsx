import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Trash2, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

export const DailyExpensesPage: React.FC = () => {
  const [dateStr, setDateStr] = useState(new Date().toISOString().split('T')[0]);
  const [summary, setSummary] = useState<any>(null);
  const [categories, setCategories] = useState<any[]>([]);
  const [amount, setAmount] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(true);

  const shiftDate = (days: number) => {
    const [y, m, d] = dateStr.split('-').map(Number);
    const dt = new Date(Date.UTC(y, m - 1, d + days));
    setDateStr(dt.toISOString().split('T')[0]);
  };

  const fetchData = async () => {
    try {
      const [sumRes, catRes] = await Promise.all([
        api.get(`/expenses/daily/${dateStr}`),
        api.get('/categories'),
      ]);
      setSummary(sumRes.data);
      setCategories(catRes.data);
      if (catRes.data.length > 0 && !categoryId) {
        setCategoryId(String(catRes.data[0].id));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateStr]);

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/expenses', {
        amount,
        category_id: Number(categoryId),
        description,
        expense_date: dateStr,
      });
      setAmount('');
      setDescription('');
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add expense.');
    }
  };

  const handleDeleteExpense = async (id: number) => {
    if (!confirm('Delete this expense?')) return;
    await api.delete(`/expenses/${id}`);
    fetchData();
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading daily expenses...</div>;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Daily Expense Tracker</h2>
          <p className="text-sm text-slate-500">{summary?.day_of_week}, {dateStr}</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => shiftDate(-1)}
            className="p-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-slate-700"
            title="Previous Day"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <input
            type="date"
            value={dateStr}
            onChange={(e) => setDateStr(e.target.value)}
            className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-700"
          />
          <button
            onClick={() => shiftDate(1)}
            className="p-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-slate-700"
            title="Next Day"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          <button
            onClick={() => setDateStr(new Date().toISOString().split('T')[0])}
            className="px-3 py-2 bg-emerald-50 text-emerald-700 font-semibold rounded-xl text-xs"
          >
            Today
          </button>
        </div>
      </div>

      {!summary?.month_exists ? (
        <div className="bg-white p-12 rounded-2xl border border-slate-200 text-center space-y-4">
          <Calendar className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="text-lg font-bold text-slate-900">Month not created for {dateStr.slice(0, 7)}</h3>
          <p className="text-sm text-slate-500">Go to the Overview page and set up this month first before recording daily expenses.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Add Expense</h3>
            <form onSubmit={handleAddExpense} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Amount (BDT)</label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="250"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 font-semibold"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Category</label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900"
                >
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Description</label>
                <input
                  type="text"
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Rickshaw fare / groceries"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl shadow-md text-sm"
              >
                Add Expense
              </button>
            </form>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-slate-200">
                <p className="text-xs font-semibold uppercase text-slate-400">Day's Spending</p>
                <p className="text-2xl font-bold text-rose-600 mt-1">৳{Number(summary.daily_total).toLocaleString('en-BD')}</p>
              </div>
              <div className="bg-white p-5 rounded-2xl border border-slate-200">
                <p className="text-xs font-semibold uppercase text-slate-400">Remaining Budget (As of Date)</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">৳{Number(summary.remaining_monthly_budget_as_of_date).toLocaleString('en-BD')}</p>
              </div>
              <div className="bg-white p-5 rounded-2xl border border-slate-200">
                <p className="text-xs font-semibold uppercase text-slate-400">Transactions</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{summary.transaction_count}</p>
              </div>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-4">Transactions on {dateStr}</h3>
              {summary.expenses.length === 0 ? (
                <p className="text-sm text-slate-500 text-center py-8">No expenses recorded for this date.</p>
              ) : (
                <div className="space-y-3">
                  {summary.expenses.map((exp: any) => (
                    <div key={exp.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <div>
                        <span className="text-xs font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-md">
                          {exp.category_name}
                        </span>
                        <h4 className="font-semibold text-slate-900 mt-1">{exp.description}</h4>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="font-bold text-rose-600">৳{Number(exp.amount).toLocaleString('en-BD')}</span>
                        <button
                          onClick={() => handleDeleteExpense(exp.id)}
                          className="text-slate-400 hover:text-rose-600 p-1"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
