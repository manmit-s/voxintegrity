import React from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import StitchScreen from './pages/StitchScreen'
import './stitch-host.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<StitchScreen screen="capture" />} />
        <Route path="/verify" element={<StitchScreen screen="capture" />} />
        <Route path="/telemetry" element={<StitchScreen screen="telemetry" />} />
        <Route path="/summary" element={<StitchScreen screen="summary" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
