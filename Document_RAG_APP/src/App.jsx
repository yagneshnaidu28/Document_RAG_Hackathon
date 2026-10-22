import { useState } from 'react'
import UploadScreen from './components/UploadScreen.jsx'
import Chat from './components/Chat.jsx'

export default function App() {
  const [ready, setReady] = useState(false)

  if (!ready) return <UploadScreen onReady={() => setReady(true)} />
  return (
    <main className="agent">
      <p className="ready">Document ready.</p>
      <Chat />
    </main>
  )
}
