import React, { useState, useEffect, useRef } from 'react';
import { Bell, Clock, AlertTriangle, CheckCircle2, ChevronDown, User } from 'lucide-react';
import { ReminderItem, StudentProfile } from '../../types';
import { api } from '../../services/api';

interface NavbarProps {
  profile: StudentProfile | null;
  onRefresh?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ profile }) => {
  const [reminders, setReminders] = useState<ReminderItem[]>([]);
  const [showBellDropdown, setShowBellDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadReminders();
    const interval = setInterval(loadReminders, 30000); // 30s poll
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowBellDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadReminders = async () => {
    try {
      const res = await api.getReminders();
      setReminders(res.reminders);
    } catch (e) {
      // ignore
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md flex items-center justify-between px-6 z-20">
      <div className="flex items-center space-x-3">
        <h2 className="text-lg font-bold text-slate-100">AI-Powered Study Planner</h2>
        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/50">
          v1.0.0
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {/* Reminders Bell */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowBellDropdown(!showBellDropdown)}
            className="relative p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Notifications & Reminders"
          >
            <Bell className="w-5 h-5" />
            {reminders.length > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-rose-500 rounded-full ring-2 ring-slate-900 animate-pulse" />
            )}
          </button>

          {showBellDropdown && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-slate-900/95 border border-slate-700/80 shadow-2xl backdrop-blur-xl p-4 z-50">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                <span className="font-semibold text-sm text-slate-200 flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-indigo-400" />
                  <span>Active Reminders</span>
                </span>
                <span className="text-xs text-indigo-400 font-medium px-2 py-0.5 bg-indigo-950/70 rounded-full border border-indigo-800/50">
                  {reminders.length} alert{reminders.length !== 1 ? 's' : ''}
                </span>
              </div>

              {reminders.length === 0 ? (
                <div className="py-6 text-center text-slate-400 text-sm flex flex-col items-center">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400/80 mb-2" />
                  <p>All caught up! No active deadline alerts.</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {reminders.map((r) => {
                    const isOverdue = r.type === 'overdue_task';
                    const isUpcoming = r.type === 'upcoming_session';
                    return (
                      <div
                        key={r.id}
                        className={`p-3 rounded-xl border text-xs transition-all ${
                          isOverdue
                            ? 'bg-rose-950/20 border-rose-800/40 text-rose-200'
                            : isUpcoming
                            ? 'bg-indigo-950/20 border-indigo-800/40 text-indigo-200'
                            : 'bg-amber-950/20 border-amber-800/40 text-amber-200'
                        }`}
                      >
                        <div className="flex items-center justify-between font-semibold mb-1">
                          <span className="flex items-center space-x-1.5">
                            {isOverdue ? (
                              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                            ) : (
                              <Clock className="w-3.5 h-3.5 text-indigo-400" />
                            )}
                            <span className="truncate max-w-[200px]">{r.title}</span>
                          </span>
                          <span className={`text-[10px] uppercase font-bold px-1.5 py-0.2 rounded ${
                            r.urgency === 'high' ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-700 text-slate-300'
                          }`}>
                            {r.urgency}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-300/80 leading-relaxed">{r.message}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* User Pill */}
        <div className="flex items-center space-x-2.5 pl-2 border-l border-slate-800">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
            {profile?.display_name ? profile.display_name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-slate-200">{profile?.display_name || 'Student'}</div>
            <div className="text-[10px] text-slate-400">{profile?.timezone || 'UTC'}</div>
          </div>
        </div>
      </div>
    </header>
  );
};
