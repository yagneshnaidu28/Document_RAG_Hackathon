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
