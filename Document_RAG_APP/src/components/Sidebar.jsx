import logo from '../assets/logo-small.png'
import { formatTime } from '../format.js'

export default function Sidebar({ open, sessions, activeId, onNewChat, onSelect, onDelete }) {
  return (
    <aside className={`sidebar${open ? '' : ' closed'}`}>
      <div className="brand">
        <img className="logo" src={logo} alt="Document Agents logo" />
        <h5 className="title">Document Agents</h5>
      </div>
      <div className="sidebar-body">
        <button className="new-chat" onClick={onNewChat}>
          <span aria-hidden="true">＋</span> New chat
        </button>
        <div className="history-head">HISTORY</div>
        {sessions.length === 0 && <p className="history-empty">No conversations yet.</p>}
        <ul className="history-list">
          {sessions.map((s) => (
            <li
              key={s.id}
              className={`history-item${s.id === activeId ? ' active' : ''}`}
              onClick={() => onSelect(s.id)}
            >
              <div className="history-text">
                <div className="history-title" title={s.title}>{s.title}</div>
                <div className="history-meta">
                  {formatTime(s.created_at)}
                  {s.read_only && <span className="badge"> · read-only</span>}
                </div>
              </div>
              <button
                className="icon-btn small"
                aria-label="Delete conversation"
                title="Delete conversation"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete(s)
                }}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 7h16M10 11v6m4-6v6M6 7l1 12h10l1-12M9 7V4h6v3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </aside>
  )
}
