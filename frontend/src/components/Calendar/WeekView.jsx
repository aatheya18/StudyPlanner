import React from 'react';
import { Clock, BookOpen, ChevronLeft, ChevronRight } from 'lucide-react';

export default function WeekView({ sessions, currentDate, onDateChange }) {
  // Compute start of week (Monday) for currentDate
  const getMonday = (d) => {
    const date = new Date(d);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
    return new Date(date.setDate(diff));
  };

  const monday = getMonday(currentDate);

  // Generate 7 days of this week
  const weekDays = Array.from({ length: 7 }).map((_, idx) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + idx);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const dateString = `${yyyy}-${mm}-${dd}`;
    return {
      date: d,
      dateString,
      dayName: d.toLocaleDateString('en-US', { weekday: 'short' }),
      displayDate: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      isToday: new Date().toDateString() === d.toDateString()
    };
  });

  const nextWeek = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + 7);
    onDateChange(d);
  };

  const prevWeek = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() - 7);
    onDateChange(d);
  };

  const goToday = () => {
    onDateChange(new Date());
  };

  // Group sessions by date
  const sessionsByDate = {};
  sessions.forEach((s) => {
    if (!sessionsByDate[s.session_date]) {
      sessionsByDate[s.session_date] = [];
    }
    sessionsByDate[s.session_date].push(s);
  });

  return (
    <div className="week-view-wrapper">
      <div className="calendar-controls">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button type="button" className="btn btn-secondary btn-icon" onClick={prevWeek} title="Previous Week">
            <ChevronLeft size={16} />
          </button>
          <button type="button" className="btn btn-secondary" onClick={goToday} style={{ fontSize: '13px', padding: '6px 12px' }}>
            Today
          </button>
          <button type="button" className="btn btn-secondary btn-icon" onClick={nextWeek} title="Next Week">
            <ChevronRight size={16} />
          </button>
          <span style={{ fontWeight: 600, fontSize: '14px', marginLeft: '6px' }}>
            {weekDays[0].displayDate} — {weekDays[6].displayDate}, {weekDays[0].date.getFullYear()}
          </span>
        </div>
      </div>

      <div className="week-grid">
        {weekDays.map((day) => {
          const daySessions = sessionsByDate[day.dateString] || [];
          // Sort by start time
          daySessions.sort((a, b) => a.start_time.localeCompare(b.start_time));

          return (
            <div 
              key={day.dateString} 
              className={`week-day-col ${day.isToday ? 'is-today' : ''}`}
            >
              <div className="week-day-header">
                <div className="week-day-name">{day.dayName}</div>
                <div className="week-day-date">{day.displayDate.split(' ')[1]}</div>
              </div>

              <div className="week-sessions-list">
                {daySessions.length === 0 ? (
                  <div style={{ 
                    padding: '24px 8px', 
                    textAlign: 'center', 
                    color: 'var(--text-muted)', 
                    fontSize: '11px',
                    fontStyle: 'italic'
                  }}>
                    No study planned
                  </div>
                ) : (
                  daySessions.map((session, sIdx) => {
                    const color = session.subject_color || '#54552d';
                    return (
                      <div 
                        key={session.id || `${session.task_id}-${sIdx}`}
                        className="session-chip"
                        style={{ borderLeftColor: color }}
                      >
                        <div className="session-time">
                          <Clock size={11} />
                          <span>{session.start_time} - {session.end_time}</span>
                          <span style={{ marginLeft: 'auto', fontWeight: 700 }}>{session.duration_mins}m</span>
                        </div>
                        <div className="session-title" title={session.task_title}>
                          {session.task_title}
                        </div>
                        <div className="session-subject">
                          <span className="color-dot" style={{ backgroundColor: color, width: '7px', height: '7px' }}></span>
                          <span style={{ color: 'var(--text-secondary)' }}>{session.subject_name}</span>
                          {session.total_parts > 1 && (
                            <span className="session-part-badge">
                              {session.part_number}/{session.total_parts}
                            </span>
                          )}
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
    </div>
  );
}
