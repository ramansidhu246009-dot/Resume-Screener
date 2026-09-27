from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import shutil

from app.extractor import extract_text
from app.ranker import load_model, rank_resumes, process_job_background
from app.schemas import RankResponse, JobCreateResponse, JobStatusResponse
from app.database import engine, Base, get_db
from app.models import ScreeningJob, Candidate

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Resume Screener (Production Edition)")

@app.on_event("startup")
def startup_event():
    # Pre-load the ML model in the main thread to prevent 
    # OpenMP/PyTorch deadlocks and slow initialization in background threads.
    print("Pre-loading ML model...", flush=True)
    load_model()
    print("ML model loaded successfully.", flush=True)

MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB
MAX_FILE_COUNT = 50

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

uploads_dir = "/tmp/uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "UI not found"

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/jobs", response_model=JobCreateResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=422, detail="Job description cannot be empty")
    if not resumes:
        raise HTTPException(status_code=422, detail="No resumes supplied")
    if len(resumes) > MAX_FILE_COUNT:
        raise HTTPException(status_code=400, detail=f"Maximum of {MAX_FILE_COUNT} files allowed")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(uploads_dir, job_id)
    os.makedirs(job_dir, exist_ok=True)

    file_paths = {}
    for resume in resumes:
        if resume.size > MAX_FILE_SIZE:
            continue
        file_path = os.path.join(job_dir, resume.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        file_paths[resume.filename] = file_path

    new_job = ScreeningJob(
        id=job_id,
        job_description=job_description,
        total_files=len(file_paths),
        status="pending"
    )
    db.add(new_job)
    db.commit()

    # Start background task
    background_tasks.add_task(process_job_background, job_id, file_paths)

    return {"job_id": job_id, "status": "pending", "message": "Job successfully queued for background processing."}

@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ScreeningJob).filter(ScreeningJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidates = db.query(Candidate).filter(Candidate.job_id == job_id).all()
    
    results = []
    failed = []
    
    valid_cands = [c for c in candidates if c.status == "success"]
    valid_cands.sort(key=lambda x: x.score, reverse=True)
    
    for idx, c in enumerate(valid_cands):
        results.append({
            "rank": idx + 1,
            "filename": c.filename,
            "score": c.score,
            "matched_keywords": c.matched_keywords.split(",") if c.matched_keywords else []
        })
        
    for c in candidates:
        if c.status == "failed":
            failed.append({
                "filename": c.filename,
                "error": c.error_message or "Unknown error"
            })

    progress = 0
    if job.total_files > 0:
        progress = int((job.processed_files / job.total_files) * 100)

    return {
        "job_id": job.id,
        "status": job.status,
        "total_files": job.total_files,
        "processed_files": job.processed_files,
        "progress_percentage": progress,
        "created_at": job.created_at,
        "results": results,
        "failed": failed
    }

