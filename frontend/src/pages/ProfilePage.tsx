import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export const ProfilePage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [msg, setMsg] = useState('');

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.patch('/profile', { full_name: fullName });
    await refreshUser();
    setMsg('Profile name updated successfully.');
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmNewPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      setMsg('Password updated successfully.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Password update failed.');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h2 className="text-2xl font-bold text-slate-900">Your Profile</h2>
        <p className="text-sm text-slate-500">Email: {user?.email} • Currency: BDT (৳) • Timezone: Asia/Dhaka</p>
        {msg && <p className="mt-3 text-sm font-semibold text-emerald-600">{msg}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <form onSubmit={handleUpdateName} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900">Update Personal Info</h3>
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Full Name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900"
            />
          </div>
          <button type="submit" className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-5 py-2.5 rounded-xl text-sm">
            Save Name
          </button>
        </form>

        <form onSubmit={handlePasswordChange} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-lg font-bold text-slate-900">Change Password</h3>
          <input
            type="password"
            required
            placeholder="Current Password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
          />
          <input
            type="password"
            required
            placeholder="New Password (min 8 chars)"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
          />
          <input
            type="password"
            required
            placeholder="Confirm New Password"
            value={confirmNewPassword}
            onChange={(e) => setConfirmNewPassword(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2 text-slate-900 text-sm"
          />
          <button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white font-semibold px-5 py-2.5 rounded-xl text-sm">
            Update Password
          </button>
        </form>
      </div>
    </div>
  );
};
