'use client';
import { useState } from 'react';

const TYPE_COLORS = { study: 'var(--accent-blue)', revision: 'var(--accent-purple)', practice: 'var(--accent-teal)', buffer: 'var(--text-muted)' };
const TYPE_ICONS = { study: '📖', revision: '🔄', practice: '✍️', buffer: '☕' };

export default function PlannerPage({ data }) {
  const [view, setView] = useState('timeline');

  if (!data?.study_plan) {
    return <div className="loading-overlay"><div className="loading-text">No study plan. Run analysis first.</div></div>;
  }

  const plan = data.study_plan;
  const sessions = plan.sessions || [];

  // Group sessions by day
  const dayMap = {};
  sessions.forEach(s => {
    if (!dayMap[s.day]) dayMap[s.day] = [];
    dayMap[s.day].push(s);
  });
  const days = Object.keys(dayMap).sort((a, b) => +a - +b);

  // Stats
  const studyHrs = sessions.filter(s => s.session_type === 'study').reduce((sum, s) => sum + s.duration_hours, 0);
  const revHrs = sessions.filter(s => s.session_type === 'revision').reduce((sum, s) => sum + s.duration_hours, 0);
  const pracHrs = sessions.filter(s => s.session_type === 'practice').reduce((sum, s) => sum + s.duration_hours, 0);

  return (
    <div className="animate-fade">
      <div className="page-header">
        <h1 className="page-title">📅 Smart Study Planner</h1>
        <p className="page-subtitle">{plan.total_days}-day plan • {plan.total_hours} total hours</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-label">Total Days</div><div className="kpi-value">{plan.total_days}</div></div>
        <div className="kpi-card"><div className="kpi-label">Study Hours</div><div className="kpi-value">{studyHrs.toFixed(0)}</div></div>
        <div className="kpi-card"><div className="kpi-label">Revision Hours</div><div className="kpi-value">{revHrs.toFixed(0)}</div></div>
        <div className="kpi-card"><div className="kpi-label">Practice Hours</div><div className="kpi-value">{pracHrs.toFixed(0)}</div></div>
      </div>

      <div className="tabs" style={{ marginBottom: 24 }}>
        <button className={`tab ${view === 'timeline' ? 'active' : ''}`} onClick={() => setView('timeline')}>Timeline</button>
        <button className={`tab ${view === 'calendar' ? 'active' : ''}`} onClick={() => setView('calendar')}>Day Cards</button>
      </div>

      {view === 'timeline' && (
        <div className="card">
          <div className="timeline">
            {sessions.map((s, i) => (
              <div key={i} className="timeline-item" style={{ animationDelay: `${i * 0.03}s`, borderLeftColor: TYPE_COLORS[s.session_type] || 'var(--accent-blue)' }}>
                <div className="timeline-day" style={{ color: TYPE_COLORS[s.session_type] }}>
                  <div>Day {s.day}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{s.date}</div>
                </div>
                <div className="timeline-content">
                  <div className="timeline-topic">{TYPE_ICONS[s.session_type]} {s.topic}</div>
                  <div className="timeline-meta">
                    <span>⏱️ {s.duration_hours}h</span>
                    <span className={`badge badge-${s.priority?.toLowerCase()}`}>{s.priority}</span>
                    <span style={{ textTransform: 'capitalize', color: TYPE_COLORS[s.session_type] }}>{s.session_type}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {view === 'calendar' && (
        <div className="grid-auto">
          {days.map(day => (
            <div key={day} className="card">
              <div className="card-header">
                <div className="card-title">📆 Day {day}</div>
                <span className="card-subtitle">{dayMap[day][0]?.date}</span>
              </div>
              {dayMap[day].map((s, i) => (
                <div key={i} style={{ padding: '10px 12px', background: 'var(--bg-glass)', borderRadius: 8, marginBottom: 8, borderLeft: `3px solid ${TYPE_COLORS[s.session_type]}` }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{TYPE_ICONS[s.session_type]} {s.topic}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 12 }}>
                    <span>⏱️ {s.duration_hours}h</span>
                    <span style={{ textTransform: 'capitalize' }}>{s.session_type}</span>
                  </div>
                </div>
              ))}
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>
                Total: {dayMap[day].reduce((sum, s) => sum + s.duration_hours, 0).toFixed(1)}h
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
