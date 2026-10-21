import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CheckCircle, Clock, Trash2 } from 'lucide-react';

export const MonthlyBudgetPage: React.FC = () => {
  const [months, setMonths] = useState<any[]>([]);
  const [currentMonth, setCurrentMonth] = useState<any>(null);
  const [bills, setBills] = useState<any[]>([]);
  const [incomes, setIncomes] = useState<any[]>([]);
  const [newBillName, setNewBillName] = useState('');
  const [newBillAmount, setNewBillAmount] = useState('');
  const [newBillStatus, setNewBillStatus] = useState('UNPAID');
  const [incAmount, setIncAmount] = useState('');
  const [incCategory, setIncCategory] = useState('Salary / Earnings');
  const [incDesc, setIncDesc] = useState('');

  const fetchMonths = async () => {
    const res = await api.get('/months');
    setMonths(res.data);
    if (res.data.length > 0) {
      const active = currentMonth
        ? res.data.find((x: any) => x.id === currentMonth.id) || res.data[0]
        : res.data[0];
      setCurrentMonth(active);
      fetchDetails(active.id);
    }
  };

  const fetchDetails = async (monthId: number) => {
    const [bRes, iRes] = await Promise.all([
      api.get(`/bills?monthly_budget_id=${monthId}`),
      api.get(`/incomes?monthly_budget_id=${monthId}`),
    ]);
    setBills(bRes.data);
    setIncomes(iRes.data);
  };

  useEffect(() => {
    fetchMonths();
  }, []);

  const handleAddBill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentMonth) return;
    await api.post('/bills', {
      monthly_budget_id: currentMonth.id,
      name: newBillName,
      amount: newBillAmount,
      payment_status: newBillStatus,
    });
    setNewBillName('');
    setNewBillAmount('');
    fetchMonths();
  };

  const handleTogglePaid = async (bill: any) => {
    const newStatus = bill.payment_status === 'PAID' ? 'UNPAID' : 'PAID';
    await api.patch(`/bills/${bill.id}`, { payment_status: newStatus });
    fetchMonths();
  };

  const handleDeleteBill = async (id: number) => {
    await api.delete(`/bills/${id}`);
    fetchMonths();
  };

  const handleAddIncome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentMonth) return;
    await api.post('/incomes', {
      monthly_budget_id: currentMonth.id,
      amount: incAmount,
      category: incCategory,
      income_date: `${currentMonth.year}-${String(currentMonth.month).padStart(2, '0')}-01`,
      description: incDesc,
    });
    setIncAmount('');
    setIncDesc('');
    fetchMonths();
  };

  if (!currentMonth) {
    return (
      <div className="p-8 bg-white rounded-2xl border border-slate-200 text-center text-slate-500">
        No monthly budgets found. Set up a month first on the Overview page.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Fixed Bills & Monthly Income</h2>
          <p className="text-sm text-slate-500">
            {currentMonth.month_name} {currentMonth.year} • Paid Bills: ৳{Number(currentMonth.paid_bills_total).toLocaleString('en-BD')} | Unpaid: ৳{Number(currentMonth.unpaid_bills_total).toLocaleString('en-BD')}
          </p>
        </div>
        <select
          value={currentMonth.id}
          onChange={(e) => {
            const m = months.find((x) => x.id === Number(e.target.value));
            setCurrentMonth(m);
            fetchDetails(m.id);
          }}
          className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-700"
        >
          {months.map((m) => (
            <option key={m.id} value={m.id}>{m.month_name} {m.year}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Add Fixed Bill</h3>
            <form onSubmit={handleAddBill} className="space-y-3">
              <input
                type="text"
                required
                value={newBillName}
                onChange={(e) => setNewBillName(e.target.value)}
                placeholder="House Rent / Electricity / Wi-Fi"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
              />
              <input
                type="number"
                step="0.01"
                required
                value={newBillAmount}
                onChange={(e) => setNewBillAmount(e.target.value)}
                placeholder="Amount in BDT (e.g. 5000)"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
              />
              <select
                value={newBillStatus}
                onChange={(e) => setNewBillStatus(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
              >
                <option value="UNPAID">Unpaid</option>
                <option value="PAID">Paid</option>
              </select>
              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm"
              >
                Add Fixed Bill
              </button>
            </form>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Record Monthly Income</h3>
            <form onSubmit={handleAddIncome} className="space-y-3">
              <select
                value={incCategory}
                onChange={(e) => setIncCategory(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
              >
                <option>Salary / Earnings</option>
                <option>Family Allowance</option>
                <option>Scholarship</option>
                <option>Other Income</option>
              </select>
              <input
                type="number"
                step="0.01"
                required
                value={incAmount}
                onChange={(e) => setIncAmount(e.target.value)}
                placeholder="Amount in BDT"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
              />
              <input
                type="text"
                required
                value={incDesc}
                onChange={(e) => setIncDesc(e.target.value)}
                placeholder="Description"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
              />
              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 rounded-xl text-sm"
              >
                Add Income (+ Cash)
              </button>
            </form>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Fixed Bills</h3>
            {bills.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No fixed bills added for this month yet.</p>
            ) : (
              <div className="space-y-3">
                {bills.map((bill) => (
                  <div key={bill.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <div>
                      <h4 className="font-bold text-slate-900">{bill.name}</h4>
                      <p className="text-sm font-semibold text-slate-700">৳{Number(bill.amount).toLocaleString('en-BD')}</p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => handleTogglePaid(bill)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 ${
                          bill.payment_status === 'PAID'
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {bill.payment_status === 'PAID' ? <CheckCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
                        <span>{bill.payment_status === 'PAID' ? 'PAID (Click to Unpay)' : 'UNPAID (Mark Paid)'}</span>
                      </button>
                      <button onClick={() => handleDeleteBill(bill.id)} className="text-slate-400 hover:text-rose-600 p-1.5">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Recorded Incomes</h3>
            {incomes.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">No extra income recorded for this month.</p>
            ) : (
              <div className="space-y-3">
                {incomes.map((inc) => (
                  <div key={inc.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <div>
                      <span className="text-xs font-bold px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md">{inc.category}</span>
                      <h4 className="font-semibold text-slate-900 mt-1">{inc.description}</h4>
                    </div>
                    <span className="font-bold text-emerald-600">+৳{Number(inc.amount).toLocaleString('en-BD')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
