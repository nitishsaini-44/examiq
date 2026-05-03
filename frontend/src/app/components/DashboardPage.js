'use client';
import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend } from 'recharts';

const COLORS = ['#6366f1', '#a855f7', '#14b8a6', '#f59e0b', '#f43f5e', '#22c55e', '#3b82f6', '#ec4899'];
const HEAT_COLORS = ['#1e1b4b', '#312e81', '#4338ca', '#6366f1', '#818cf8', '#a5b4fc'];

function getHeatColor(value, max) {
  if (value === 0) return 'rgba(255,255,255,0.03)';
  const idx = Math.min(Math.floor((value / Math.max(max, 1)) * (HEAT_COLORS.length - 1)), HEAT_COLORS.length - 1);
  return HEAT_COLORS[idx];
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, padding: '10px 14px', fontSize: 13 }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

export default function DashboardPage({ data }) {
  const [activeTab, setActiveTab] = useState('overview');

  if (!data) {
    return <div className="loading-overlay"><div className="loading-text">No analysis data. Upload papers first.</div></div>;
  }

  const { topic_rankings = [], syllabus_coverage = {}, predictions = {}, dashboard_data = {} } = data;
  const { frequency_chart = {}, heatmap = {}, difficulty_pie = {}, total_questions = 0, total_topics = 0, total_years = 0, avg_importance = 0, coverage_percentage = 0 } = dashboard_data;

  const freqData = (frequency_chart.labels || []).map((l, i) => ({ name: l.length > 20 ? l.slice(0, 20) + '…' : l, value: frequency_chart.values?.[i] || 0 }));
  const pieData = [
    { name: 'Easy', value: difficulty_pie.easy || 0 },
    { name: 'Medium', value: difficulty_pie.medium || 0 },
    { name: 'Hard', value: difficulty_pie.hard || 0 },
  ].filter(d => d.value > 0);
  const pieColors = ['#22c55e', '#f59e0b', '#f43f5e'];

  const heatMax = Math.max(...(heatmap.matrix || []).flat(), 1);

  return (
    <div className="animate-fade">
      <div className="page-header">
        <h1 className="page-title">📊 Analytics Dashboard</h1>
        <p className="page-subtitle">AI-powered insights from {total_questions} questions across {total_years} years</p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-label">Total Questions</div><div className="kpi-value">{total_questions}</div></div>
        <div className="kpi-card"><div className="kpi-label">Topics Found</div><div className="kpi-value">{total_topics}</div></div>
        <div className="kpi-card"><div className="kpi-label">Years Analyzed</div><div className="kpi-value">{total_years}</div></div>
        <div className="kpi-card"><div className="kpi-label">Avg Importance</div><div className="kpi-value">{avg_importance.toFixed(0)}</div></div>
        <div className="kpi-card"><div className="kpi-label">Syllabus Coverage</div><div className="kpi-value">{coverage_percentage.toFixed(0)}%</div></div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {['overview', 'topics', 'predictions', 'coverage'].map(t => (
          <button key={t} className={`tab ${activeTab === t ? 'active' : ''}`} onClick={() => setActiveTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div>
          <div className="grid-2">
            {/* Frequency Bar Chart */}
            <div className="card">
              <div className="card-header"><div className="card-title">📊 Topic Frequency</div></div>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={freqData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <XAxis type="number" stroke="#64748b" fontSize={12} />
                  <YAxis type="category" dataKey="name" width={130} stroke="#64748b" fontSize={11} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Frequency" radius={[0, 6, 6, 0]}>
                    {freqData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Difficulty Pie + Insights */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div className="card">
                <div className="card-header"><div className="card-title">🎯 Difficulty Distribution</div></div>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false} fontSize={12}>
                      {pieData.map((_, i) => <Cell key={i} fill={pieColors[i]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="card">
                <div className="card-header"><div className="card-title">💡 Key Insights</div></div>
                {(predictions.key_insights || []).map((insight, i) => (
                  <div key={i} className="insight-item" style={{ animationDelay: `${i * 0.1}s` }}>{insight}</div>
                ))}
                {(!predictions.key_insights || predictions.key_insights.length === 0) && (
                  <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>No insights generated yet.</div>
                )}
              </div>
            </div>
          </div>

          {/* Heatmap */}
          {heatmap.topics?.length > 0 && (
            <div className="card" style={{ marginTop: 24 }}>
              <div className="card-header"><div className="card-title">🔥 Topic × Year Heatmap</div></div>
              <div style={{ overflowX: 'auto' }}>
                <div className="heatmap-grid">
                  <div className="heatmap-row">
                    <div className="heatmap-label" style={{ fontWeight: 600, color: 'var(--text-muted)' }}>Topic</div>
                    {(heatmap.years || []).map(y => (
                      <div key={y} className="heatmap-cell" style={{ background: 'transparent', fontSize: 11, color: 'var(--text-muted)', fontWeight: 600 }}>{y}</div>
                    ))}
                  </div>
                  {(heatmap.topics || []).map((topic, ti) => (
                    <div key={ti} className="heatmap-row">
                      <div className="heatmap-label" title={topic}>{topic}</div>
                      {(heatmap.matrix?.[ti] || []).map((val, yi) => (
                        <div key={yi} className="heatmap-cell" style={{ background: getHeatColor(val, heatMax), color: val > 0 ? '#fff' : 'var(--text-muted)' }} title={`${topic} - ${heatmap.years?.[yi]}: ${val} questions`}>
                          {val || ''}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'topics' && (
        <div className="card">
          <div className="card-header"><div className="card-title">🏆 Topic Rankings</div></div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead><tr><th>#</th><th>Topic</th><th>Frequency</th><th>Total Marks</th><th>Trend</th><th>Score</th><th>Priority</th></tr></thead>
              <tbody>
                {topic_rankings.map((t, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 700, color: 'var(--text-muted)' }}>{t.rank}</td>
                    <td style={{ fontWeight: 600 }}>{t.topic}</td>
                    <td>{t.frequency}</td>
                    <td>{t.total_marks}</td>
                    <td>{t.trend === 'increasing' ? '📈' : t.trend === 'decreasing' ? '📉' : '➡️'} {t.trend}</td>
                    <td><span style={{ fontWeight: 700, color: 'var(--accent-blue)' }}>{t.importance_score}</span></td>
                    <td><span className={`badge badge-${t.priority?.toLowerCase()}`}>{t.priority}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'predictions' && (
        <div>
          {/* Predicted Topics */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header"><div className="card-title">🔥 Predicted Next Exam Topics</div></div>
            {(predictions.predicted_topics || []).length > 0 ? predictions.predicted_topics.map((p, i) => (
              <div key={i} className="alert-card alert-fire">
                <div><strong>{p.topic}</strong><div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{p.reason} • Score: {p.importance}</div></div>
              </div>
            )) : <div style={{ color: 'var(--text-muted)', fontSize: 14 }}>No predictions available.</div>}
          </div>

          <div className="grid-2">
            {/* 80/20 Strategy */}
            <div className="card">
              <div className="card-header"><div className="card-title">🎯 80/20 Focus List</div></div>
              {(predictions.pareto_topics || []).map((p, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border-glass)' }}>
                  <span style={{ fontWeight: 500, fontSize: 14 }}>{p.topic}</span>
                  <span className="badge badge-medium">{p.cumulative_pct}%</span>
                </div>
              ))}
            </div>

            {/* Low ROI */}
            <div className="card">
              <div className="card-header"><div className="card-title">📉 Low ROI Topics</div></div>
              {(predictions.low_roi_topics || []).length > 0 ? predictions.low_roi_topics.map((p, i) => (
                <div key={i} className="alert-card alert-info">
                  <div><strong>{p.topic}</strong><div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{p.reason}</div></div>
                </div>
              )) : <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>All topics have reasonable ROI.</div>}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'coverage' && (
        <div className="card">
          <div className="card-header"><div className="card-title">📚 Syllabus Coverage</div></div>
          <div className="progress-bar" style={{ marginBottom: 24, height: 12 }}>
            <div className="progress-fill" style={{ width: `${coverage_percentage}%` }} />
          </div>
          <div style={{ textAlign: 'center', marginBottom: 24, fontSize: 14, color: 'var(--text-secondary)' }}>{coverage_percentage.toFixed(1)}% of syllabus covered in past papers</div>
          <div className="coverage-section"><div className="coverage-title">✅ Fully Covered</div><div className="coverage-list">{(syllabus_coverage.fully_covered || []).map((t, i) => <span key={i} className="coverage-tag tag-covered">{t}</span>)}</div></div>
          <div className="coverage-section"><div className="coverage-title">⚠️ Partially Covered</div><div className="coverage-list">{(syllabus_coverage.partially_covered || []).map((t, i) => <span key={i} className="coverage-tag tag-partial">{t}</span>)}</div></div>
          <div className="coverage-section"><div className="coverage-title">❌ Never Asked</div><div className="coverage-list">{(syllabus_coverage.never_asked || []).map((t, i) => <span key={i} className="coverage-tag tag-uncovered">{t}</span>)}</div></div>
        </div>
      )}
    </div>
  );
}
