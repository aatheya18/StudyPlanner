import React from 'react';
import { ChevronLeft, ChevronRight, Clock } from 'lucide-react';

export default function MonthView({ sessions, currentDate, onDateChange }) {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); // 0-indexed

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);

  // Month title
  const monthName = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  // Navigation
  const prevMonth = () => {
    onDateChange(new Date(year, month - 1, 1));
  };

  const nextMonth = () => {
    onDateChange(new Date(year, month + 1, 1));
  };

  const goToday = () => {
    onDateChange(new Date());
  };

  // Day of week for 1st day of month (0 = Sun, 1 = Mon, ..., 6 = Sat)
  // We want Monday = 0, ..., Sunday = 6
  let startingDay = firstDayOfMonth.getDay() - 1;
  if (startingDay === -1) startingDay = 6;

  const totalDays = lastDayOfMonth.getDate();

  // Group sessions by YYYY-MM-DD
  const sessionsByDate = {};
  sessions.forEach((s) => {
    if (!sessionsByDate[s.session_date]) {
      sessionsByDate[s.session_date] = [];
    }
    sessionsByDate[s.session_date].push(s);
  });

  // Build calendar matrix (42 cells: 6 weeks x 7 days)
  const calendarCells = [];

  // Previous month trailing days
  const prevMonthLastDate = new Date(year, month, 0).getDate();
  for (let i = startingDay - 1; i >= 0; i--) {
    const d = prevMonthLastDate - i;
    const dateObj = new Date(year, month - 1, d);
    const dateString = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    calendarCells.push({
      dateNumber: d,
      dateString,
      isCurrentMonth: false,
      isToday: false
    });
  }

  // Current month days
  const todayStr = new Date().toISOString().split('T')[0];
  for (let d = 1; d <= totalDays; d++) {
    const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    calendarCells.push({
      dateNumber: d,
      dateString,
      isCurrentMonth: true,
      isToday: dateString === todayStr
    });
  }

  // Next month leading days to complete the 6 rows (or 5 rows)
  const remainingCells = (7 - (calendarCells.length % 7)) % 7;
  for (let d = 1; d <= remainingCells; d++) {
    const dateObj = new Date(year, month + 1, d);
    const dateString = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    calendarCells.push({
      dateNumber: d,
      dateString,
      isCurrentMonth: false,
      isToday: false
    });
  }

  const weekHeaders = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="month-view-wrapper">
      <div className="calendar-controls">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button type="button" className="btn btn-secondary btn-icon" onClick={prevMonth} title="Previous Month">
            <ChevronLeft size={16} />
          </button>
          <button type="button" className="btn btn-secondary" onClick={goToday} style={{ fontSize: '13px', padding: '6px 12px' }}>
            Today
          </button>
          <button type="button" className="btn btn-secondary btn-icon" onClick={nextMonth} title="Next Month">
            <ChevronRight size={16} />
          </button>
          <span style={{ fontWeight: 600, fontSize: '14px', marginLeft: '6px' }}>
            {monthName}
          </span>
        </div>
      </div>

      <div className="month-grid">
        {weekHeaders.map((h) => (
          <div key={h} className="month-weekday-header">
            {h}
          </div>
        ))}

        {calendarCells.map((cell, idx) => {
          const daySessions = sessionsByDate[cell.dateString] || [];
          const totalMins = daySessions.reduce((acc, s) => acc + s.duration_mins, 0);

          return (
            <div 
              key={`${cell.dateString}-${idx}`}
              className={`month-day-cell ${!cell.isCurrentMonth ? 'other-month' : ''} ${cell.isToday ? 'is-today' : ''}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="month-day-number">{cell.dateNumber}</span>
                {totalMins > 0 && (
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    {totalMins}m
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginTop: '2px' }}>
                {daySessions.slice(0, 3).map((session, sIdx) => {
                  const color = session.subject_color || '#54552d';
                  return (
                    <div 
                      key={session.id || sIdx}
                      className="month-badge"
                      style={{ 
                        borderLeftColor: color, 
                        backgroundColor: `${color}15`,
                        color: 'var(--text-primary)'
                      }}
                      title={`${session.start_time} - ${session.end_time}: ${session.task_title} (${session.subject_name})`}
                    >
                      <span style={{ fontWeight: 700, marginRight: '3px' }}>{session.start_time}</span>
                      <span>{session.task_title}</span>
                    </div>
                  );
                })}

                {daySessions.length > 3 && (
                  <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 600, textAlign: 'center' }}>
                    +{daySessions.length - 3} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
