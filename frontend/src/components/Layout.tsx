import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Calendar,
  Receipt,
  DollarSign,
  History,
  PieChart,
  User,
  Settings,
  LogOut,
  Wallet,
} from 'lucide-react';

export const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Monthly Budget', path: '/budget', icon: Calendar },
    { label: 'Daily Expenses', path: '/expenses', icon: Receipt },
    { label: 'Loans & Lending', path: '/loans', icon: DollarSign },
    { label: 'Monthly History', path: '/history', icon: History },
    { label: 'Reports', path: '/reports', icon: PieChart },
    { label: 'Profile', path: '/profile', icon: User },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="w-64 bg-slate-900 text-slate-300 hidden md:flex flex-col justify-between border-r border-slate-800">
        <div>
          <div className="p-6 flex items-center space-x-3 border-b border-slate-800">
            <div className="bg-emerald-600 p-2 rounded-xl text-white">
              <Wallet className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-wide">TakaTrack</h1>
              <p className="text-xs text-emerald-400 font-medium">Bangladesh Finance Manager</p>
            </div>
          </div>
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-3 px-4 py-2.5 rounded-xl font-medium transition-colors text-sm ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/20'
                      : 'hover:bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="px-4 py-3 mb-3 bg-slate-800/50 rounded-xl">
            <p className="text-xs text-slate-400">Signed in as</p>
            <p className="text-sm font-semibold text-white truncate">{user?.full_name}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-4 py-2.5 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors font-medium text-sm"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-slate-200 h-16 px-6 flex items-center justify-between md:justify-end">
          <div className="flex items-center space-x-3 md:hidden">
            <div className="bg-emerald-600 p-2 rounded-xl text-white">
              <Wallet className="w-5 h-5" />
            </div>
            <span className="font-bold text-slate-900 text-lg">TakaTrack</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-slate-600 hidden sm:inline">
              Welcome, <strong className="text-slate-900">{user?.full_name}</strong>
            </span>
          </div>
        </header>

        <main className="flex-1 p-6 overflow-y-auto max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
