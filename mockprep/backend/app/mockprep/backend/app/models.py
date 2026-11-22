from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    results = relationship("QuestionResult", back_populates="user", cascade="all, delete-orphan")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(100), nullable=False)               # e.g., 'Software Engineer', 'Data Analyst'
    interview_type = Column(String(50), nullable=False)     # 'Technical' or 'Behavioral'
    difficulty = Column(String(50), nullable=False)         # 'Easy', 'Medium', 'Hard'
    status = Column(String(50), default="IN_PROGRESS")      # 'IN_PROGRESS', 'COMPLETED'
    average_score = Column(Float, default=0.0)              # Score out of 10
    total_questions = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    results = relationship("QuestionResult", back_populates="session", cascade="all, delete-orphan")

class QuestionResult(Base):
    __tablename__ = "question_results"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    user_answer = Column(Text, nullable=False)
    
    # Weighted Scoring out of 10
    score = Column(Float, nullable=False)                   # Overall out of 10.0
    correctness = Column(Float, default=0.0)               # out of 10.0 (weight 2.5)
    clarity = Column(Float, default=0.0)                   # out of 10.0 (weight 2.0)
    depth = Column(Float, default=0.0)                     # out of 10.0 (weight 2.0)
    relevance = Column(Float, default=0.0)                 # out of 10.0 (weight 2.0)
    communication = Column(Float, default=0.0)             # out of 10.0 (weight 1.5)
    
    # Feedback & Reference
    feedback_summary = Column(Text, nullable=True)
    strengths_json = Column(Text, nullable=True)           # JSON string of list
    improvements_json = Column(Text, nullable=True)        # JSON string of list
    model_answer = Column(Text, nullable=True)             # High-scoring benchmark answer
    
    time_taken_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="results")
    user = relationship("User", back_populates="results")
