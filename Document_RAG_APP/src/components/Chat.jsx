import { useEffect, useRef, useState } from 'react'
import { sendChat } from '../api.js'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [waiting, setWaiting] = useState(false)
  const bottom = useRef(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waiting])

  async function send(e) {
    e.preventDefault()
    const question = text.trim()
    if (!question || waiting) return
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

  return (
    <section className="chat">
      <div className="messages">
        {messages.length === 0 && <p className="hint">Ask a question about your document.</p>}
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
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Ask a question…"
          autoFocus
        />
        <button type="submit" className="send" disabled={waiting || !text.trim()} aria-label="Send">
          ➤
        </button>
      </form>
    </section>
  )
}
