import axios from 'axios'
import supabase from './supabaseClient'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(async (config) => {
  const { data: { session } } = supabase
    ? await supabase.auth.getSession()
    : { data: { session: null } }
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

export const verifyVoice = (formData) => api.post('/voice/verify', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})

export const getHistory = () => api.get('/history')
export const login = (email, password) => api.post('/auth/login', { email, password })

const wsBase = () => (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/^http/, 'ws').replace(/\/$/, '')
const pcm16Base64 = (samples) => { const pcm = new Int16Array(samples.length); for (let i = 0; i < samples.length; i += 1) pcm[i] = Math.max(-1, Math.min(1, samples[i])) * 32767; const bytes = new Uint8Array(pcm.buffer); let binary = ''; for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000)); return btoa(binary) }

// The one canonical stream protocol: JSON envelopes containing little-endian PCM16 at 16 kHz.
export function openInferenceStream({ onEvent, onError }) {
  const sessionId = `VK-${crypto.randomUUID()}`; const socket = new WebSocket(`${wsBase()}/voice/stream-inference`)
  const ready = new Promise((resolve, reject) => { socket.onopen = () => socket.send(JSON.stringify({ action: 'start', session_id: sessionId, audio_format: 'pcm16_16khz' })); socket.onerror = () => reject(new Error('Unable to connect to the inference stream.')); socket.onmessage = ({ data }) => { const event = JSON.parse(data); if (event.action === 'error') { const error = new Error(event.detail); onError?.(error); reject(error); return }; onEvent?.(event); if (event.action === 'started') resolve() } })
  return { sessionId, ready, send(samples) { if (socket.readyState === WebSocket.OPEN && samples.length) socket.send(JSON.stringify({ action: 'chunk', session_id: sessionId, audio_bytes: pcm16Base64(samples) })) }, stop() { if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ action: 'stop', session_id: sessionId })) }, close() { socket.close() } }
}

export default api
