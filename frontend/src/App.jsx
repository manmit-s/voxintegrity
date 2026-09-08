import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import StitchScreen from './pages/StitchScreen'
import CaptureScreen from './pages/CaptureScreen'
import TelemetryScreen from './pages/TelemetryScreen'
import SummaryScreen from './pages/SummaryScreen'
import { useVoiceSession } from './hooks/useVoiceSession'

function VoiceConsole() {
  const session = useVoiceSession()
  if (session.phase === 'summary') return <SummaryScreen session={session} />
  if (session.phase === 'live' || session.phase === 'connecting') return <TelemetryScreen session={session} />
  return <CaptureScreen session={session} />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* The mockup design, wired to the live inference pipeline. */}
        <Route path="/" element={<VoiceConsole />} />
        <Route path="/verify" element={<VoiceConsole />} />
        <Route path="/telemetry" element={<VoiceConsole />} />
        <Route path="/summary" element={<VoiceConsole />} />
        {/* Static design mockups kept for reference. */}
        <Route path="/mock/:screen" element={<StitchScreen screen="capture" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
