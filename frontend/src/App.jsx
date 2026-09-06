import { BrowserRouter, Routes, Route } from 'react-router-dom'
import React from 'react'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<h1>Vaani Kavach - Voice Protection</h1>} />
        <Route path="/verify" element={<div>Verify Voice</div>} />
        <Route path="/history" element={<div>History</div>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
