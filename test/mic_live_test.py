import asyncio
import numpy as np
import sounddevice as sd
import websockets

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SECONDS = 0.5
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_SECONDS)

async def stream_mic():
    uri = "ws://localhost:8000/api/v1/voice/ws/stream"

    async with websockets.connect(uri, ping_interval=None, ping_timeout=None) as websocket:
        print("Connected to backend websocket.")
        print("Speak now...")

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(status, flush=True)

            audio = np.frombuffer(indata, dtype=np.float32)
            audio = audio.reshape(-1)

            if audio.size > 0:
                try:
                    loop.create_task(websocket.send(audio.tobytes()))
                except Exception:
                    pass

        loop = asyncio.get_running_loop()

        with sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype="float32",
            callback=audio_callback,
            blocksize=CHUNK_SAMPLES,
        ):
            try:
                while True:
                    msg = await websocket.recv()
                    print("Received:", msg)
            except KeyboardInterrupt:
                print("\nStopping mic stream.")
            finally:
                print("Disconnected.")

asyncio.run(stream_mic())