import { FiMessageSquare, FiPlus, FiDatabase, FiZap, FiClock } from 'react-icons/fi';
import './Sidebar.css';

function Sidebar({ sessionsList, currentSessionId, onSelectSession, onNewSession, activeFile }) {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-logo">✦</div>
        <span className="sidebar-brand-name">DataPilot</span>
      </div>

      {/* New Analysis CTA */}
      <button className="new-chat-btn" onClick={onNewSession} id="new-analysis-btn">
        <span className="btn-icon">⊕</span>
        New Analysis
      </button>

      {/* Session History */}
      <div className="sidebar-section-label">
        <FiClock className="label-icon" />
        Session History
      </div>

      <div className="sessions-scroll">
        {sessionsList.length === 0 ? (
          <div className="sessions-empty">
            <div className="empty-icon">🛸</div>
            <p>No sessions yet.<br />Upload a CSV to begin.</p>
          </div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {sessionsList.map((session, idx) => (
              <li
                key={session.id}
                className={`session-item ${session.id === currentSessionId ? 'active' : ''}`}
                onClick={() => onSelectSession(session.id)}
                style={{ animationDelay: `${idx * 0.04}s` }}
              >
                <div className="session-icon">
                  <FiMessageSquare size={11} />
                </div>
                <div className="session-info">
                  <span className="session-title">{session.title || 'Untitled Analysis'}</span>
                  <span className="session-date">
                    {new Date(session.updated_at).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric', year: '2-digit'
                    })}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="sidebar-footer-info">
          <span className="pulse-dot" />
          <span>AI Engine Active</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
