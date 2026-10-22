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

export async function sendChat(question, history) {
  let res
  try {
    res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, history: history.slice(-6) }),
    })
  } catch {
    throw new Error('the server could not be reached, please try again')
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || 'something went wrong, please try again')
  return data.answer
}
