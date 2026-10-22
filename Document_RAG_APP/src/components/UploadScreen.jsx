import { useRef, useState } from 'react'
import { uploadPdf } from '../api.js'

const MAX_BYTES = 40 * 1024 * 1024

export default function UploadScreen({ onReady }) {
  const input = useRef(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleFile(file) {
    if (!file) return
    setError('')
    if (!file.name.toLowerCase().endsWith('.pdf') || file.size > MAX_BYTES) {
      setError('this document is invalid')
      return
    }
    setBusy(true)
    try {
      await uploadPdf(file)
      onReady()
    } catch (e) {
      setError(
        e.message === 'server'
          ? 'cannot reach the server, please try again'
          : 'this document is invalid'
      )
    } finally {
      setBusy(false)
      if (input.current) input.current.value = ''
    }
  }

  return (
    <main className="center">
      <h1>Document Agents</h1>
      <p className="hint">Upload a PDF (max 40 MB) and ask questions about it.</p>
      {busy ? (
        <div className="dots" aria-label="Processing">
          <span /><span /><span />
        </div>
      ) : (
        <button className="primary" onClick={() => input.current.click()}>
          Upload PDF
        </button>
      )}
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {error && <p className="error">{error}</p>}
    </main>
  )
}
