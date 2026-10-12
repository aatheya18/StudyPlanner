import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight,
  TrendingUp,
  Sparkles,
  BookOpen,
  Play
} from 'lucide-react';
import { DashboardSummary, StudySession } from '../types';
import { api } from '../services/api';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [completingId, setCompletingId] = useState<number | null>(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const summary = await api.getDashboard();
      setData(summary);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickComplete = async (session: StudySession) => {
    try {
      setCompletingId(session.id);
      await api.completeSession(session.id, { mark_task_completed: false });
      await loadDashboard();
    } catch (err: any) {
      alert(`Error completing session: ${err.message}`);
    } finally {
      setCompletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading student metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <div className="p-4 rounded-xl bg-rose-950/30 border border-rose-800 text-rose-300 text-sm flex items-center justify-between">
          <span>{error || 'Unable to load dashboard summary'}</span>
          <button
            onClick={loadDashboard}
            className="px-3 py-1 rounded-lg bg-rose-900/60 hover:bg-rose-800 text-xs text-white"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Calculate highest planned minutes for chart scaling
  const maxMins = Math.max(1, ...data.weekly_progress.map(p => Math.max(p.planned_minutes, p.completed_minutes)));

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900/80 to-slate-900/40 border border-indigo-900/40 backdrop-blur-xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Academic Overview</h1>
          <p className="text-sm text-slate-400 mt-1">
            Track daily study load, active schedules, and rule-based progress.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Link
            to="/calendar"
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-2 shadow-lg shadow-indigo-600/25 transition-all"
          >
            <Calendar className="w-4 h-4" />
            <span>Open Calendar</span>
          </Link>
          <Link
            to="/ai-suggestions"
            className="px-4 py-2 rounded-xl bg-violet-600/20 hover:bg-violet-600/30 text-violet-300 border border-violet-500/30 text-xs font-semibold flex items-center space-x-2 transition-all"
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Suggestions</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Planned Study Time */}
        <div className="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400">Total Planned Study</span>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {Math.floor(data.total_planned_minutes / 60)}h {data.total_planned_minutes % 60}m
            </div>
            <span className="text-[11px] text-indigo-400 mt-1 block">Cumulative planned load</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* Total Completed Study Time */}
        <div className="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400">Completed Study Time</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {Math.floor(data.total_completed_minutes / 60)}h {data.total_completed_minutes % 60}m
            </div>
            <span className="text-[11px] text-emerald-500 mt-1 block">Logged study minutes</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Pending Tasks */}
        <div className="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400">Tasks Pending</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">
              {data.pending_tasks_count}
            </div>
            <span className="text-[11px] text-slate-400 mt-1 block">Awaiting completion</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <BookOpen className="w-6 h-6" />
          </div>
        </div>

        {/* Completed Tasks */}
        <div className="glass-card p-5 rounded-2xl flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-400">Tasks Completed</span>
            <div className="text-2xl font-bold text-sky-400 mt-1">
              {data.completed_tasks_count}
            </div>
            <span className="text-[11px] text-sky-400 mt-1 block">Fully achieved</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Grid: Weekly Chart & Today Sessions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Progress Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-indigo-400" />
                <span>Weekly Study Distribution</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Planned vs Actual study duration across the week</p>
            </div>
            <div className="flex items-center space-x-4 text-xs">
              <span className="flex items-center space-x-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500"></span>
                <span>Planned</span>
              </span>
              <span className="flex items-center space-x-1.5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400"></span>
                <span>Completed</span>
              </span>
            </div>
          </div>

          {/* Bar Chart Visualization */}
          <div className="h-56 flex items-end justify-between gap-3 pt-6 pb-2 px-2 border-b border-slate-800">
            {data.weekly_progress.map((pt, idx) => {
              const plannedHeight = Math.round((pt.planned_minutes / maxMins) * 160);
              const completedHeight = Math.round((pt.completed_minutes / maxMins) * 160);
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2 group">
                  <div className="w-full flex items-end justify-center gap-1.5 h-44">
                    {/* Planned Bar */}
                    <div
                      style={{ height: `${Math.max(6, plannedHeight)}px` }}
                      className="w-3.5 sm:w-5 bg-indigo-600/50 hover:bg-indigo-500 rounded-t-md transition-all relative"
                    >
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-[10px] text-white px-1.5 py-0.5 rounded shadow pointer-events-none transition-opacity whitespace-nowrap z-10">
                        {pt.planned_minutes}m
                      </div>
                    </div>
                    {/* Completed Bar */}
                    <div
                      style={{ height: `${Math.max(6, completedHeight)}px` }}
                      className="w-3.5 sm:w-5 bg-emerald-500 hover:bg-emerald-400 rounded-t-md transition-all relative"
                    >
                      <div className="opacity-0 group-hover:opacity-100 absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-[10px] text-white px-1.5 py-0.5 rounded shadow pointer-events-none transition-opacity whitespace-nowrap z-10">
                        {pt.completed_minutes}m
                      </div>
                    </div>
                  </div>
                  <div className="text-center">
                    <span className="block text-xs font-semibold text-slate-300">{pt.day}</span>
                    <span className="block text-[10px] text-slate-500">{pt.date.slice(5)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Today's Scheduled Sessions */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-indigo-400" />
                <span>Today's Sessions</span>
              </h3>
              <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded-full font-medium">
                {data.today_sessions.length}
              </span>
            </div>

            {data.today_sessions.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-xs">
                <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p>No study sessions scheduled for today.</p>
                <Link
                  to="/calendar"
                  className="mt-3 inline-block text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
                >
                  Generate or schedule a session →
                </Link>
              </div>
            ) : (
              <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                {data.today_sessions.map((sess) => {
                  const sStart = new Date(sess.start_at);
                  const sEnd = new Date(sess.end_at);
                  const isDone = sess.status === 'Completed';

                  return (
                    <div
                      key={sess.id}
                      className={`p-3 rounded-xl border text-xs transition-all ${
                        isDone
                          ? 'bg-slate-900/40 border-slate-800 opacity-60'
                          : 'bg-slate-800/40 border-slate-700/60 hover:border-indigo-500/40'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span
                          className="px-2 py-0.5 rounded text-[10px] font-bold"
                          style={{
                            backgroundColor: `${sess.subject_color || '#3B82F6'}20`,
                            color: sess.subject_color || '#3B82F6',
                            border: `1px solid ${sess.subject_color || '#3B82F6'}40`
                          }}
                        >
                          {sess.subject_name || 'Subject'}
                        </span>
                        <span className="text-[11px] font-medium text-slate-400 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            {sStart.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                            {sEnd.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </span>
                      </div>
                      <div className="font-semibold text-slate-200 text-sm truncate">{sess.task_title}</div>

                      <div className="mt-2 flex items-center justify-between pt-2 border-t border-slate-800/80">
                        <span className={`text-[10px] font-medium ${isDone ? 'text-emerald-400' : 'text-slate-400'}`}>
                          Status: {sess.status}
                        </span>
                        {!isDone && (
                          <button
                            disabled={completingId === sess.id}
                            onClick={() => handleQuickComplete(sess)}
                            className="px-2.5 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-[11px] font-medium flex items-center space-x-1"
                          >
                            <CheckCircle2 className="w-3 h-3" />
                            <span>{completingId === sess.id ? 'Saving...' : 'Mark Complete'}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <Link
            to="/calendar"
            className="mt-4 w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white text-xs font-semibold flex items-center justify-center space-x-1 transition-colors"
          >
            <span>View Full Calendar</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Deadlines Section: Tasks Due Soon & Overdue */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Due Soon */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <span>Approaching Deadlines (Next 72 Hours)</span>
            </h3>
            <span className="text-xs px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full font-medium">
              {data.tasks_due_soon.length}
            </span>
          </div>

          {data.tasks_due_soon.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No tasks due within the next 3 days.</p>
          ) : (
            <div className="space-y-2">
              {data.tasks_due_soon.map((task) => (
                <div key={task.id} className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-200">{task.title}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      Due: {new Date(task.due_at).toLocaleDateString()} {new Date(task.due_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    task.priority === 'High' ? 'bg-rose-500/20 text-rose-300' : 'bg-slate-700 text-slate-300'
                  }`}>
                    {task.priority}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Overdue Tasks */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              <span>Overdue Tasks</span>
            </h3>
            <span className="text-xs px-2 py-0.5 bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-full font-medium">
              {data.overdue_tasks.length}
            </span>
          </div>

          {data.overdue_tasks.length === 0 ? (
            <div className="py-4 text-center text-xs text-slate-500 flex items-center justify-center space-x-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Great job! No overdue tasks.</span>
            </div>
          ) : (
            <div className="space-y-2">
              {data.overdue_tasks.map((task) => (
                <div key={task.id} className="p-3 rounded-xl bg-rose-950/20 border border-rose-900/40 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-rose-200">{task.title}</div>
                    <div className="text-[11px] text-rose-400/80 mt-0.5">
                      Missed: {new Date(task.due_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Link
                    to="/tasks"
                    className="px-2 py-1 rounded bg-rose-900/40 hover:bg-rose-800/60 text-white text-[11px] font-medium"
                  >
                    Reschedule
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
