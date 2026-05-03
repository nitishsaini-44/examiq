'use client';
export default function Sidebar({ activePage, onNavigate, isOpen, hasData }) {
  const links = [
    { id: 'upload', icon: '📄', label: 'Upload Papers' },
    { id: 'dashboard', icon: '📊', label: 'Dashboard' },
    { id: 'planner', icon: '📅', label: 'Study Planner' },
    { id: 'practice', icon: '📝', label: 'Practice' },
  ];

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">IQ</div>
        <span className="sidebar-logo-text">ExamIQ</span>
      </div>
      <nav className="sidebar-nav">
        {links.map(link => (
          <button
            key={link.id}
            className={`sidebar-link ${activePage === link.id ? 'active' : ''}`}
            onClick={() => onNavigate(link.id)}
            disabled={link.id !== 'upload' && !hasData && link.id !== 'upload'}
            style={link.id !== 'upload' && !hasData ? { opacity: 0.4 } : {}}
          >
            <span className="sidebar-link-icon">{link.icon}</span>
            {link.label}
          </button>
        ))}
      </nav>
      <div style={{ padding: '16px', borderTop: '1px solid var(--border-glass)', marginTop: 'auto' }}>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>AI Study Engine v1.0</div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Powered by ExamIQ</div>
      </div>
    </aside>
  );
}
