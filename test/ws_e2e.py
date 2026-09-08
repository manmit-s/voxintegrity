import asyncio, base64, json, uuid, numpy as np, websockets

async def main():
    sid = 'VK-e2e-' + str(uuid.uuid4())
    scores = []
    async with websockets.connect('ws://localhost:8000/api/v1/voice/stream-inference', ping_interval=None) as ws:
        await ws.send(json.dumps({'action':'start','session_id':sid,'audio_format':'pcm16_16khz'}))
        print('RECV:', await ws.recv(), flush=True)
        t = np.arange(32000*14)/16000.0
        audio = (0.3*np.sin(2*np.pi*220*t)*(1+0.5*np.sin(2*np.pi*3*t))).astype(np.float32)
        async def drain(timeout):
            try:
                while True:
                    ev = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
                    if ev.get('action') == 'score': scores.append(ev['score'])
                    elif ev.get('action') == 'done': print('DONE summary:', ev['final_summary'], flush=True)
                    elif ev.get('action') == 'error': print('ERROR:', ev, flush=True)
            except asyncio.TimeoutError:
                return
        for i in range(28):
            chunk = audio[i*16000:(i+1)*16000]
            b64 = base64.b64encode(np.clip(chunk,-1,1).astype('<i2').tobytes()).decode()
            await ws.send(json.dumps({'action':'chunk','session_id':sid,'audio_bytes':b64}))
            await drain(0.05)
        await drain(8)
        await ws.send(json.dumps({'action':'stop','session_id':sid}))
        print('Final RECV:', (await ws.recv())[:250], flush=True)
    print('score count:', len(scores), 'unique:', len(set(scores)), 'min/max:', (min(scores), max(scores)) if scores else None, flush=True)

asyncio.run(main())
