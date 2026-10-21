import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [dailyTarget, setDailyTarget] = useState(String(user?.settings?.daily_spending_target || ''));
  const [categories, setCategories] = useState<any[]>([]);
  const [newCatName, setNewCatName] = useState('');
  const [savedMsg, setSavedMsg] = useState('');

  const fetchCategories = async () => {
    const res = await api.get('/categories');
    setCategories(res.data);
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.patch('/profile', {
      daily_spending_target: dailyTarget ? Number(dailyTarget) : 0,
    });
    await refreshUser();
    setSavedMsg('Settings updated!');
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/categories', { name: newCatName });
      setNewCatName('');
      fetchCategories();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Category already exists.');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900">Application Settings & Custom Categories</h2>
        <p className="text-sm text-slate-500">Configure optional daily spending targets and custom expense categories.</p>
        {savedMsg && <p className="mt-2 text-sm font-semibold text-emerald-600">{savedMsg}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <form onSubmit={handleSaveSettings} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900">Daily Spending Target (Optional)</h3>
          <input
            type="number"
            step="0.01"
            value={dailyTarget}
            onChange={(e) => setDailyTarget(e.target.value)}
            placeholder="e.g. 500 BDT"
            className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900"
          />
          <button type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm">
            Save Target
          </button>
        </form>

        <form onSubmit={handleCreateCategory} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900">Add Custom Expense Category</h3>
          <input
            type="text"
            required
            value={newCatName}
            onChange={(e) => setNewCatName(e.target.value)}
            placeholder="e.g. Books & Stationery"
            className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900"
          />
          <button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white font-semibold px-5 py-2.5 rounded-xl text-sm">
            Create Category
          </button>
        </form>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-3">Available Expense Categories ({categories.length})</h3>
        <div className="flex flex-wrap gap-2">
          {categories.map((c) => (
            <span
              key={c.id}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold ${
                c.is_default ? 'bg-slate-100 text-slate-700' : 'bg-emerald-100 text-emerald-800'
              }`}
            >
              {c.name} {!c.is_default && '(Custom)'}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
