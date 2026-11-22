from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Interview Session Schemas ---
class CreateSessionRequest(BaseModel):
    role: str                       # e.g. "Software Engineer", "Data Analyst"
    interview_type: str             # "Technical" or "Behavioral"
    difficulty: str                 # "Easy", "Medium", "Hard"

class SessionResponse(BaseModel):
    id: int
    user_id: int
    role: str
    interview_type: str
    difficulty: str
    status: str
    average_score: float
    total_questions: int
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Question Generation & Evaluation ---
class GenerateQuestionRequest(BaseModel):
    session_id: int
    role: str
    interview_type: str             # "Technical" or "Behavioral"
    difficulty: str                 # "Easy", "Medium", "Hard"
    previous_questions: Optional[List[str]] = []

class QuestionResponse(BaseModel):
    id: Optional[str] = None
    question: str
    category: str
    hint: str
    expected_key_points: List[str]

class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_text: str
    category: Optional[str] = "General"
    user_answer: str
    time_taken_seconds: Optional[int] = 0

class WeightedScoreBreakdown(BaseModel):
    overall_score: float            # Out of 10.0
    correctness: float              # Out of 10.0 (weight 2.5)
    clarity: float                  # Out of 10.0 (weight 2.0)
    depth: float                    # Out of 10.0 (weight 2.0)
    relevance: float                # Out of 10.0 (weight 2.0)
    communication: float            # Out of 10.0 (weight 1.5)

class EvaluationResponse(BaseModel):
    id: int
    session_id: int
    score: float
    breakdown: WeightedScoreBreakdown
    strengths: List[str]
    improvements: List[str]
    feedback_summary: str
    model_answer: str

# --- Dashboard & Analytics ---
class RecentSessionSummary(BaseModel):
    id: int
    role: str
    interview_type: str
    difficulty: str
    average_score: float
    total_questions: int
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DashboardAnalytics(BaseModel):
    total_interviews: int
    average_score: float
    total_questions_answered: int
    strongest_role: str
    recent_sessions: List[RecentSessionSummary]
    score_trend: List[float]
