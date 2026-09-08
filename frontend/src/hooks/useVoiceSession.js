import { useCallback, useEffect, useRef, useState } from 'react'
import { openInferenceStream } from '../services/api'

const TARGET_RATE = 16000
const CHUNK_SAMPLES = 1600
export const VERDICT_THRESHOLD = 0.5

function resample(samples, sourceRate) {
  if (sourceRate === TARGET_RATE) return samples
  const output = new Float32Array(Math.round(samples.length * TARGET_RATE / sourceRate))
  const ratio = sourceRate / TARGET_RATE
  for (let i = 0; i < output.length; i += 1) {
    const at = i * ratio
    const left = Math.floor(at)
    const right = Math.min(left + 1, samples.length - 1)
    output[i] = samples[left] + (samples[right] - samples[left]) * (at - left)
  }
  return output
}

function clampPcm(samples) {
  const pcm = new Float32Array(samples.length)
  for (let i = 0; i < samples.length; i += 1) pcm[i] = Math.max(-1, Math.min(1, samples[i]))
  return pcm
}

export function useVoiceSession() {
  const [phase, setPhase] = useState('idle') // idle | connecting | live | summary
  const [sessionId, setSessionId] = useState(null)
  const [points, setPoints] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [vuLevel, setVuLevel] = useState(0) // 0..1 rms
  const [elapsedMs, setElapsedMs] = useState(0)

  const streamRef = useRef(null)
  const audioRef = useRef(null)
  const startedAtRef = useRef(0)
  const timerRef = useRef(null)

  const teardownAudio = useCallback(() => {
    const active = audioRef.current
    if (!active) return
    if (active.raf) cancelAnimationFrame(active.raf)
    active.worklet?.disconnect(); active.source?.disconnect(); active.sink?.disconnect()
    active.context?.close().catch(() => {})
    active.tracks?.forEach(track => track.stop())
    audioRef.current = null
    setVuLevel(0)
  }, [])

  const handleEvent = useCallback((event) => {
    if (event.action === 'score') setPoints(current => [...current, event])
    else if (event.action === 'done') {
      setSummary(event.final_summary)
      setPhase('summary')
      teardownAudio()
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [teardownAudio])

  const handleError = useCallback((issue) => setError(issue?.message || String(issue)), [])

  const openSession = useCallback(async () => {
    const stream = openInferenceStream({ onEvent: handleEvent, onError: handleError })
    streamRef.current = stream
    setSessionId(stream.sessionId)
    setPoints([]); setSummary(null); setError('')
    setPhase('connecting')
    await stream.ready
    startedAtRef.current = Date.now()
    setElapsedMs(0)
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => setElapsedMs(Date.now() - startedAtRef.current), 100)
    return stream
  }, [handleEvent, handleError])

  const startMic = useCallback(async () => {
    try {
      setError('')
      setPhase('connecting')
      const stream = await openSession()
      const media = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
      const context = new AudioContext()
      await context.audioWorklet.addModule('/audio-worklet-processor.js')
      const source = context.createMediaStreamSource(media)
      const worklet = new AudioWorkletNode(context, 'capture-processor')
      const sink = context.createGain()
      sink.gain.value = 0
      const analyser = context.createAnalyser()
      analyser.fftSize = 1024
      const pending = []
      worklet.port.onmessage = ({ data }) => {
        pending.push(...resample(data, context.sampleRate))
        while (pending.length >= CHUNK_SAMPLES) stream.send(new Float32Array(pending.splice(0, CHUNK_SAMPLES)))
      }
      source.connect(worklet)
      source.connect(analyser)
      worklet.connect(sink)
      sink.connect(context.destination)
      audioRef.current = { context, source, worklet, sink, analyser, tracks: media.getTracks(), raf: 0 }
      // Real input level for the VU meter (replaces the mockup's random animation).
      const scratch = new Float32Array(analyser.fftSize)
      const tick = () => {
        const active = audioRef.current
        if (!active) return
        active.analyser.getFloatTimeDomainData(scratch)
        let sum = 0
        for (let i = 0; i < scratch.length; i += 1) sum += scratch[i] * scratch[i]
        setVuLevel(Math.min(1, Math.sqrt(sum / scratch.length) * 4))
        active.raf = requestAnimationFrame(tick)
      }
      audioRef.current.raf = requestAnimationFrame(tick)
      setPhase('live')
    } catch (issue) {
      teardownAudio()
      streamRef.current?.close()
      streamRef.current = null
      setPhase('idle')
      handleError(issue)
    }
  }, [handleError, openSession, teardownAudio])

  const analyzeFile = useCallback(async (file) => {
    if (!file) return
    try {
      setError('')
      setPhase('connecting')
      const stream = await openSession()
      const context = new AudioContext()
      const buffer = await context.decodeAudioData(await file.arrayBuffer())
      await context.close()
      const mono = new Float32Array(buffer.length)
      for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) {
        const data = buffer.getChannelData(channel)
        for (let i = 0; i < mono.length; i += 1) mono[i] += data[i] / buffer.numberOfChannels
      }
      const pcm = clampPcm(resample(mono, buffer.sampleRate))
      setPhase('live')
      for (let start = 0; start < pcm.length; start += CHUNK_SAMPLES) {
        stream.send(pcm.subarray(start, start + CHUNK_SAMPLES))
        await new Promise(resolve => window.setTimeout(resolve, 100))
      }
      stream.stop()
    } catch (issue) {
      teardownAudio()
      streamRef.current?.close()
      streamRef.current = null
      setPhase('idle')
      handleError(issue)
    }
  }, [handleError, openSession, teardownAudio])

  const stopCapture = useCallback(() => {
    // Backend replies with a "done" event; the handler moves us to summary.
    streamRef.current?.stop()
    teardownAudio()
    if (timerRef.current) clearInterval(timerRef.current)
  }, [teardownAudio])

  const reset = useCallback(() => {
    streamRef.current?.close()
    streamRef.current = null
    teardownAudio()
    if (timerRef.current) clearInterval(timerRef.current)
    setPhase('idle'); setSessionId(null); setPoints([]); setSummary(null); setError(''); setVuLevel(0); setElapsedMs(0)
  }, [teardownAudio])

  useEffect(() => () => {
    streamRef.current?.close()
    teardownAudio()
    if (timerRef.current) clearInterval(timerRef.current)
  }, [teardownAudio])

  return { phase, sessionId, points, summary, error, vuLevel, elapsedMs, startMic, analyzeFile, stopCapture, reset }
}
