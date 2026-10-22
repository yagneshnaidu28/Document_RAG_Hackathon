import { useEffect, useState } from 'react'
import UploadScreen from './components/UploadScreen.jsx'
import Sidebar from './components/Sidebar.jsx'
import DocumentPanel from './components/DocumentPanel.jsx'
import Chat from './components/Chat.jsx'
import { getDocument } from './api.js'

export default function App() {
  const [loading, setLoading] = useState(true)
  const [serverError, setServerError] = useState(false)
  const [document, setDocument] = useState(null)
  const [onAgentScreen, setOnAgentScreen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chatNo, setChatNo] = useState(0)

  async function refresh() {
    try {
      const d = await getDocument()
      setDocument(d.exists ? d : null)
      setServerError(false)
      if (d.exists) setOnAgentScreen(true)
    } catch {
      setServerError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  if (loading) return <main className="center" />
  if (serverError)
    return (
      <main className="center">
        <p className="error">cannot reach the server, please try again</p>
        <button className="primary" onClick={refresh}>Retry</button>
      </main>
    )
  if (!onAgentScreen) return <UploadScreen onReady={refresh} />

  return (
    <div className="agent-screen">
      <Sidebar open={sidebarOpen} onNewChat={() => setChatNo((n) => n + 1)} />
      <div className="main">
        <div className="topbar">
          <button
            className="icon-btn"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 6h16M4 12h16M4 18h16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </button>
          <div>
            <div className="topbar-title">New chat</div>
            <div className="topbar-sub">{document ? '1 document loaded' : 'No document'}</div>
          </div>
        </div>
        <div className="content">
          <DocumentPanel document={document} onChanged={refresh} />
          {/* key: a new document or New chat starts a fresh conversation */}
          <Chat key={`${document?.document_id ?? 'none'}-${chatNo}`} disabled={!document} />
        </div>
      </div>
    </div>
  )
}
