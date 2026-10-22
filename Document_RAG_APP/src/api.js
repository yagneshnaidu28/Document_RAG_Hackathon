export const API = 'http://localhost:8000'

export async function uploadPdf(file) {
  const form = new FormData()
  form.append('file', file)
  let res
  try {
    res = await fetch(`${API}/upload-pdf`, { method: 'POST', body: form })
  } catch {
    throw new Error('server')
  }
  if (!res.ok) throw new Error('invalid')
  return res.json()
}

// Returns { answer, session_id }. On failure throws an Error carrying the
// message to show, and session_id when the server already saved the question.
export async function sendChat(question, sessionId) {
  let res
  try {
    res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: sessionId || null }),
    })
  } catch {
    throw new Error('the server could not be reached, please try again')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(data.detail || 'something went wrong, please try again')
    err.sessionId = data.session_id
    throw err
  }
  return data
}

export async function listSessions() {
  const res = await fetch(`${API}/sessions`)
  if (!res.ok) throw new Error('server')
  return res.json()
}

export async function getSession(id) {
  const res = await fetch(`${API}/sessions/${encodeURIComponent(id)}`)
  if (!res.ok) throw new Error('not found')
  return res.json()
}

export async function deleteSession(id) {
  const res = await fetch(`${API}/sessions/${encodeURIComponent(id)}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('server')
}

export async function getDocument() {
  const res = await fetch(`${API}/document`)
  if (!res.ok) throw new Error('server')
  return res.json()
}

export async function deleteDocument() {
  const res = await fetch(`${API}/document`, { method: 'DELETE' })
  if (!res.ok) throw new Error('server')
}
