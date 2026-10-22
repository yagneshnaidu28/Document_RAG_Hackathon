import usePdfUpload from '../hooks/usePdfUpload.js'
import Dropzone from './Dropzone.jsx'
import logo from '../assets/logo-small.png'

export default function UploadScreen({ onReady }) {
  const { busy, error, handleFile } = usePdfUpload(onReady)

  return (
    <main className="center">
      <img className="logo big" src={logo} alt="Document Agents logo" />
      <h1>Document Agents</h1>
      <p className="hint">Upload a PDF and ask questions about it.</p>
      <div className="upload-card">
        <Dropzone busy={busy} error={error} onFile={handleFile} />
      </div>
    </main>
  )
}
