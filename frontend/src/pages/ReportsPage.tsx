import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Download } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [months, setMonths] = useState<any[]>([]);
  const [selectedMonthId, setSelectedMonthId] = useState<string>('');
  const [reportData, setReportData] = useState<any>(null);

  useEffect(() => {
    api.get('/months').then((res) => {
      setMonths(res.data);
      if (res.data.length > 0) {
        setSelectedMonthId(String(res.data[0].id));
        loadReport(res.data[0].year, res.data[0].month);
      }
    });
  }, []);

  const loadReport = async (year: number, month: number) => {
    const res = await api.get(`/reports/monthly-details/${year}/${month}`);
    setReportData(res.data);
  };

  const handleMonthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedMonthId(id);
    const m = months.find((x) => String(x.id) === id);
    if (m) loadReport(m.year, m.month);
  };

  const handleExportCSV = async () => {
    const m = months.find((x) => String(x.id) === selectedMonthId);
    if (!m) return;
    const res = await api.get(`/reports/export-csv?year=${m.year}&month=${m.month}`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `takatrack_${m.year}_${m.month}.csv`);
    document.body.appendChild(link);
    link.click();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Reports & Analytics</h2>
          <p className="text-sm text-slate-500">Category spending breakdown, ledger history, and CSV export.</p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedMonthId}
            onChange={handleMonthChange}
            className="bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-sm font-semibold text-slate-700"
          >
            {months.map((m) => (
              <option key={m.id} value={m.id}>{m.month_name} {m.year}</option>
            ))}
          </select>
          <button
            onClick={handleExportCSV}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-2 rounded-xl text-sm flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {reportData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Spending by Category</h3>
            {Object.keys(reportData.summary.category_breakdown).length === 0 ? (
              <p className="text-sm text-slate-500 py-8 text-center">No daily expenses recorded for this month.</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(reportData.summary.category_breakdown).map(([cat, amt]: [string, any]) => (
                  <div key={cat} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="font-semibold text-slate-700">{cat}</span>
                    <span className="font-bold text-rose-600">৳{Number(amt).toLocaleString('en-BD')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Recent Ledger Transactions</h3>
            {reportData.recent_transactions.length === 0 ? (
              <p className="text-sm text-slate-500 py-8 text-center">No transactions recorded.</p>
            ) : (
              <div className="space-y-3">
                {reportData.recent_transactions.map((t: any) => (
                  <div key={t.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div>
                      <p className="text-xs text-slate-400">{t.date} • {t.transaction_type}</p>
                      <h4 className="font-semibold text-slate-900">{t.description}</h4>
                    </div>
                    <span className="font-bold text-slate-900">৳{Number(t.amount).toLocaleString('en-BD')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
