import React, { useState } from 'react'
import { VERDICT_THRESHOLD } from '../hooks/useVoiceSession'

const C = 2 * Math.PI * 50 // circumference of the r=50 gauge circle

function formatAxis(ms) {
  const seconds = Math.floor(ms / 1000)
  const sStr = seconds < 10 ? '0' + seconds : String(seconds)
  return `00:${sStr}`
}

function download(name, content, type) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(url)
}

export default function SummaryScreen({ session }) {
  const [toast, setToast] = useState(null)
  const summary = session.summary
  const points = session.points
  const flagged = summary?.verdict === 'fake'
  const confidence = summary?.confidence ?? 0
  const avg = summary?.avg_score ?? 0
  const totalWindows = summary?.total_windows ?? points.length
  const highRisk = summary?.high_risk_windows ?? points.filter(point => point.smoothed_score >= VERDICT_THRESHOLD).length
  const flaggedPct = totalWindows ? (highRisk / totalWindows * 100) : 0
  const durationMs = points.length ? points[points.length - 1].window_end_ms : 0
  const gaugeOffset = C * (1 - Math.min(1, confidence))

  const notify = (title, message) => {
    setToast({ title, message })
    window.setTimeout(() => setToast(null), 3000)
  }

  const exportSession = () => {
    if (!points.length) return notify('Nothing to export', 'No score windows were recorded this session.')
    const payload = { session_id: session.sessionId, final_summary: summary, decision_threshold: VERDICT_THRESHOLD, windows: points }
    download(`vaani-kavach-${session.sessionId}.json`, JSON.stringify(payload, null, 2), 'application/json')
    const csv = ['timestamp_ms,window_start_ms,window_end_ms,score,smoothed_score,verdict']
      .concat(points.map(point => [point.timestamp_ms, point.window_start_ms, point.window_end_ms, point.score, point.smoothed_score, point.verdict].join(',')))
      .join('\n')
    download(`vaani-kavach-${session.sessionId}.csv`, csv, 'text/csv')
    notify('Export Ready', 'Session metrics and window scores exported as JSON and CSV.')
  }

  return (
    <div className="bg-surface-container-lowest font-body-base text-on-surface antialiased select-none min-h-screen flex flex-col justify-between">
      <header className="fixed top-0 left-0 w-full z-50 bg-surface-container-lowest/95 backdrop-blur-md border-b border-surface-container-high/60">
        <div className="h-16 w-full px-scale-6 flex items-center justify-between">
          <div className="flex items-center gap-scale-4">
            <div className="bg-surface-container-high px-scale-3 py-scale-1 flex items-center gap-scale-2">
              <span className="w-1.5 h-1.5 bg-primary-container"></span>
              <span className="font-label-caps text-label-caps text-primary-container tracking-widest uppercase">VAANI KAVACH</span>
            </div>
            <div className="hidden md:flex flex-col">
              <span className="font-telemetry-micro text-telemetry-micro uppercase text-on-surface-variant">Voice Deepfake Detection Platform</span>
            </div>
          </div>
          <div className="flex items-center gap-scale-2 bg-surface-container-low px-scale-3 py-scale-1 border border-surface-container-high">
            <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase">SESSION ID:</span>
            <span className="font-telemetry-sm text-telemetry-sm text-on-surface font-mono">{session.sessionId}</span>
          </div>
        </div>
      </header>
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 pt-24 pb-8 flex flex-col gap-scale-5">
        <div>
          <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider block mb-scale-1">SESSION ANALYSIS RESULT</span>
          <h1 className="font-verdict-xl text-[36px] md:text-verdict-xl text-on-surface uppercase tracking-tight">Audio Analysis Summary</h1>
        </div>
        <div className="w-full bg-surface-container-low border border-surface-container-high p-scale-6 md:p-scale-7">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-scale-6 items-center">
            <div className="lg:col-span-8 flex flex-col gap-scale-3">
              <div className="flex items-center gap-scale-2">
                <span className={`px-scale-3 py-scale-1 font-label-caps text-label-caps uppercase font-semibold flex items-center gap-scale-2 border ${flagged ? 'bg-secondary/15 text-secondary border-secondary/40' : 'bg-primary-container/15 text-primary-container border-primary-container/40'}`}>
                  <span className="material-symbols-outlined text-[15px]">{flagged ? 'warning' : 'verified_user'}</span>
                  {flagged ? 'Likely Synthetic Voice Detected' : 'Voice Appears Authentic'}
                </span>
              </div>
              <div className="py-scale-1">
                <h2 className="font-headline-lg text-headline-lg md:text-[28px] text-on-surface tracking-tight font-semibold">
                  {flagged ? 'High Probability of Synthetic Speech' : 'No Strong Synthetic Indicators Found'}
                </h2>
              </div>
              <p className="font-body-base text-body-base text-on-surface-variant max-w-2xl leading-relaxed">
                {flagged
                  ? 'The analyzed audio segment exhibits acoustic characteristics consistent with synthetic or voice-cloned generation across the analyzed temporal windows.'
                  : 'The analyzed audio segment does not exhibit dominant acoustic characteristics of synthetic or voice-cloned generation across the analyzed temporal windows.'}
              </p>
            </div>
            <div className="lg:col-span-4 flex flex-col items-center justify-center p-scale-6 bg-surface-container-lowest border border-surface-container-high">
              <div className="w-full flex items-center justify-between mb-scale-2">
                <span className="font-label-caps text-label-caps text-outline uppercase">Model Confidence</span>
                <span className={`font-label-caps text-label-caps font-semibold ${flagged ? 'text-secondary' : 'text-primary-container'}`}>{flagged ? 'Flagged' : 'Passing'}</span>
              </div>
              <div className="relative flex items-center justify-center my-scale-2">
                <svg className="w-36 h-36 -rotate-90 transform" viewBox="0 0 120 120">
                  <circle cx="60" cy="60" fill="none" r="50" stroke="#1d2025" strokeDasharray={C} strokeDashoffset="0" strokeWidth="8"></circle>
                  <circle cx="60" cy="60" fill="none" r="50" stroke={flagged ? '#f59e0b' : '#00f0a8'} strokeDasharray={C} strokeDashoffset={gaugeOffset} strokeLinecap="round" strokeWidth="8"></circle>
                </svg>
                <div className="absolute flex flex-col items-center justify-center">
                  <span className="font-telemetry-lg text-telemetry-lg font-bold tracking-tight" style={{ color: flagged ? '#ffb4a6' : '#00f0a8' }}>{Math.round(confidence * 100)}%</span>
                  <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">Spoof Probability</span>
                </div>
              </div>
              <div className="w-full text-center mt-scale-2">
                <span className="font-telemetry-sm text-telemetry-sm text-on-surface font-mono">Average Score: {avg.toFixed(3)}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-scale-4">
          <div className="bg-surface-container-low border border-surface-container-high p-scale-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-scale-2">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">Total Duration</span>
              <span className="material-symbols-outlined text-outline text-[18px]">timer</span>
            </div>
            <div className="font-telemetry-lg text-telemetry-lg text-on-surface font-semibold">{formatAxis(durationMs)}</div>
          </div>
          <div className="bg-surface-container-low border border-surface-container-high p-scale-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-scale-2">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">Analyzed Windows</span>
              <span className="material-symbols-outlined text-outline text-[18px]">view_agenda</span>
            </div>
            <div className="font-telemetry-lg text-telemetry-lg text-on-surface font-semibold">{totalWindows}</div>
          </div>
          <div className="bg-surface-container-low border border-surface-container-high p-scale-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-scale-2">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">Avg Spoof Score</span>
              <span className="material-symbols-outlined text-outline text-[18px]">percent</span>
            </div>
            <div className="font-telemetry-lg text-telemetry-lg text-on-surface font-semibold">{avg.toFixed(2)}</div>
          </div>
          <div className="bg-surface-container-low border border-surface-container-high p-scale-4 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-scale-2">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">Flagged Windows</span>
              <span className="material-symbols-outlined text-outline text-[18px]">flag</span>
            </div>
            <div className="font-telemetry-lg text-telemetry-lg font-semibold" style={{ color: flagged ? '#ffb4a6' : '#00f0a8' }}>{highRisk} <span className="text-telemetry-micro text-outline font-normal">/ {totalWindows}</span></div>
          </div>
        </div>
        <div className="w-full bg-surface-container-low border border-surface-container-high p-scale-5 flex flex-col gap-scale-3">
          <div className="flex items-center justify-between">
            <span className="font-label-caps text-label-caps text-on-surface uppercase tracking-wider font-semibold">WINDOW SCORE DISTRIBUTION</span>
            <span className="font-telemetry-micro text-telemetry-micro text-outline">Threshold {VERDICT_THRESHOLD.toFixed(2)} · Bars above are flagged</span>
          </div>
          <div className="w-full h-40 flex items-end gap-px bg-surface-container-lowest border border-surface-variant p-scale-2">
            {points.map((point, index) => (
              <div key={index} className={`flex-1 ${point.smoothed_score >= VERDICT_THRESHOLD ? 'bg-secondary' : 'bg-primary-container/80'}`} style={{ height: `${Math.round(Math.min(1, Math.max(0.02, point.smoothed_score)) * 100)}%` }} title={`Window ${index + 1}: ${point.smoothed_score.toFixed(2)}`}></div>
            ))}
            {!points.length && <div className="w-full text-center font-telemetry-micro text-telemetry-micro text-outline">No windows recorded.</div>}
          </div>
          <div className="w-full flex justify-between font-telemetry-micro text-telemetry-micro text-outline pt-scale-1">
            <span>00:00</span>
            <span>{formatAxis(durationMs / 2)}</span>
            <span>{formatAxis(durationMs)}</span>
          </div>
        </div>
        <div className="flex items-center justify-between text-telemetry-micro text-on-surface-variant font-mono pt-scale-1">
          <span>{highRisk} of {totalWindows} windows flagged above {VERDICT_THRESHOLD.toFixed(2)} cutoff ({flaggedPct.toFixed(1)}%)</span>
          <span>Sample Rate: 16kHz Mono</span>
        </div>
        <div className="w-full bg-surface-container-low border border-surface-container-high p-scale-5 flex flex-col sm:flex-row items-center justify-between gap-scale-4">
          <div className="text-telemetry-sm text-outline">Analysis complete for session audio stream.</div>
          <div className="flex flex-wrap items-center gap-scale-3 w-full sm:w-auto">
            <button onClick={exportSession} className="flex-1 sm:flex-initial flex items-center justify-center gap-scale-2 bg-surface-container-high hover:bg-surface-bright px-scale-4 py-scale-3 text-on-surface font-label-caps text-label-caps uppercase tracking-wider transition-colors border border-surface-variant">
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">download</span>
              <span>Export Session Data (.JSON / .CSV)</span>
            </button>
            <button onClick={session.reset} className="w-full sm:w-auto flex items-center justify-center gap-scale-2 bg-primary-container hover:bg-primary text-on-primary-container font-label-caps text-label-caps uppercase tracking-wider font-bold px-scale-5 py-scale-3 transition-colors shadow-sm">
              <span className="material-symbols-outlined text-[18px]">add_circle</span>
              <span>Analyze New Audio</span>
            </button>
          </div>
        </div>
        {toast && (
          <div className="fixed bottom-scale-6 right-scale-6 bg-surface-container-high border border-surface-variant p-scale-4 shadow-xl flex items-center gap-scale-3 z-50 rounded">
            <span className="w-2 h-2 bg-primary-container rounded-full"></span>
            <div className="flex flex-col">
              <span className="font-label-caps text-label-caps text-on-surface font-semibold">{toast.title}</span>
              <span className="font-telemetry-micro text-telemetry-micro text-on-surface-variant font-mono">{toast.message}</span>
            </div>
          </div>
        )}
      </main>
      <footer className="w-full border-t border-surface-container-high/60 bg-surface-container-lowest py-scale-3 px-scale-6 text-on-surface-variant"><div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-scale-3"><div className="flex items-center gap-scale-2 font-telemetry-micro text-telemetry-micro"><span className="w-1.5 h-1.5 rounded-full bg-primary-container"></span><span>Vaani Kavach Audio Verification</span></div><div className="font-telemetry-micro text-telemetry-micro text-outline">16kHz PCM Analysis Engine</div></div></footer>
    </div>
  )
}
