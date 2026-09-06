import React, { useRef, useState } from 'react'

export default function VoiceRecorder({ onCapture }) {
  const inputRef = useRef(null)
  const [selected, setSelected] = useState(null)
  const handleUpload = (event) => {
    const nextFile = event.target.files?.[0]
    if (nextFile) setSelected(nextFile)
  }
  return <div className="recorder"><input ref={inputRef} className="visually-hidden" type="file" accept="audio/*" onChange={handleUpload} /><button className="primary-button capture-button" onClick={() => selected ? onCapture(selected) : inputRef.current?.click()}>{selected ? 'START ANALYSIS' : 'SELECT AUDIO SAMPLE'} <span>{selected ? '→' : '+'}</span></button>{selected && <button className="file-chip" onClick={() => inputRef.current?.click()}>{selected.name} <span>{(selected.size / 1024 / 1024).toFixed(2)} MB</span></button>}</div>
}
