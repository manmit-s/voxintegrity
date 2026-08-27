import { useState } from 'react'
import { verifyVoice } from '../services/api'

export default function VoiceRecorder() {
  const [result, setResult] = useState(null)
  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const fd = new FormData()
    fd.append('file', file)
    const { data } = await verifyVoice(fd)
    setResult(data)
  }
  return (
    <div>
      <input type='file' accept='audio/*' onChange={handleUpload} />
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  )
}
