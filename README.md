# Vaani Kavach - Voice Protection System

> Hackathon project for secure voice authentication and deepfake detection.

## Overview
Vaani Kavach provides real-time voice verification using ML pipeline + FastAPI backend + React frontend with Supabase.

## Architecture
- **Backend**: FastAPI (Python 3.11) - auth, voice verification, history, Supabase
- **Frontend**: React + Vite + React Router + Supabase JS
- **ML Pipeline**: PyTorch - MFCC + CNN for deepfake detection
- **Infra**: Docker + GitHub Actions (inactive, manual dispatch)

## Project Structure
\\\
backend/         # FastAPI service
frontend/        # React app
ml_pipeline/     # Training & evaluation
.github/workflows # CI/CD (inactive)
\\\

## Quick Start
### Backend
\\\ash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
\\\
### Frontend
\\\ash
cd frontend
npm install
npm run dev
\\\
### ML
\\\ash
cd ml_pipeline
pip install -r requirements-ml.txt
python src/train.py
\\\

## CI/CD
Pipelines are configured as \workflow_dispatch\ only (inactive) - see \.github/workflows/*\.
To activate, uncomment \push\/\pull_request\ triggers.

## Team
Hackathon 2026 - Vaani Kavach

## License
MIT
