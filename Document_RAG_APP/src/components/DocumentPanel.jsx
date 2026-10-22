import { useState } from 'react'
import usePdfUpload from '../hooks/usePdfUpload.js'
import Dropzone from './Dropzone.jsx'
import ConfirmDialog from './ConfirmDialog.jsx'
import { deleteDocument } from '../api.js'
import { formatTime } from '../format.js'

export default function DocumentPanel({ document, onChanged }) {
  const { busy, error, handleFile } = usePdfUpload(onChanged)
  const [confirming, setConfirming] = useState(false)

  async function remove() {
    setConfirming(false)
    try {
      await deleteDocument()
    } catch {
      /* the refresh below shows the real state */
    } finally {
      await onChanged()
    }
  }

  return (
    <section className="doc-panel">
      <Dropzone busy={busy} error={error} onFile={handleFile} compact />
      {document && !busy && (
        <div className="pdf-row">
          <span className="pdf-badge" aria-hidden="true">PDF</span>
          <div className="pdf-info">
            <div className="pdf-name" title={document.filename}>{document.filename}</div>
            <div className="pdf-meta">
              {document.chunks != null && `${document.chunks} chunks · `}
              {formatTime(document.uploaded_at)}
            </div>
          </div>
          <button
            className="icon-btn"
            onClick={() => setConfirming(true)}
            aria-label="Delete document"
            title="Delete document"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 7h16M10 11v6m4-6v6M6 7l1 12h10l1-12M9 7V4h6v3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      )}
      {confirming && (
        <ConfirmDialog
          message="Delete this document? Questions cannot be asked until you upload another."
          onYes={remove}
          onNo={() => setConfirming(false)}
        />
      )}
    </section>
  )
}
