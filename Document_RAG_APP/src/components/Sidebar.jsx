import logo from '../assets/logo-small.png'

export default function Sidebar({ open, onNewChat }) {
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
        <p className="history-empty">No conversations yet.</p>
      </div>
    </aside>
  )
}
