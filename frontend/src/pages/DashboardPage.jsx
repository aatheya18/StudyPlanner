import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import StatCard from '../components/StatCard';
import WeekView from '../components/Calendar/WeekView';
import MonthView from '../components/Calendar/MonthView';
import { 
  CheckCircle2, 
  Clock, 
  Hourglass, 
  Sparkles, 
  AlertTriangle,
  Calendar as CalendarIcon,
  RefreshCw
} from 'lucide-react';

export default function DashboardPage() {
  const { apiFetch } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [atRiskTasks, setAtRiskTasks] = useState([]);
  const [stats, setStats] = useState({
    pending_count: 0,
    completed_count: 0,
    total_planned_minutes: 0,
    total_tasks_scheduled: 0
  });

  const [viewMode, setViewMode] = useState('week'); // 'week' or 'month'
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [notification, setNotification] = useState(null);

  const fetchPlanData = async () => {
    try {
      const data = await apiFetch('/plan/sessions');
      setSessions(data.sessions || []);
      setAtRiskTasks(data.at_risk_tasks || []);
      if (data.stats) {
        setStats(data.stats);
      }
    } catch (err) {
      console.error('Failed to load plan sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlanData();
  }, []);

  const handleGeneratePlan = async () => {
    setGenerating(true);
    setNotification(null);
    try {
      const data = await apiFetch('/plan/generate', { method: 'POST' });
      setSessions(data.sessions || []);
      setAtRiskTasks(data.at_risk_tasks || []);
      if (data.stats) {
        setStats(data.stats);
      }
      setNotification({
        type: 'success',
        message: `Plan generated! Scheduled ${data.sessions.length} study session(s) across your available days.`
      });
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to generate plan'
      });
    } finally {
      setGenerating(false);
    }
  };

  // Format minutes into "Xh Ym" or "0m"
  const formatStudyTime = (mins) => {
    if (!mins || mins <= 0) return '0m';
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    if (h === 0) return `${m}m`;
    if (m === 0) return `${h}h`;
    return `${h}h ${m}m`;
  };

  return (
    <div className="dashboard-page">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-title-group">
          <h2>Dashboard</h2>
          <p>Overview of your study sessions, pending milestones, and intelligent schedule.</p>
        </div>

        <div className="page-actions">
          <div className="view-toggle">
            <button
              id="view-toggle-week"
              type="button"
              className={`view-toggle-btn ${viewMode === 'week' ? 'active' : ''}`}
              onClick={() => setViewMode('week')}
            >
              Week View
            </button>
            <button
              id="view-toggle-month"
              type="button"
              className={`view-toggle-btn ${viewMode === 'month' ? 'active' : ''}`}
              onClick={() => setViewMode('month')}
            >
              Month View
            </button>
          </div>

          <button
            id="generate-plan-btn"
            type="button"
            className="btn btn-primary"
            onClick={handleGeneratePlan}
            disabled={generating}
          >
            {generating ? (
              <>
                <RefreshCw size={16} className="spin-icon" style={{ animation: 'spin 1s linear infinite' }} />
                <span>Optimizing Schedule...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Generate Plan</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Notification toast/message if any */}
      {notification && (
        <div style={{
          backgroundColor: notification.type === 'error' ? 'var(--danger-bg)' : 'var(--success-bg)',
          color: notification.type === 'error' ? 'var(--danger-text)' : 'var(--success-text)',
          border: `1px solid ${notification.type === 'error' ? 'var(--danger-border)' : 'var(--success-border)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          marginBottom: '20px',
          fontSize: '13px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{notification.message}</span>
          <button 
            type="button" 
            onClick={() => setNotification(null)}
            style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 700 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Top Stat Cards */}
      <div className="stats-grid">
        <StatCard
          icon={Hourglass}
          value={stats.pending_count}
          label="Pending Tasks"
          accentColor="var(--dusty-olive)"
        />
        <StatCard
          icon={CheckCircle2}
          value={stats.completed_count}
          label="Completed Tasks"
          accentColor="var(--palm-leaf)"
        />
        <StatCard
          icon={Clock}
          value={formatStudyTime(stats.total_planned_minutes)}
          label="Total Planned Study"
          accentColor="var(--golden-sand)"
        />
      </div>

      {/* Warning List for Tasks at Risk / May Remain Incomplete */}
      {atRiskTasks.length > 0 && (
        <div className="warning-banner" id="at-risk-warning-banner">
          <AlertTriangle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1 }}>
            <h4>At Risk Tasks ({atRiskTasks.length})</h4>
            <p style={{ fontSize: '12px', marginBottom: '8px' }}>
              The following task(s) cannot be fully completed before their deadline due to limited available time in your profile schedule:
            </p>
            <ul>
              {atRiskTasks.map((t) => (
                <li key={t.id}>
                  <span className="badge-risk">At Risk</span>
                  <strong>{t.title}</strong>
                  {t.subject_name && (
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      ({t.subject_name})
                    </span>
                  )}
                  <span>— {t.reason}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Calendar Section */}
      <div className="calendar-section">
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            Loading study schedule...
          </div>
        ) : sessions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 20px' }}>
            <CalendarIcon size={44} style={{ color: 'var(--text-muted)', marginBottom: '12px', opacity: 0.6 }} />
            <h3 style={{ fontSize: '18px', marginBottom: '6px' }}>No Study Plan Generated Yet</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '440px', margin: '0 auto 20px auto' }}>
              Add your subjects and tasks, then click <strong>"Generate Plan"</strong> to automatically create an optimized study schedule matching your availability.
            </p>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleGeneratePlan}
              disabled={generating}
            >
              <Sparkles size={16} />
              <span>Generate My Study Plan</span>
            </button>
          </div>
        ) : viewMode === 'week' ? (
          <WeekView
            sessions={sessions}
            currentDate={calendarDate}
            onDateChange={setCalendarDate}
          />
        ) : (
          <MonthView
            sessions={sessions}
            currentDate={calendarDate}
            onDateChange={setCalendarDate}
          />
        )}
      </div>
    </div>
  );
}
