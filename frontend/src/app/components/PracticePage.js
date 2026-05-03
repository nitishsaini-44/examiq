'use client';
import { useState } from 'react';

export default function PracticePage({ data }) {
  const [selectedTopic, setSelectedTopic] = useState('all');
  const [expandedQ, setExpandedQ] = useState(null);

  if (!data?.practice_questions?.length) {
    return <div className="loading-overlay"><div className="loading-text">No practice questions. Run analysis first.</div></div>;
  }

  const questions = data.practice_questions;
  const topics = ['all', ...new Set(questions.map(q => q.topic))];
  const filtered = selectedTopic === 'all' ? questions : questions.filter(q => q.topic === selectedTopic);

  const diffColors = { Easy: 'badge-easy', Medium: 'badge-medium', Hard: 'badge-hard' };

  return (
    <div className="animate-fade">
      <div className="page-header">
        <h1 className="page-title">📝 Practice Questions</h1>
        <p className="page-subtitle">{questions.length} exam-style questions generated from analysis</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-label">Total Questions</div><div className="kpi-value">{questions.length}</div></div>
        <div className="kpi-card"><div className="kpi-label">Topics Covered</div><div className="kpi-value">{topics.length - 1}</div></div>
        <div className="kpi-card"><div className="kpi-label">Showing</div><div className="kpi-value">{filtered.length}</div></div>
      </div>

      {/* Topic Filter */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
        {topics.map(t => (
          <button key={t} className={`tab ${selectedTopic === t ? 'active' : ''}`} onClick={() => setSelectedTopic(t)} style={{ borderRadius: 20, padding: '8px 16px' }}>
            {t === 'all' ? '📋 All Topics' : t}
          </button>
        ))}
      </div>

      {/* Questions */}
      <div>
        {filtered.map((q, i) => (
          <div key={i} className="question-card animate-slide" style={{ animationDelay: `${i * 0.05}s` }}>
            <div className="question-header">
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontWeight: 700, color: 'var(--accent-blue)', fontSize: 14 }}>Q{i + 1}</span>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{q.topic}</span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span className={`badge ${diffColors[q.difficulty] || 'badge-medium'}`}>{q.difficulty}</span>
                <span className="badge badge-medium">{q.marks}M</span>
              </div>
            </div>
            <div className="question-text">{q.question_text}</div>
            <div className="question-meta">
              <span className="badge badge-low">{q.question_type}</span>
              {q.hint && (
                <button onClick={() => setExpandedQ(expandedQ === i ? null : i)} style={{ background: 'none', border: 'none', color: 'var(--accent-teal)', cursor: 'pointer', fontSize: 12 }}>
                  {expandedQ === i ? '🔽 Hide Hint' : '💡 Show Hint'}
                </button>
              )}
            </div>
            {expandedQ === i && q.hint && (
              <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(20,184,166,0.08)', borderRadius: 8, fontSize: 13, color: 'var(--accent-teal)', borderLeft: '3px solid var(--accent-teal)' }}>
                💡 {q.hint}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
