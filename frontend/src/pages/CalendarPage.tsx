import React, { useEffect, useState } from 'react';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RotateCcw,
  Check,
  Plus
} from 'lucide-react';
import { StudySession, ScheduleGenerateResponse } from '../types';
import { api } from '../services/api';
import { Modal } from '../components/common/Modal';

export const CalendarPage: React.FC = () => {
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [currentWeekStart, setCurrentWeekStart] = useState<Date>(() => {
    const d = new Date();
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Monday
    const monday = new Date(d.setDate(diff));
    monday.setHours(0, 0, 0, 0);
    return monday;
  });

  // Selected Session for Details Modal
  const [selectedSession, setSelectedSession] = useState<StudySession | null>(null);
  const [actualDuration, setActualDuration] = useState<number>(45);
  const [markTaskComplete, setMarkTaskComplete] = useState<boolean>(false);
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  // Generate Schedule Modal
  const [isGenerateOpen, setIsGenerateOpen] = useState<boolean>(false);
  const [genHorizon, setGenHorizon] = useState<number>(7);
  const [genClearExisting, setGenClearExisting] = useState<boolean>(true);
  const [genLoading, setGenLoading] = useState<boolean>(false);
  const [genResult, setGenResult] = useState<ScheduleGenerateResponse | null>(null);

  useEffect(() => {
    loadSessions();
  }, [currentWeekStart]);

  const loadSessions = async () => {
    try {
      setLoading(true);
      const weekEnd = new Date(currentWeekStart);
      weekEnd.setDate(weekEnd.getDate() + 7);

      const data = await api.getSessions({
        start: currentWeekStart.toISOString(),
        end: weekEnd.toISOString()
      });
      setSessions(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePrevWeek = () => {
    const d = new Date(currentWeekStart);
    d.setDate(d.getDate() - 7);
    setCurrentWeekStart(d);
  };

  const handleNextWeek = () => {
    const d = new Date(currentWeekStart);
    d.setDate(d.getDate() + 7);
    setCurrentWeekStart(d);
  };

  const handleToday = () => {
    const d = new Date();
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(d.setDate(diff));
    monday.setHours(0, 0, 0, 0);
    setCurrentWeekStart(monday);
  };

  const openSessionDetails = (sess: StudySession) => {
    setSelectedSession(sess);
    const dur = Math.round((new Date(sess.end_at).getTime() - new Date(sess.start_at).getTime()) / 60000);
    setActualDuration(sess.actual_duration_minutes || dur);
    setMarkTaskComplete(false);
  };

  const handleCompleteSession = async () => {
    if (!selectedSession) return;
    try {
      setModalLoading(true);
      await api.completeSession(selectedSession.id, {
        actual_duration_minutes: Number(actualDuration),
        mark_task_completed: markTaskComplete
      });
      setSelectedSession(null);
      await loadSessions();
    } catch (err: any) {
      alert(`Error completing session: ${err.message}`);
    } finally {
      setModalLoading(false);
    }
  };

  const handleSkipSession = async () => {
    if (!selectedSession) return;
    try {
      setModalLoading(true);
      await api.skipSession(selectedSession.id);
      setSelectedSession(null);
      await loadSessions();
    } catch (err: any) {
      alert(`Error skipping session: ${err.message}`);
    } finally {
      setModalLoading(false);
    }
  };

  const handleTriggerGenerate = async () => {
    try {
      setGenLoading(true);
      const res = await api.generateSchedule({
        horizon_days: genHorizon,
        clear_existing_scheduled: genClearExisting
      });
      setGenResult(res);
      await loadSessions();
    } catch (err: any) {
      alert(`Schedule generation failed: ${err.message}`);
    } finally {
      setGenLoading(false);
    }
  };

  // Generate 7 days of current week
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(currentWeekStart);
    d.setDate(d.getDate() + i);
    return d;
  });

  return (
    <div className="space-y-6">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Calendar & Study Sessions</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Weekly timetable of rule-based scheduled study blocks and session tracking.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => {
              setGenResult(null);
              setIsGenerateOpen(true);
            }}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-indigo-600/25 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>Generate Schedule</span>
          </button>
        </div>
      </div>

      {/* Week Navigation Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={handlePrevWeek}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextWeek}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={handleToday}
            className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-750 text-slate-200 text-xs font-semibold border border-slate-700/60"
          >
            Today
          </button>
        </div>

        <div className="text-sm font-bold text-slate-200">
          {weekDays[0].toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} –{' '}
          {weekDays[6].toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>

        <div className="text-xs text-slate-400 hidden sm:block">
          Total Sessions This Week: <span className="font-bold text-slate-200">{sessions.length}</span>
        </div>
      </div>

      {/* 7-Day Week Columns */}
      <div className="grid grid-cols-1 md:grid-cols-7 gap-3 min-h-[500px]">
        {weekDays.map((dayDate, idx) => {
          const isToday = new Date().toDateString() === dayDate.toDateString();
          // Filter sessions for this day
          const daySessions = sessions.filter((s) => {
            const sDate = new Date(s.start_at);
            return sDate.toDateString() === dayDate.toDateString();
          });

          return (
            <div
              key={idx}
              className={`rounded-2xl border p-3 flex flex-col min-h-[300px] ${
                isToday
                  ? 'bg-slate-900/90 border-indigo-500/50 shadow-lg shadow-indigo-950/30'
                  : 'glass-panel border-slate-800'
              }`}
            >
              {/* Day Header */}
              <div className="pb-3 border-b border-slate-800 mb-3 text-center">
                <span className="text-[11px] font-semibold uppercase text-slate-400 block">
                  {dayDate.toLocaleDateString(undefined, { weekday: 'short' })}
                </span>
                <span className={`text-base font-bold inline-block mt-0.5 px-2 py-0.5 rounded-full ${
                  isToday ? 'bg-indigo-600 text-white' : 'text-slate-200'
                }`}>
                  {dayDate.getDate()}
                </span>
              </div>

              {/* Sessions List */}
              <div className="space-y-2 flex-1 overflow-y-auto">
                {daySessions.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-[11px] text-slate-600 italic py-8 text-center">
                    No sessions
                  </div>
                ) : (
                  daySessions.map((s) => {
                    const startStr = new Date(s.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    const endStr = new Date(s.end_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    const isDone = s.status === 'Completed';
                    const isSkipped = s.status === 'Skipped';

                    return (
                      <div
                        key={s.id}
                        onClick={() => openSessionDetails(s)}
                        className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-all hover:scale-[1.02] ${
                          isDone
                            ? 'bg-emerald-950/20 border-emerald-800/40 opacity-75'
                            : isSkipped
                            ? 'bg-slate-900/40 border-slate-800 opacity-50 line-through'
                            : 'bg-slate-800/70 border-slate-750 hover:border-indigo-500/50 shadow-sm'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className="px-1.5 py-0.2 rounded text-[9px] font-bold truncate max-w-[80px]"
                            style={{
                              backgroundColor: `${s.subject_color || '#3B82F6'}20`,
                              color: s.subject_color || '#3B82F6'
                            }}
                          >
                            {s.subject_name || 'Subject'}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {startStr}
                          </span>
                        </div>
                        <div className="font-semibold text-slate-200 text-xs truncate">
                          {s.task_title || 'Study Session'}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-1 flex items-center justify-between">
                          <span>{startStr} - {endStr}</span>
                          {isDone && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Session Details Modal */}
      <Modal
        isOpen={selectedSession !== null}
        onClose={() => setSelectedSession(null)}
        title="Study Session Details"
      >
        {selectedSession && (
          <div className="space-y-4 text-xs">
            <div>
              <span
                className="px-2 py-0.5 rounded text-[10px] font-bold inline-block mb-1"
                style={{
                  backgroundColor: `${selectedSession.subject_color || '#3B82F6'}20`,
                  color: selectedSession.subject_color || '#3B82F6'
                }}
              >
                {selectedSession.subject_name || 'Subject'}
              </span>
              <h3 className="text-base font-bold text-slate-100">{selectedSession.task_title}</h3>
            </div>

            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-800">
              <div>
                <span className="text-[10px] text-slate-500 block">Scheduled Window</span>
                <span className="text-slate-200 font-semibold mt-0.5 block">
                  {new Date(selectedSession.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                  {new Date(selectedSession.end_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">Status</span>
                <span className={`font-semibold mt-0.5 block ${
                  selectedSession.status === 'Completed' ? 'text-emerald-400' : 'text-slate-300'
                }`}>
                  {selectedSession.status}
                </span>
              </div>
            </div>

            {selectedSession.status !== 'Completed' && (
              <div className="space-y-3 pt-2">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">
                    Actual Study Duration (minutes)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="600"
                    value={actualDuration}
                    onChange={(e) => setActualDuration(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={markTaskComplete}
                    onChange={(e) => setMarkTaskComplete(e.target.checked)}
                    className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0"
                  />
                  <span>Mark overall task as fully Completed as well</span>
                </label>
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-slate-800">
              {selectedSession.status !== 'Completed' && (
                <button
                  type="button"
                  disabled={modalLoading}
                  onClick={handleSkipSession}
                  className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-slate-200"
                >
                  Skip Session
                </button>
              )}
              <div className="flex items-center space-x-2 ml-auto">
                <button
                  type="button"
                  onClick={() => setSelectedSession(null)}
                  className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300"
                >
                  Close
                </button>
                {selectedSession.status !== 'Completed' && (
                  <button
                    type="button"
                    disabled={modalLoading}
                    onClick={handleCompleteSession}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center space-x-1.5"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{modalLoading ? 'Saving...' : 'Complete Session'}</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Generate Schedule Modal */}
      <Modal
        isOpen={isGenerateOpen}
        onClose={() => setIsGenerateOpen(false)}
        title="Generate Study Schedule"
        maxWidth="max-w-md"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-400 leading-relaxed">
            The rule-based scheduler evaluates task priority, deadline urgency, daily study limits, and breaks
            to place incomplete tasks into available time slots.
          </p>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Planning Horizon (Days)</label>
            <input
              type="number"
              min="1"
              max="14"
              value={genHorizon}
              onChange={(e) => setGenHorizon(Number(e.target.value))}
              className="w-full px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <label className="flex items-center space-x-2 text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={genClearExisting}
              onChange={(e) => setGenClearExisting(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-0"
            />
            <span>Clear existing upcoming uncompleted sessions before generating</span>
          </label>

          {genResult && (
            <div className="p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 space-y-2">
              <div className="font-semibold text-emerald-400">{genResult.message}</div>
              {genResult.unscheduled_tasks.length > 0 && (
                <div className="mt-2 space-y-1">
                  <span className="font-bold text-amber-400 block">Unscheduled Tasks ({genResult.unscheduled_tasks.length}):</span>
                  {genResult.unscheduled_tasks.map((u) => (
                    <div key={u.task_id} className="text-[11px] text-slate-300">
                      • <span className="font-semibold">{u.title}:</span> {u.reason}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsGenerateOpen(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 font-medium"
            >
              {genResult ? 'Done' : 'Cancel'}
            </button>
            <button
              type="button"
              disabled={genLoading}
              onClick={handleTriggerGenerate}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold flex items-center space-x-1.5 shadow-lg shadow-indigo-600/25"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{genLoading ? 'Computing...' : 'Run Scheduler'}</span>
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
