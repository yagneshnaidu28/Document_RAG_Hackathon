import { useEffect, useRef, useState } from 'react'
import { sendChat } from '../api.js'

// initialMessages / initialSessionId: set when an old conversation is opened.
// noDocument: no PDF is loaded. readOnly: the conversation belongs to a PDF
// that was replaced or deleted. Either way the input is disabled.
export default function Chat({
  initialMessages = [],
  initialSessionId = null,
  noDocument,
  readOnly,
  onSessionSaved,
}) {
  const [messages, setMessages] = useState(initialMessages)
  const [sessionId, setSessionId] = useState(initialSessionId)
  const [text, setText] = useState('')
  const [waiting, setWaiting] = useState(false)
  const bottom = useRef(null)
  const disabled = noDocument || readOnly

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waiting])

  async function send(e) {
    e?.preventDefault()
    const question = text.trim()
    if (!question || waiting || disabled) return
    setMessages((m) => [...m.filter((x) => !x.error), { role: 'user', text: question }])
    setText('')
    setWaiting(true)
    try {
      const { answer, session_id } = await sendChat(question, sessionId)
      setSessionId(session_id)
      setMessages((m) => [...m, { role: 'assistant', text: answer }])
      onSessionSaved?.(session_id)
    } catch (err) {
      if (err.sessionId) {
        setSessionId(err.sessionId)
        onSessionSaved?.(err.sessionId)
      }
      setMessages((m) => [...m, { role: 'assistant', text: err.message, error: true }])
    } finally {
      setWaiting(false)
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const empty = messages.length === 0 && !waiting
  const placeholder = noDocument
    ? 'No document to search'
    : readOnly
      ? 'Read-only: its document was replaced or deleted'
      : 'Ask a question about your document…'

  return (
    <section className="chat">
      <div className="messages">
        {empty && (
          <div className="empty-state">
            <h2>{noDocument ? 'No document to search' : 'Ask anything about your document'}</h2>
            {noDocument && <p className="hint">Upload a PDF above to start asking questions.</p>}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}${m.error ? ' error-bubble' : ''}`}>
            {m.text}
          </div>
        ))}
        {waiting && (
          <div className="bubble assistant">
            <div className="dots small"><span /><span /><span /></div>
          </div>
        )}
        {readOnly && messages.length > 0 && (
          <p className="readonly-note">
            This conversation is read-only because its document was replaced or deleted.
            Start a new chat to ask about the current document.
          </p>
        )}
        <div ref={bottom} />
      </div>
      <form className="input-bar" onSubmit={send}>
        <textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          autoFocus
        />
        <button
          type="submit"
          className="send"
          disabled={disabled || waiting || !text.trim()}
          aria-label="Send"
        >
          →
        </button>
      </form>
      <p className="input-hint">Enter to send · Shift + Enter for a new line</p>
    </section>
  )
}
