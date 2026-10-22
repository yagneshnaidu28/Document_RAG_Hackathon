import { useRef, useState } from 'react'

// Dashed upload box: click to choose a PDF, or drag and drop one.
export default function Dropzone({ busy, error, onFile, compact }) {
  const input = useRef(null)
  const [over, setOver] = useState(false)

  function choose(file) {
    onFile(file)
    if (input.current) input.current.value = ''
  }

  return (
    <div
      className={`dropzone${over ? ' over' : ''}${compact ? ' compact' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        if (!busy) choose(e.dataTransfer.files[0])
      }}
    >
      {busy ? (
        <div className="dots" aria-label="Processing">
          <span /><span /><span />
        </div>
      ) : (
        <>
          <svg className="drop-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="drop-main">
            <button type="button" className="link" onClick={() => input.current.click()}>
              Upload a file
            </button>{' '}
            or drag and drop
          </p>
          <p className="drop-sub">PDF only, up to 40 MB</p>
        </>
      )}
      <input
        ref={input}
        type="file"
        accept="application/pdf,.pdf"
        hidden
        onChange={(e) => choose(e.target.files[0])}
      />
      {error && <p className="error">{error}</p>}
    </div>
  )
}
