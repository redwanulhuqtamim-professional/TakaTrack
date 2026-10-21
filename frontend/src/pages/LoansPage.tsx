import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export const LoansPage: React.FC = () => {
  const [loans, setLoans] = useState<any[]>([]);
  const [lendings, setLendings] = useState<any[]>([]);
  const [personName, setPersonName] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [purpose, setPurpose] = useState('');
  const [tab, setTab] = useState<'loans' | 'lendings'>('loans');

  const fetchData = async () => {
    const [lRes, ldRes] = await Promise.all([api.get('/loans'), api.get('/lendings')]);
    setLoans(lRes.data);
    setLendings(ldRes.data);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const endpoint = tab === 'loans' ? '/loans' : '/lendings';
    await api.post(endpoint, {
      person_name: personName,
      principal_amount: amount,
      [tab === 'loans' ? 'borrowing_date' : 'lending_date']: date,
      purpose,
    });
    setPersonName('');
    setAmount('');
    setPurpose('');
    fetchData();
  };

  const handleRepay = async (id: number) => {
    const repayAmt = prompt('Enter repayment amount in BDT:');
    if (!repayAmt) return;
    const endpoint = tab === 'loans' ? `/loans/${id}/repayments` : `/lendings/${id}/repayments`;
    try {
      await api.post(endpoint, {
        amount: repayAmt,
        repayment_date: new Date().toISOString().split('T')[0],
      });
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record repayment.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Loans & Lending Management</h2>
          <p className="text-sm text-slate-500">Borrowing increases cash & liability; lending decreases cash & creates a receivable.</p>
        </div>
        <div className="flex bg-slate-100 p-1 rounded-xl">
          <button
            onClick={() => setTab('loans')}
            className={`px-4 py-2 rounded-lg text-xs font-bold ${tab === 'loans' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'}`}
          >
            Loans (Borrowed)
          </button>
          <button
            onClick={() => setTab('lendings')}
            className={`px-4 py-2 rounded-lg text-xs font-bold ${tab === 'lendings' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'}`}
          >
            Lending (Receivables)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900">{tab === 'loans' ? 'Record Borrowed Loan' : 'Record Money Lent'}</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <input
              type="text"
              required
              value={personName}
              onChange={(e) => setPersonName(e.target.value)}
              placeholder="Person's Name (e.g. Rahim)"
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
            />
            <input
              type="number"
              step="0.01"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Amount in BDT (e.g. 5000)"
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
            />
            <input
              type="date"
              required
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
            />
            <input
              type="text"
              value={purpose}
              onChange={(e) => setPurpose(e.target.value)}
              placeholder="Purpose / Notes"
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
            />
            <button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-sm"
            >
              Save Record
            </button>
          </form>
        </div>

        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-4">{tab === 'loans' ? 'Borrowed Money Records' : 'Lent Money Records'}</h3>
          {(tab === 'loans' ? loans : lendings).length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-8">No records yet.</p>
          ) : (
            <div className="space-y-3">
              {(tab === 'loans' ? loans : lendings).map((item) => (
                <div key={item.id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <h4 className="font-bold text-slate-900">{item.person_name}</h4>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${item.status === 'ACTIVE' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>
                        {item.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{item.purpose || 'No notes'}</p>
                    <p className="text-sm font-semibold text-slate-700 mt-2">
                      Principal: ৳{Number(item.principal_amount).toLocaleString('en-BD')} • Outstanding: <strong className="text-rose-600">৳{Number(item.outstanding_amount).toLocaleString('en-BD')}</strong>
                    </p>
                  </div>
                  {item.status === 'ACTIVE' && (
                    <button
                      onClick={() => handleRepay(item.id)}
                      className="bg-slate-900 hover:bg-slate-800 text-white font-semibold px-4 py-2 rounded-xl text-xs"
                    >
                      Record Repayment
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
