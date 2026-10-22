import { useState } from 'react'
import UploadScreen from './components/UploadScreen.jsx'

export default function App() {
  const [ready, setReady] = useState(false)

  if (!ready) return <UploadScreen onReady={() => setReady(true)} />
  return (
    <main className="center">
      <p className="ready">Document ready.</p>
    </main>
  )
}
