import { useState } from 'react'
import { uploadPdf } from '../api.js'

const MAX_BYTES = 40 * 1024 * 1024

// Shared by the first upload screen and the drop box on the agent screen.
export default function usePdfUpload(onDone) {
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
      await onDone()
    } catch (e) {
      setError(
        e.message === 'server'
          ? 'cannot reach the server, please try again'
          : 'this document is invalid'
      )
    } finally {
      setBusy(false)
    }
  }

  return { busy, error, handleFile }
}
