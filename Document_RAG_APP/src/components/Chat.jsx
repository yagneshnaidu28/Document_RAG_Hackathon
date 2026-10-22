import { useEffect, useRef, useState } from 'react'
import { sendChat } from '../api.js'

export default function Chat({ disabled }) {
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [waiting, setWaiting] = useState(false)
  const bottom = useRef(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waiting])

  async function send(e) {
    e?.preventDefault()
    const question = text.trim()
    if (!question || waiting || disabled) return
    const history = messages.filter((m) => !m.error)
    setMessages([...history, { role: 'user', text: question }])
    setText('')
    setWaiting(true)
    try {
      const answer = await sendChat(question, history)
      setMessages((m) => [...m, { role: 'assistant', text: answer }])
    } catch (err) {
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

  return (
    <section className="chat">
      <div className="messages">
        {empty && (
          <div className="empty-state">
            <h2>{disabled ? 'No document to search' : 'Ask anything about your document'}</h2>
            {disabled && <p className="hint">Upload a PDF above to start asking questions.</p>}
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
        <div ref={bottom} />
      </div>
      <form className="input-bar" onSubmit={send}>
        <textarea
          rows={1}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={disabled ? 'No document to search' : 'Ask a question about your document…'}
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
