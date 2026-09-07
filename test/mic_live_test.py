"""Manual microphone smoke test for the canonical JSON/PCM16 websocket."""

import asyncio
import base64
import uuid

import numpy as np
import sounddevice as sd
import websockets

SAMPLE_RATE = 16000
CHUNK_SAMPLES = SAMPLE_RATE // 2


async def stream_mic():
    session_id = f"VK-smoke-{uuid.uuid4()}"
    uri = "ws://localhost:8000/api/v1/voice/stream-inference"
    async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
        await websocket.send('{"action":"start","session_id":"%s","audio_format":"pcm16_16khz"}' % session_id)
        print("Received:", await websocket.recv())
        loop = asyncio.get_running_loop()

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(status, flush=True)
            pcm = np.clip(indata[:, 0], -1, 1)
            encoded = base64.b64encode((pcm * 32767).astype("<i2").tobytes()).decode()
            loop.create_task(websocket.send('{"action":"chunk","session_id":"%s","audio_bytes":"%s"}' % (session_id, encoded)))

        with sd.InputStream(channels=1, samplerate=SAMPLE_RATE, dtype="float32", callback=audio_callback, blocksize=CHUNK_SAMPLES):
            try:
                while True:
                    print("Received:", await websocket.recv())
            except KeyboardInterrupt:
                await websocket.send('{"action":"stop","session_id":"%s"}' % session_id)


if __name__ == "__main__":
    asyncio.run(stream_mic())
