from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class RankedResume(BaseModel):
    rank: int
    filename: str
    score: float
    matched_keywords: Optional[List[str]] = []

class FailedResume(BaseModel):
    filename: str
    error: str

# Legacy response schema (kept for backward compatibility if needed)
class RankResponse(BaseModel):
    job_description_chars: int
    results: List[RankedResume]
    failed: List[FailedResume]

# New Async API schemas
class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    total_files: int
    processed_files: int
    progress_percentage: int
    created_at: datetime
    results: List[RankedResume]
    failed: List[FailedResume]
