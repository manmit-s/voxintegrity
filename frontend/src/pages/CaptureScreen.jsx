import React, { useRef, useState } from 'react'

const BARS = 10

export default function CaptureScreen({ session }) {
  const fileInputRef = useRef(null)
  const [fileName, setFileName] = useState('')
  const [dragging, setDragging] = useState(false)
  const connecting = session.phase === 'connecting'

  const activeBars = Math.round(session.vuLevel * BARS)
  const dbfs = session.vuLevel > 0.001 ? `${Math.max(-60, Math.round(20 * Math.log10(session.vuLevel)))} dBFS` : 'STANDBY'

  const pickFile = () => fileInputRef.current?.click()
  const onDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files?.[0]
    if (file) { setFileName(file.name); session.analyzeFile(file) }
  }
  const onPick = (event) => {
    const file = event.target.files?.[0]
    if (file) { setFileName(file.name); session.analyzeFile(file) }
  }

  return (
    <div className="bg-surface-lowest text-on-surface font-mono antialiased min-h-screen flex flex-col justify-between selection:bg-accent selection:text-surface-lowest">
      <header className="w-full border-b border-outline-dim bg-surface-lowest/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.5)]"></div>
            <span className="font-heading font-bold text-lg tracking-tight text-on-surface">VAANI KAVACH</span>
            <span className="text-outline-dim text-xs">/</span>
            <span className="text-on-surface-variant text-xs hidden sm:inline tracking-normal font-sans">Voice-Cloning Detection</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-surface-low border border-outline-dim text-xs text-on-surface-variant">
              <span className="relative flex h-2 w-2 items-center justify-center"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-60"></span><span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-teal-400"></span></span>
              <span>{connecting ? 'Connecting' : 'System Ready'}</span>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col justify-center max-w-6xl mx-auto w-full px-6 py-10">
        <div className="mb-10 text-center max-w-2xl mx-auto flex flex-col gap-3">
          <h1 className="font-heading font-bold text-3xl sm:text-4xl text-on-surface tracking-tight">Signal Input &amp; Capture</h1>
          <p className="text-sm text-on-surface-variant leading-relaxed font-sans">
            Select an audio source to begin synthetic acoustic anomaly detection. Real-time inference uses a 2&nbsp;second analysis window with a 500&nbsp;ms stride.
          </p>
        </div>
        {session.error && (
          <div className="mb-8 mx-auto max-w-2xl bg-danger/10 border border-danger/40 text-danger text-xs font-mono px-4 py-3 rounded-lg text-center">{session.error}</div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
          <div className="bg-surface-low border border-outline-dim rounded-xl p-7 flex flex-col justify-between hover:border-surface-highest transition-colors">
            <div className="flex flex-col gap-6">
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Channel 01</span>
                <span className="text-xs text-on-surface-variant flex items-center gap-1.5">
                  <span className={`w-1.5 h-1.5 rounded-full ${connecting ? 'bg-accent animate-pulse' : 'bg-on-surface-variant'}`}></span>
                  <span>{connecting ? 'Connecting' : 'Idle'}</span>
                </span>
              </div>
              <div>
                <h2 className="font-heading font-semibold text-xl text-on-surface mb-2">Live Microphone</h2>
                <p className="text-xs text-on-surface-variant leading-relaxed font-sans">
                  Stream direct audio input via system mic. Audio chunks are analyzed continuously in 500&nbsp;ms strides.
                </p>
              </div>
              <div className="bg-surface rounded-lg p-4 border border-outline-dim flex flex-col gap-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-on-surface-variant text-[11px]">INPUT LEVEL</span>
                  <span className={`text-[11px] font-mono ${activeBars > 0 ? 'text-accent' : 'text-on-surface-variant'}`}>{dbfs}</span>
                </div>
                <div className="flex gap-1 h-3 items-center">
                  {Array.from({ length: BARS }).map((_, index) => (
                    <div key={index} className={`flex-1 h-full rounded-sm transition-colors ${index < activeBars ? 'bg-accent' : 'bg-surface-high'}`}></div>
                  ))}
                </div>
              </div>
            </div>
            <div className="pt-8">
              <button
                onClick={session.startMic}
                disabled={connecting}
                className="w-full bg-teal-500 hover:bg-teal-400 disabled:opacity-60 text-slate-950 font-semibold text-xs tracking-wider uppercase py-3.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-all cursor-pointer font-heading shadow-sm active:translate-y-px">
                <span className="material-symbols-outlined text-[18px]">mic</span>
                <span>{connecting ? 'Connecting…' : 'Arm Microphone'}</span>
              </button>
            </div>
          </div>
          <div className="bg-surface-low border border-outline-dim rounded-xl p-7 flex flex-col justify-between hover:border-surface-highest transition-colors">
            <div className="flex flex-col gap-6">
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold">Channel 02</span>
                <span className="text-xs text-on-surface-variant">Max 25 MB</span>
              </div>
              <div>
                <h2 className="font-heading font-semibold text-xl text-on-surface mb-2">Audio File Upload</h2>
                <p className="text-xs text-on-surface-variant leading-relaxed font-sans">
                  Inspect recorded voice samples for vocoder phase artifacts and clone residuals.
                </p>
              </div>
              <div
                onClick={pickFile}
                onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                className={`bg-surface rounded-lg p-6 border border-dashed flex flex-col items-center justify-center text-center cursor-pointer transition-colors group ${dragging ? 'border-accent' : 'border-outline-dim hover:border-teal-400/50'}`}>
                <div className="w-10 h-10 rounded-full bg-surface-high flex items-center justify-center text-on-surface-variant group-hover:text-teal-400 transition-colors mb-3"><span className="material-symbols-outlined text-[22px]">upload_file</span></div>
                <p className={`text-xs font-heading font-medium mb-1 ${fileName ? 'text-accent' : 'text-on-surface'}`}>{fileName || 'Drag & drop audio file here'}</p>
                <p className="text-[11px] text-on-surface-variant font-sans">Supports WAV, MP3, FLAC, M4A</p>
                <input ref={fileInputRef} accept=".wav,.mp3,.flac,.m4a,audio/*" className="hidden" type="file" onChange={onPick} />
              </div>
            </div>
            <div className="pt-8">
              <button
                onClick={pickFile}
                disabled={connecting}
                className="w-full bg-surface-high hover:bg-surface-highest disabled:opacity-60 text-on-surface font-medium text-xs tracking-wider uppercase py-3.5 px-4 rounded-lg flex items-center justify-center gap-2 border border-outline-dim transition-all cursor-pointer font-heading">
                <span className="material-symbols-outlined text-[18px]">folder_open</span>
                <span>Browse Audio File</span>
              </button>
            </div>
          </div>
        </div>
        <div className="mt-8 text-center">
          <span className="inline-flex items-center gap-2 text-xs text-on-surface-variant/80 px-3.5 py-1 rounded-full bg-surface-low border border-outline-dim"><span className="material-symbols-outlined text-[14px] text-teal-400">shield_with_heart</span><span>AST model inference · DirectML GPU accelerated</span></span>
        </div>
      </main>
      <footer className="w-full border-t border-outline-dim bg-surface-lowest py-3 text-xs text-on-surface-variant">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>VAANI KAVACH — Voice Signal Integrity</span>
          <span className="text-[11px] text-on-surface-variant/70 font-sans flex items-center gap-1.5"><span className="material-symbols-outlined text-[13px] text-teal-400">verified</span>Ready for audio ingestion</span>
        </div>
      </footer>
    </div>
  )
}
