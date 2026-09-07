import React, { useEffect, useRef, useState } from 'react'
import { openInferenceStream } from '../services/api'

const TARGET_RATE = 16000
const CHUNK_SAMPLES = 1600

function resample(samples, sourceRate) {
  if (sourceRate === TARGET_RATE) return samples
  const output = new Float32Array(Math.round(samples.length * TARGET_RATE / sourceRate)); const ratio = sourceRate / TARGET_RATE
  for (let i = 0; i < output.length; i += 1) { const at = i * ratio; const left = Math.floor(at); const right = Math.min(left + 1, samples.length - 1); output[i] = samples[left] + (samples[right] - samples[left]) * (at - left) }
  return output
}

export default function VoiceRecorder({ onStart, onEvent, onDone, onError }) {
  const inputRef = useRef(null); const resources = useRef({}); const [selected, setSelected] = useState(null); const [capturing, setCapturing] = useState(false)
  const dispose = (finish = true) => { const active = resources.current; active.worklet?.disconnect(); active.source?.disconnect(); active.sink?.disconnect(); active.context?.close(); active.tracks?.forEach(track => track.stop()); if (finish) active.stream?.stop(); else active.stream?.close(); resources.current = {}; setCapturing(false) }
  useEffect(() => () => dispose(false), [])
  const open = async (source, name) => { const stream = openInferenceStream({ onEvent: event => { onEvent?.(event); if (event.action === 'done') { onDone?.(event.final_summary); dispose(false) } }, onError }); resources.current.stream = stream; await stream.ready; onStart?.({ sessionId: stream.sessionId, source, name }); return stream }
  const sendInChunks = async (stream, data, pace = false) => { for (let start = 0; start < data.length; start += CHUNK_SAMPLES) { stream.send(data.subarray(start, start + CHUNK_SAMPLES)); if (pace) await new Promise(resolve => window.setTimeout(resolve, 100)) } }
  const analyzeFile = async () => { if (!selected) return inputRef.current?.click(); try { setCapturing(true); const stream = await open('file', selected.name); const context = new AudioContext(); const buffer = await context.decodeAudioData(await selected.arrayBuffer()); await context.close(); const mono = new Float32Array(buffer.length); for (let channel = 0; channel < buffer.numberOfChannels; channel += 1) for (let i = 0; i < mono.length; i += 1) mono[i] += buffer.getChannelData(channel)[i] / buffer.numberOfChannels; await sendInChunks(stream, resample(mono, buffer.sampleRate), true); stream.stop() } catch (error) { dispose(false); onError?.(error) } }
  const startMic = async () => { try { setCapturing(true); const stream = await open('microphone', 'live microphone'); const media = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } }); const context = new AudioContext(); await context.audioWorklet.addModule('/audio-worklet-processor.js'); const source = context.createMediaStreamSource(media); const worklet = new AudioWorkletNode(context, 'capture-processor'); const sink = context.createGain(); sink.gain.value = 0; const pending = []; worklet.port.onmessage = ({ data }) => { pending.push(...resample(data, context.sampleRate)); while (pending.length >= CHUNK_SAMPLES) stream.send(new Float32Array(pending.splice(0, CHUNK_SAMPLES))) }; source.connect(worklet); worklet.connect(sink); sink.connect(context.destination); resources.current = { stream, context, source, worklet, sink, tracks: media.getTracks() } } catch (error) { dispose(false); onError?.(error) } }
  return <div className="recorder"><input ref={inputRef} className="visually-hidden" type="file" accept="audio/*" onChange={event => setSelected(event.target.files?.[0] || null)} />
    {!capturing && <><button className="primary-button capture-button" onClick={startMic}>USE MICROPHONE <span>●</span></button><button className="secondary-button" onClick={analyzeFile}>{selected ? 'ANALYZE SELECTED FILE' : 'SELECT AUDIO FILE'} <span>+</span></button></>}
    {capturing && <button className="text-button" onClick={() => dispose(true)}>STOP & VIEW SUMMARY</button>}
    {selected && !capturing && <button className="file-chip" onClick={() => inputRef.current?.click()}>{selected.name} <span>{(selected.size / 1024 / 1024).toFixed(2)} MB</span></button>}
  </div>
}
