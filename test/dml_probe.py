import sys, time
from pathlib import Path

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
import onnxruntime as ort
device_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
print('ORT version:', ort.__version__)
print('Available providers:', ort.get_available_providers())
from app.ml_integration.model_loader import OnnxAudioClassifier

m = OnnxAudioClassifier(Path(__file__).resolve().parents[1] / (sys.argv[2] if len(sys.argv) > 2 else 'ml_pipeline/weights/ast_finetuned_fp32.onnx'), dml_device_id=device_id)
print('Session providers:', m.session.get_providers())
print('using_cpu_fallback after probe:', m.using_cpu_fallback)
rng = np.random.default_rng(0)
# realistic-shaped random input matching actual mel-feature stats (dB scale, ~[-80, 0])
w = rng.normal(-55.0, 18.0, 32000).astype(np.float32)
for i in range(5):
    t0 = time.perf_counter()
    s = m.predict(w)
    print(f'predict {i+1}: score={s:.4f} time={time.perf_counter()-t0:.3f}s cpu_fallback={m.using_cpu_fallback}')
print('FINAL providers after real inference:', m.session.get_providers())
print('FINAL using_cpu_fallback:', m.using_cpu_fallback)
