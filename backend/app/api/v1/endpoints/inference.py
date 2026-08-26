from fastapi import APIRouter, UploadFile, File, HTTPException
from app.ml_integration.preprocessor import preprocess_audio
from app.ml_integration.model_loader import get_model

router = APIRouter()

@router.post("/verify")
async def verify_voice(file: UploadFile = File(...)):
    try:
        waveform = await preprocess_audio(file)
        model = get_model()
        # score = model.predict(waveform)
        score = 0.87  # placeholder
        return {"filename": file.filename, "score": score, "verdict": "real" if score > 0.5 else "fake"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/detect-deepfake")
async def detect_deepfake(file: UploadFile = File(...)):
    return {"result": "pending-model-integration", "filename": file.filename}
