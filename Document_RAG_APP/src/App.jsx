import { useEffect, useState } from 'react'
import UploadScreen from './components/UploadScreen.jsx'
import Sidebar from './components/Sidebar.jsx'
import DocumentPanel from './components/DocumentPanel.jsx'
import Chat from './components/Chat.jsx'
import ConfirmDialog from './components/ConfirmDialog.jsx'
import { getDocument, listSessions, getSession, deleteSession } from './api.js'

export default function App() {
  const [loading, setLoading] = useState(true)
  const [serverError, setServerError] = useState(false)
  const [document, setDocument] = useState(null)
  const [onAgentScreen, setOnAgentScreen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const [sessions, setSessions] = useState([])
  const [active, setActive] = useState(null) // an opened conversation, or null for a new chat
  const [activeId, setActiveId] = useState(null) // highlighted in the sidebar
  const [chatNo, setChatNo] = useState(0) // changing it starts the chat view fresh
  const [toDelete, setToDelete] = useState(null)

  async function refreshSessions() {
    try {
      setSessions(await listSessions())
    } catch {
      /* the list stays as it was */
    }
  }

  async function refresh() {
    try {
      const d = await getDocument()
      setDocument(d.exists ? d : null)
      setServerError(false)
      if (d.exists) setOnAgentScreen(true)
      await refreshSessions()
    } catch {
      setServerError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  function newChat() {
    setActive(null)
    setActiveId(null)
    setChatNo((n) => n + 1)
  }

  async function documentChanged() {
    await refresh()
    newChat()
  }

  async function openSession(id) {
    try {
      const s = await getSession(id)
      setActive(s)
      setActiveId(id)
      setChatNo((n) => n + 1)
    } catch {
      await refreshSessions()
    }
  }

  async function confirmDelete() {
    const s = toDelete
    setToDelete(null)
    try {
      await deleteSession(s.id)
    } catch {
      /* the refresh below shows the real state */
    } finally {
      await refreshSessions()
      if (s.id === activeId) newChat()
    }
  }

  if (loading) return <main className="center" />
  if (serverError)
    return (
      <main className="center">
        <p className="error">cannot reach the server, please try again</p>
        <button className="primary" onClick={refresh}>Retry</button>
      </main>
    )
  if (!onAgentScreen) return <UploadScreen onReady={documentChanged} />

  return (
    <div className="agent-screen">
      <Sidebar
        open={sidebarOpen}
        sessions={sessions}
        activeId={activeId}
        onNewChat={newChat}
        onSelect={openSession}
        onDelete={setToDelete}
      />
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
          <div className="topbar-text">
            <div className="topbar-title">{active?.title || 'New chat'}</div>
            <div className="topbar-sub">{document ? '1 document loaded' : 'No document'}</div>
          </div>
        </div>
        <div className="content">
          <DocumentPanel document={document} onChanged={documentChanged} />
          <Chat
            key={`${document?.document_id ?? 'none'}-${chatNo}`}
            initialMessages={active?.messages ?? []}
            initialSessionId={active?.id ?? null}
            readOnly={Boolean(active?.read_only)}
            noDocument={!document}
            onSessionSaved={(id) => {
              setActiveId(id)
              refreshSessions()
            }}
          />
        </div>
      </div>
      {toDelete && (
        <ConfirmDialog
          message="Delete this conversation? It will disappear from your history."
          onYes={confirmDelete}
          onNo={() => setToDelete(null)}
        />
      )}
    </div>
  )
}
