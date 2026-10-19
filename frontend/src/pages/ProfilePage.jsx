import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  User, 
  Clock, 
  Calendar, 
  Palette, 
  Save, 
  CheckCircle2, 
  AlertCircle 
} from 'lucide-react';

const DAYS_OF_WEEK = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday'
];

export default function ProfilePage() {
  const { apiFetch, user, setUser, theme, setTheme } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [sessionLength, setSessionLength] = useState(45);
  const [breakLength, setBreakLength] = useState(15);
  const [dailyDurationCap, setDailyDurationCap] = useState(240);
  const [selectedTheme, setSelectedTheme] = useState(theme);

  // 7 days availability
  const [availability, setAvailability] = useState(
    DAYS_OF_WEEK.map((_, idx) => ({
      day_of_week: idx,
      is_enabled: true,
      start_time: '09:00',
      end_time: '18:00'
    }))
  );

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await apiFetch('/profile');
        if (data.settings) {
          setDisplayName(data.settings.display_name || '');
          setSessionLength(data.settings.session_length || 45);
          setBreakLength(data.settings.break_length || 15);
          setDailyDurationCap(data.settings.daily_duration_cap || 240);
          if (data.settings.theme) {
            setSelectedTheme(data.settings.theme);
            setTheme(data.settings.theme);
          }
        }
        if (data.availability && data.availability.length > 0) {
          setAvailability(data.availability);
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleThemeChange = (newTheme) => {
    setSelectedTheme(newTheme);
    setTheme(newTheme); // Immediate application
  };

  const handleAvailabilityToggle = (dow) => {
    setAvailability((prev) =>
      prev.map((item) =>
        item.day_of_week === dow
          ? { ...item, is_enabled: !item.is_enabled }
          : item
      )
    );
  };

  const handleTimeChange = (dow, field, value) => {
    setAvailability((prev) =>
      prev.map((item) =>
        item.day_of_week === dow
          ? { ...item, [field]: value }
          : item
      )
    );
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setFeedback(null);

    // Validation
    const sess = Number(sessionLength);
    const brk = Number(breakLength);
    const cap = Number(dailyDurationCap);

    if (sess <= 0 || cap <= 0 || brk < 0) {
      setFeedback({
        type: 'error',
        message: 'Session length and daily duration must be positive numbers. Break length cannot be negative.'
      });
      return;
    }

    if (sess > cap) {
      setFeedback({
        type: 'error',
        message: 'Preferred session length cannot exceed total daily study duration.'
      });
      return;
    }

    // Validate times for enabled days
    for (const item of availability) {
      if (item.is_enabled) {
        const [sh, sm] = item.start_time.split(':').map(Number);
        const [eh, em] = item.end_time.split(':').map(Number);
        if (eh * 60 + em <= sh * 60 + sm) {
          setFeedback({
            type: 'error',
            message: `End time must be after start time on ${DAYS_OF_WEEK[item.day_of_week]}.`
          });
          return;
        }
      }
    }

    setSaving(true);
    try {
      const res = await apiFetch('/profile', {
        method: 'PUT',
        body: JSON.stringify({
          settings: {
            display_name: displayName.trim(),
            session_length: sess,
            break_length: brk,
            daily_duration_cap: cap,
            theme: selectedTheme
          },
          availability
        })
      });

      setUser((prev) => ({
        ...prev,
        display_name: displayName.trim() || prev.username,
        theme: selectedTheme
      }));

      setFeedback({
        type: 'success',
        message: 'Profile settings and weekly availability saved successfully!'
      });
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to save settings'
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
        Loading profile settings...
      </div>
    );
  }

  return (
    <div className="profile-page" style={{ maxWidth: '820px' }}>
      <div className="page-header">
        <div className="page-title-group">
          <h2>Profile & Preferences</h2>
          <p>Customize your study duration caps, session chunk lengths, and 7-day schedule.</p>
        </div>
      </div>

      {feedback && (
        <div style={{
          backgroundColor: feedback.type === 'error' ? 'var(--danger-bg)' : 'var(--success-bg)',
          color: feedback.type === 'error' ? 'var(--danger-text)' : 'var(--success-text)',
          border: `1px solid ${feedback.type === 'error' ? 'var(--danger-border)' : 'var(--success-border)'}`,
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          marginBottom: '20px',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {feedback.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
          <span>{feedback.message}</span>
        </div>
      )}

      <form onSubmit={handleSave}>
        {/* General Profile & Theme */}
        <div className="profile-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <User size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '17px' }}>Account & Appearance</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="profile-display-name">Display Name</label>
              <input
                id="profile-display-name"
                type="text"
                className="form-input"
                placeholder="e.g. Alex"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Theme</label>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  id="theme-light-btn"
                  type="button"
                  className={`btn ${selectedTheme === 'light' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1 }}
                  onClick={() => handleThemeChange('light')}
                >
                  Light Mode
                </button>
                <button
                  id="theme-dark-btn"
                  type="button"
                  className={`btn ${selectedTheme === 'dark' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ flex: 1 }}
                  onClick={() => handleThemeChange('dark')}
                >
                  Dark Mode
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Study Timing Preferences */}
        <div className="profile-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Clock size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '17px' }}>Study Session Durations</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="pref-session-length">
                Preferred Session Length (mins)
              </label>
              <input
                id="pref-session-length"
                type="number"
                className="form-input"
                min="15"
                step="5"
                value={sessionLength}
                onChange={(e) => setSessionLength(e.target.value)}
                required
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Default: 45 mins. Long tasks split into these chunks.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="pref-break-length">
                Preferred Break Length (mins)
              </label>
              <input
                id="pref-break-length"
                type="number"
                className="form-input"
                min="0"
                step="5"
                value={breakLength}
                onChange={(e) => setBreakLength(e.target.value)}
                required
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Default: 15 mins. Placed between consecutive study sessions.
              </span>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="pref-daily-cap">
                Total Daily Study Cap (mins)
              </label>
              <input
                id="pref-daily-cap"
                type="number"
                className="form-input"
                min="30"
                step="15"
                value={dailyDurationCap}
                onChange={(e) => setDailyDurationCap(e.target.value)}
                required
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Default: 240 mins (4 hours) under relaxed scheduling.
              </span>
            </div>
          </div>
        </div>

        {/* Weekly Availability */}
        <div className="profile-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Calendar size={18} style={{ color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: '17px' }}>Weekly Availability (Monday – Sunday)</h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Specify the days you can study and your available hours (24-hour HH:MM format).
          </p>

          <div className="availability-grid">
            {availability.map((item) => {
              const dow = item.day_of_week;
              const dayName = DAYS_OF_WEEK[dow];

              return (
                <div key={dow} className="avail-row">
                  <label className="avail-day-name" style={{ cursor: 'pointer' }}>
                    <input
                      id={`avail-day-checkbox-${dow}`}
                      type="checkbox"
                      checked={item.is_enabled}
                      onChange={() => handleAvailabilityToggle(dow)}
                      style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
                    />
                    <span style={{ color: item.is_enabled ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                      {dayName}
                    </span>
                  </label>

                  <div className="avail-times" style={{ opacity: item.is_enabled ? 1 : 0.4 }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>From</span>
                    <input
                      id={`avail-start-${dow}`}
                      type="time"
                      className="avail-time-input"
                      value={item.start_time}
                      disabled={!item.is_enabled}
                      onChange={(e) => handleTimeChange(dow, 'start_time', e.target.value)}
                      required={item.is_enabled}
                    />
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>To</span>
                    <input
                      id={`avail-end-${dow}`}
                      type="time"
                      className="avail-time-input"
                      value={item.end_time}
                      disabled={!item.is_enabled}
                      onChange={(e) => handleTimeChange(dow, 'end_time', e.target.value)}
                      required={item.is_enabled}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button
            id="save-profile-btn"
            type="submit"
            className="btn btn-primary"
            disabled={saving}
            style={{ padding: '12px 28px', fontSize: '15px' }}
          >
            <Save size={16} />
            <span>{saving ? 'Saving Preferences...' : 'Save Profile Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}
