from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

class ScreeningJob(Base):
    __tablename__ = "screening_jobs"

    id = Column(String, primary_key=True, index=True)
    job_description = Column(Text, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("screening_jobs.id"))
    filename = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    matched_keywords = Column(Text, nullable=True)  # Store as comma-separated string
    status = Column(String, default="success") # success, failed
    error_message = Column(Text, nullable=True)

    job = relationship("ScreeningJob", back_populates="candidates")
