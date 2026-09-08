import React from 'react'
import { VERDICT_THRESHOLD } from '../hooks/useVoiceSession'

const W = 1000
const H = 380
const PAD = 60

function formatClock(ms) {
  const total = Math.floor(ms / 100)
  const seconds = Math.floor(total / 10)
  const centis = total % 10
  const sStr = seconds < 10 ? '0' + seconds : String(seconds)
  return `00:${sStr}.${centis}`
}

function formatAxis(ms) {
  const seconds = Math.floor(ms / 1000)
  const sStr = seconds < 10 ? '0' + seconds : String(seconds)
  return `00:${sStr}`
}

function buildPaths(points) {
  const spanMs = Math.max(30000, points.length ? points[points.length - 1].timestamp_ms : 0)
  const toXY = (point, index) => {
    const x = PAD + (point.timestamp_ms / spanMs) * (W - PAD - 30)
    const y = (1 - Math.min(1, Math.max(0, point.smoothed_score))) * H
    return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
  }
  const line = points.map(toXY).join(' ')
  const lastX = points.length ? PAD + (points[points.length - 1].timestamp_ms / spanMs) * (W - PAD - 30) : PAD
  const lastY = points.length ? (1 - Math.min(1, Math.max(0, points[points.length - 1].smoothed_score))) * H : H
  const area = points.length > 1 ? `${line} L ${lastX.toFixed(1)} ${H} L ${PAD} ${H} Z` : ''
  return { line, area, lastX, lastY, last: points[points.length - 1], spanMs }
}

export default function TelemetryScreen({ session }) {
  const { line, area, lastX, lastY, last, spanMs } = buildPaths(session.points)
  const current = last ? last.smoothed_score : 0
  const flagged = current >= VERDICT_THRESHOLD
  const scoreColor = flagged ? '#F59E0B' : '#2DD4BF'
  const thresholdTop = (1 - VERDICT_THRESHOLD) * H

  return (
    <div className="bg-surface-container-lowest font-body-base text-on-surface antialiased select-none min-h-screen flex flex-col justify-between">
      <header className="fixed top-0 left-0 w-full z-50 bg-surface-container-lowest/95 backdrop-blur-md border-b border-surface-container-high">
        <div className="h-16 w-full px-scale-6 flex items-center justify-between">
          <div className="flex items-center gap-scale-5">
            <div className="flex items-center gap-scale-3">
              <span className="font-headline-sm text-headline-sm text-on-surface font-bold tracking-tight">VAANI KAVACH</span>
              <span className="px-scale-2 py-0.5 bg-surface-container-high text-outline text-telemetry-micro font-label-caps uppercase rounded">v1.4</span>
            </div>
            <div className="h-4 w-px bg-surface-variant hidden sm:block"></div>
            <div className="flex items-center gap-scale-2">
              <span className="w-2 h-2 rounded-full bg-[#2DD4BF] animate-pulse shadow-[0_0_8px_#2DD4BF]"></span>
              <span className="font-telemetry-micro text-telemetry-micro text-[#2DD4BF] font-semibold uppercase tracking-wider">LIVE PROCESSING</span>
            </div>
          </div>
          <div className="flex items-center gap-scale-6">
            <div className="flex items-center gap-scale-2 bg-surface-container-low px-scale-3 py-scale-1 border border-surface-variant">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase">SESSION TIME:</span>
              <span className="font-telemetry-base text-telemetry-base text-on-surface font-semibold tracking-wider">{formatClock(session.elapsedMs)}</span>
            </div>
          </div>
        </div>
      </header>
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 pt-24 pb-8 flex flex-col gap-scale-5">
        <div className="bg-surface-container-low border border-surface-variant p-scale-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-scale-4">
          <div className="flex flex-col gap-scale-1">
            <span className="font-label-caps text-label-caps text-outline uppercase tracking-wider">CURRENT SPOOF SCORE</span>
            <div className="flex items-baseline gap-scale-2">
              <span className="font-verdict-xl text-verdict-xl font-bold tracking-tight" style={{ color: scoreColor }}>{session.points.length ? current.toFixed(2) : '—'}</span>
              <span className="font-headline-sm text-headline-sm text-outline">/ 1.00</span>
              {session.points.length > 0 && (
                <span className="ml-scale-3 px-scale-2 py-0.5 font-telemetry-micro font-semibold uppercase tracking-wider inline-flex items-center gap-1" style={{ background: `${scoreColor}1A`, border: `1px solid ${scoreColor}4D`, color: scoreColor }}>
                  <span className="material-symbols-outlined text-[14px]">{flagged ? 'warning' : 'verified'}</span>
                  {flagged ? 'Elevated Spoof Probability' : 'Within Authentic Range'}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-scale-6 text-telemetry-sm">
            <div className="flex flex-col">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase">DECISION THRESHOLD</span>
              <span className="font-semibold text-on-surface">≥ {VERDICT_THRESHOLD.toFixed(2)} Spoof</span>
            </div>
            <div className="h-8 w-px bg-surface-variant"></div>
            <div className="flex flex-col">
              <span className="font-telemetry-micro text-telemetry-micro text-outline uppercase">MODEL STATUS</span>
              <span className="font-semibold text-[#2DD4BF]">Inference Active</span>
            </div>
          </div>
        </div>
        <div className="w-full bg-surface-container-low border border-surface-variant p-scale-5 flex flex-col gap-scale-3">
          <div className="flex flex-wrap items-center justify-between gap-scale-3">
            <div className="flex items-center gap-scale-3">
              <span className="font-label-caps text-label-caps text-on-surface uppercase tracking-wider font-semibold">P(SPOOF) PROBABILITY STREAM</span>
              <span className="font-telemetry-micro text-telemetry-micro text-outline">TIME-SERIES (0.00 – 1.00)</span>
            </div>
            <div className="flex items-center gap-scale-5">
              <div className="flex items-center gap-scale-2"><span className="w-3 h-0.5 border-t border-dashed border-[#F59E0B]"></span><span className="font-telemetry-micro text-telemetry-micro text-on-surface-variant uppercase">Decision Threshold ({VERDICT_THRESHOLD.toFixed(2)})</span></div>
              <div className="flex items-center gap-scale-2"><span className="w-3 h-0.5 bg-gradient-to-r from-[#2DD4BF] to-[#F59E0B]"></span><span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]"></span><span className="font-telemetry-micro text-telemetry-micro text-on-surface-variant uppercase">Live Stream P(Spoof)</span></div>
            </div>
          </div>
          <div className="relative w-full h-[380px] bg-surface-container-lowest overflow-hidden border border-surface-variant">
            <div className="absolute inset-0 pointer-events-none opacity-30 bg-[linear-gradient(to_right,#272a30_1px,transparent_1px),linear-gradient(to_bottom,#272a30_1px,transparent_1px)] bg-[size:40px_40px]"></div>
            <div className="absolute left-0 w-full h-px bg-[#D97706]/40 border-t border-dashed border-[#D97706] pointer-events-none z-10" style={{ top: thresholdTop }}>
              <span className="absolute right-3 -top-4 font-telemetry-micro text-telemetry-micro text-[#D97706] uppercase tracking-wider flex items-center gap-1"><span className="material-symbols-outlined text-[12px]">straighten</span> DECISION THRESHOLD: {VERDICT_THRESHOLD.toFixed(2)} (SPOOF BOUNDARY)</span>
            </div>
            <div className="absolute top-2 left-3 z-20 flex flex-col justify-between h-[90%] font-telemetry-micro text-telemetry-micro select-none pointer-events-none text-outline">
              <span>1.00</span><span>0.80</span><span className="text-[#F59E0B] font-semibold flex items-center gap-0.5">{VERDICT_THRESHOLD.toFixed(2)} ⚑</span><span>0.60</span><span>0.40</span><span>0.20</span><span>0.00</span>
            </div>
            <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox={`0 0 ${W} ${H}`}>
              <defs>
                <linearGradient id="curveGlow" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.22"></stop>
                  <stop offset="50%" stopColor="#2DD4BF" stopOpacity="0.10"></stop>
                  <stop offset="100%" stopColor="#2DD4BF" stopOpacity="0"></stop>
                </linearGradient>
                <linearGradient id="traceGradient" x1="0%" x2="100%" y1="0%" y2="0%">
                  <stop offset="0%" stopColor="#2DD4BF"></stop>
                  <stop offset="35%" stopColor="#2DD4BF"></stop>
                  <stop offset="65%" stopColor="#38BDF8"></stop>
                  <stop offset="80%" stopColor="#F59E0B"></stop>
                  <stop offset="100%" stopColor="#F59E0B"></stop>
                </linearGradient>
                <filter height="200%" id="dotGlow" width="200%" x="-50%" y="-50%">
                  <feDropShadow dx="0" dy="0" floodColor="#F59E0B" floodOpacity="0.8" stdDeviation="3"></feDropShadow>
                </filter>
              </defs>
              {area && <path d={area} fill="url(#curveGlow)"></path>}
              {line && <path d={line} fill="none" stroke="url(#traceGradient)" strokeWidth="2.5"></path>}
              {last && <line stroke="#84958a" strokeDasharray="2,3" strokeWidth="1" x1={lastX} x2={lastX} y1="0" y2={H}></line>}
              {last && <circle cx={lastX} cy={lastY} fill={scoreColor} filter="url(#dotGlow)" r="5" stroke="#111319" strokeWidth="1.5"></circle>}
            </svg>
            <div className="absolute bottom-2 inset-x-12 z-20 flex justify-between font-telemetry-micro text-telemetry-micro text-outline pointer-events-none">
              <span>00:00</span>
              <span>{formatAxis(spanMs / 4)}</span>
              <span>{formatAxis(spanMs / 2)}</span>
              <span>{formatAxis(spanMs * 3 / 4)}</span>
              <span className="text-on-surface font-semibold">{formatAxis(spanMs)} (Now)</span>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-scale-4">
          <div className="bg-surface-container-low border border-surface-variant p-scale-4">
            <div className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">SESSION DURATION</div>
            <div className="font-telemetry-lg text-telemetry-lg text-on-surface font-semibold mt-scale-1">{formatAxis(session.elapsedMs)}</div>
            <div className="font-telemetry-micro text-telemetry-micro text-on-surface-variant mt-scale-1">Continuous capture in progress</div>
          </div>
          <div className="bg-surface-container-low border border-surface-variant p-scale-4">
            <div className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">ANALYZED WINDOWS</div>
            <div className="font-telemetry-lg text-telemetry-lg text-on-surface font-semibold mt-scale-1">{session.points.length} windows</div>
            <div className="font-telemetry-micro text-telemetry-micro text-on-surface-variant mt-scale-1">Sequential audio chunks evaluated</div>
          </div>
          <div className="bg-surface-container-low border border-surface-variant p-scale-4">
            <div className="font-telemetry-micro text-telemetry-micro text-outline uppercase tracking-wider">WINDOW STRIDE</div>
            <div className="font-telemetry-lg text-telemetry-lg text-on-surface font-semibold mt-scale-1">500 ms</div>
            <div className="font-telemetry-micro text-telemetry-micro text-on-surface-variant mt-scale-1">Analysis step interval</div>
          </div>
        </div>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-scale-4 pt-scale-2 border-t border-surface-variant">
          <div className="flex items-center gap-scale-3 text-telemetry-micro text-outline">
            <span className="inline-block w-2 h-2 rounded-full bg-[#14B8A6]"></span>
            <span>Standard forensic ingest pipeline active</span>
          </div>
          <div className="flex items-center gap-scale-3">
            <button onClick={session.stopCapture} className="px-scale-5 py-scale-2 bg-surface-container-low hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface border border-surface-variant font-label-caps text-label-caps uppercase tracking-wider transition-colors flex items-center justify-center gap-scale-2"><span className="material-symbols-outlined text-[16px]">stop_circle</span> Stop Capture</button>
            <button onClick={session.stopCapture} className="px-scale-6 py-scale-2 bg-[#14B8A6] text-slate-950 font-label-caps text-label-caps uppercase tracking-wider font-semibold shadow-[0_0_12px_rgba(20,184,166,0.3)] hover:bg-[#2DD4BF] transition-all flex items-center justify-center gap-scale-2"><span className="material-symbols-outlined text-[16px]">task_alt</span> Complete Analysis</button>
          </div>
        </div>
      </main>
      <footer className="w-full bg-surface-container-low border-t border-surface-variant py-scale-2 px-scale-6 text-outline text-telemetry-micro flex items-center justify-between"><span className="uppercase">VAANI KAVACH // ACOUSTIC INTEGRITY MONITOR</span><span>GENUINE CAPABILITY RUNTIME</span></footer>
    </div>
  )
}
