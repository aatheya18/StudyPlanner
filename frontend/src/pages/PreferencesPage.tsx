import React, { useEffect, useState } from 'react';
import { Settings, User, Clock, Calendar, Check, Save } from 'lucide-react';
import { StudentProfile, StudyPreference, AvailabilityWindow } from '../types';
import { api } from '../services/api';

const DAYS_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export const PreferencesPage: React.FC = () => {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [pref, setPref] = useState<StudyPreference | null>(null);
  const [windows, setWindows] = useState<AvailabilityWindow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState<boolean>(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const [pData, prefData, wData] = await Promise.all([
        api.getProfile(),
        api.getPreferences(),
        api.getAvailability()
      ]);
      setProfile(pData);
      setPref(prefData);
      setWindows(wData);
    } catch (err: any) {
      setSaveError(err.message || 'Failed to load preferences');
    } finally {
      setLoading(false);
    }
  };

  const handleWindowChange = (dayIndex: number, field: keyof AvailabilityWindow, val: any) => {
    const updated = [...windows];
    const itemIndex = updated.findIndex((w) => w.day_of_week === dayIndex);
    if (itemIndex >= 0) {
      updated[itemIndex] = { ...updated[itemIndex], [field]: val };
    } else {
      updated.push({
        day_of_week: dayIndex,
        start_time: '09:00',
        end_time: '18:00',
        is_active: true,
        [field]: val
      });
    }
    setWindows(updated);
  };

  const handleSaveAll = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !pref) return;

    try {
      setSaving(true);
      setSaveSuccess(false);
      setSaveError(null);

      // Validate times
      for (const w of windows) {
        if (w.is_active && w.start_time >= w.end_time) {
          throw new Error(`On ${DAYS_NAMES[w.day_of_week]}, end time must be after start time.`);
        }
      }

      await Promise.all([
        api.updateProfile({ display_name: profile.display_name, timezone: profile.timezone }),
        api.updatePreferences({
          preferred_session_minutes: Number(pref.preferred_session_minutes),
          break_duration_minutes: Number(pref.break_duration_minutes),
          maximum_daily_study_minutes: Number(pref.maximum_daily_study_minutes)
        }),
        api.updateAvailability(windows)
      ]);

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      setSaveError(err.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-16 text-center text-slate-400 text-xs">
        <div className="w-8 h-8 border-3 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-2" />
        Loading settings...
      </div>
    );
  }

  return (
    <form onSubmit={handleSaveAll} className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Profile & Study Preferences</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Configure your student display name, target session lengths, daily limits, and weekly availability.
          </p>
        </div>
        <button
          type="submit"
          disabled={saving}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-indigo-600/25 transition-all self-start sm:self-auto"
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving Changes...' : 'Save Settings'}</span>
        </button>
      </div>

      {saveSuccess && (
        <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-xs flex items-center space-x-2">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>Preferences and availability windows successfully updated!</span>
        </div>
      )}

      {saveError && (
        <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
          {saveError}
        </div>
      )}

      {/* Profile Section */}
      {profile && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <User className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-bold text-slate-100">Student Profile</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Display Name</label>
              <input
                type="text"
                required
                value={profile.display_name}
                onChange={(e) => setProfile({ ...profile, display_name: e.target.value })}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-slate-300 font-semibold mb-1">Timezone</label>
              <input
                type="text"
                required
                value={profile.timezone}
                onChange={(e) => setProfile({ ...profile, timezone: e.target.value })}
                placeholder="e.g. UTC, America/New_York"
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Study Preferences Section */}
      {pref && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Clock className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-bold text-slate-100">Study Session Constraints</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Preferred Session Length (Mins)
              </label>
              <input
                type="number"
                min="15"
                max="180"
                required
                value={pref.preferred_session_minutes}
                onChange={(e) => setPref({ ...pref, preferred_session_minutes: Number(e.target.value) })}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">Default task block split size</span>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Break Duration (Mins)
              </label>
              <input
                type="number"
                min="0"
                max="60"
                required
                value={pref.break_duration_minutes}
                onChange={(e) => setPref({ ...pref, break_duration_minutes: Number(e.target.value) })}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">Buffer between sessions</span>
            </div>

            <div>
              <label className="block text-slate-300 font-semibold mb-1">
                Max Daily Study Time (Mins)
              </label>
              <input
                type="number"
                min="30"
                max="960"
                required
                value={pref.maximum_daily_study_minutes}
                onChange={(e) => setPref({ ...pref, maximum_daily_study_minutes: Number(e.target.value) })}
                className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">Prevents student burnout</span>
            </div>
          </div>
        </div>
      )}

      {/* Weekly Availability Windows */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
          <Calendar className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-bold text-slate-100">Weekly Availability Windows</h2>
        </div>
        <p className="text-xs text-slate-400">
          Specify which days of the week you are available for studying and the permitted daily time window.
        </p>

        <div className="space-y-2.5">
          {DAYS_NAMES.map((dayName, dayIndex) => {
            const win = windows.find((w) => w.day_of_week === dayIndex) || {
              day_of_week: dayIndex,
              start_time: '09:00',
              end_time: '18:00',
              is_active: true
            };

            return (
              <div
                key={dayIndex}
                className={`p-3 rounded-xl border text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                  win.is_active
                    ? 'bg-slate-800/40 border-slate-800'
                    : 'bg-slate-900/30 border-slate-850 opacity-50'
                }`}
              >
                <div className="flex items-center space-x-3 w-36">
                  <input
                    type="checkbox"
                    checked={win.is_active}
                    onChange={(e) => handleWindowChange(dayIndex, 'is_active', e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0"
                  />
                  <span className="font-semibold text-slate-200">{dayName}</span>
                </div>

                <div className="flex items-center space-x-3 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-slate-500">From</span>
                    <input
                      type="time"
                      disabled={!win.is_active}
                      value={win.start_time}
                      onChange={(e) => handleWindowChange(dayIndex, 'start_time', e.target.value)}
                      className="px-2 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 font-mono disabled:opacity-40"
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-slate-500">To</span>
                    <input
                      type="time"
                      disabled={!win.is_active}
                      value={win.end_time}
                      onChange={(e) => handleWindowChange(dayIndex, 'end_time', e.target.value)}
                      className="px-2 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 font-mono disabled:opacity-40"
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </form>
  );
};
