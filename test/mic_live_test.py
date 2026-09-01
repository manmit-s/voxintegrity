"""Manual microphone smoke test for the binary compatibility websocket."""

import asyncio
import numpy as np
import sounddevice as sd
import websockets

SAMPLE_RATE = 16000
CHUNK_SAMPLES = SAMPLE_RATE // 2


async def stream_mic():
    uri = "ws://localhost:8000/api/v1/voice/ws/stream"
    async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
        loop = asyncio.get_running_loop()

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(status, flush=True)
            audio = np.asarray(indata, dtype=np.float32).reshape(-1)
            if audio.size:
                loop.create_task(websocket.send(audio.tobytes()))

        with sd.InputStream(channels=1, samplerate=SAMPLE_RATE, dtype="float32",
                            callback=audio_callback, blocksize=CHUNK_SAMPLES):
            try:
                while True:
                    print("Received:", await websocket.recv())
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    asyncio.run(stream_mic())
