"""
MockPrep - Single-file FastAPI Backend
Serves frontend + all API routes in one clean file.
"""
import os, json, random, re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
import jwt
from passlib.context import CryptContext

# ─── Config ───────────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("SECRET_KEY", "mockprep_secret_iet_lucknow_group05_2026")
ALGORITHM    = "HS256"
TOKEN_EXPIRE = 60 * 24 * 7          # 7 days in minutes

BASE_DIR     = Path(__file__).parent
FRONTEND_DIR = BASE_DIR / "frontend"
DB_URL       = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'mockprep.db'}")

# ─── Database ─────────────────────────────────────────────────────────────────
connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine       = create_engine(DB_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    sessions        = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    results         = relationship("QuestionResult",   back_populates="user", cascade="all, delete-orphan")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    role            = Column(String(100), nullable=False)
    interview_type  = Column(String(50),  nullable=False)
    difficulty      = Column(String(50),  nullable=False)
    status          = Column(String(50),  default="IN_PROGRESS")
    average_score   = Column(Float, default=0.0)
    total_questions = Column(Integer, default=0)
    started_at      = Column(DateTime, default=datetime.utcnow)
    completed_at    = Column(DateTime, nullable=True)
    user            = relationship("User", back_populates="sessions")
    results         = relationship("QuestionResult", back_populates="session", cascade="all, delete-orphan")

class QuestionResult(Base):
    __tablename__ = "question_results"
    id               = Column(Integer, primary_key=True, index=True)
    session_id       = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_text    = Column(Text, nullable=False)
    category         = Column(String(100), nullable=True)
    user_answer      = Column(Text, nullable=False)
    score            = Column(Float, nullable=False)
    correctness      = Column(Float, default=0.0)
    clarity          = Column(Float, default=0.0)
    depth            = Column(Float, default=0.0)
    relevance        = Column(Float, default=0.0)
    communication    = Column(Float, default=0.0)
    feedback_summary = Column(Text, nullable=True)
    strengths_json   = Column(Text, nullable=True)
    improvements_json= Column(Text, nullable=True)
    model_answer     = Column(Text, nullable=True)
    time_taken_seconds = Column(Integer, default=0)
    created_at       = Column(DateTime, default=datetime.utcnow)
    session          = relationship("InterviewSession", back_populates="results")
    user             = relationship("User", back_populates="results")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Auth helpers ─────────────────────────────────────────────────────────────
pwd_ctx  = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

def hash_pw(pw):       return pwd_ctx.hash(pw)
def verify_pw(pw, hpw):return pwd_ctx.verify(pw, hpw)

def make_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def current_user(creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ─── Schemas ──────────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    name: str
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class SessionIn(BaseModel):
    role: str
    interview_type: str
    difficulty: str

class GenQuestionIn(BaseModel):
    session_id: int
    role: str
    interview_type: str
    difficulty: str
    previous_questions: Optional[List[str]] = []

class SubmitAnswerIn(BaseModel):
    session_id: int
    question_text: str
    category: Optional[str] = "General"
    user_answer: str
    time_taken_seconds: Optional[int] = 0

# ─── Question Bank ────────────────────────────────────────────────────────────
QUESTION_BANK = [
    # Technical - Software Engineer
    {"role":"Software Engineer","type":"Technical","diff":"Easy",
     "question":"What is the difference between a process and a thread? How does memory sharing differ between them?",
     "category":"Operating Systems","hint":"Think about address spaces, heap vs stack, and context-switch cost."},
    {"role":"Software Engineer","type":"Technical","diff":"Easy",
     "question":"Explain how a HashMap works internally. What happens during a hash collision?",
     "category":"Data Structures","hint":"Discuss hashing, bucket arrays, chaining vs open addressing, load factor."},
    {"role":"Software Engineer","type":"Technical","diff":"Medium",
     "question":"Design a URL shortening service like Bitly. How would you generate unique aliases and handle high traffic?",
     "category":"System Design","hint":"Base62 encoding, distributed ID generation, Redis caching, CDN."},
    {"role":"Software Engineer","type":"Technical","diff":"Medium",
     "question":"Explain the difference between optimistic and pessimistic locking in databases with real-world examples.",
     "category":"Databases","hint":"SELECT FOR UPDATE vs version columns, contention levels, rollback costs."},
    {"role":"Software Engineer","type":"Technical","diff":"Hard",
     "question":"Walk me through how the Raft consensus algorithm handles leader election and log replication during a network partition.",
     "category":"Distributed Systems","hint":"Terms, election timeouts, quorum majority (N/2+1), split-brain resolution."},
    {"role":"Software Engineer","type":"Technical","diff":"Hard",
     "question":"How would you design a distributed rate limiter capable of 500k req/sec across multiple data centers?",
     "category":"Distributed Systems","hint":"Token bucket vs sliding window, Redis Lua scripts, local caching, fail-open policy."},
    # Behavioral
    {"role":"Software Engineer","type":"Behavioral","diff":"Medium",
     "question":"Tell me about a time you strongly disagreed with a technical decision. How did you handle it?",
     "category":"Conflict Resolution","hint":"STAR: use data, listen actively, disagree-and-commit, positive outcome."},
    {"role":"Software Engineer","type":"Behavioral","diff":"Medium",
     "question":"Describe a situation where a project you were responsible for failed or missed expectations. What did you learn?",
     "category":"Ownership & Resilience","hint":"Own the mistake, root cause analysis, systemic prevention, humility."},
    {"role":"Software Engineer","type":"Behavioral","diff":"Medium",
     "question":"Tell me about a time you were overwhelmed with competing high-priority deadlines. How did you prioritize?",
     "category":"Prioritization","hint":"RICE/Eisenhower matrix, proactive communication, scope negotiation, outcome."},
    # Data Analyst
    {"role":"Data Analyst","type":"Technical","diff":"Easy",
     "question":"What is the difference between WHERE and HAVING clauses in SQL? Give an example where WHERE would cause a syntax error.",
     "category":"SQL","hint":"Execution order: FROM→WHERE→GROUP BY→HAVING→SELECT. Aggregates need HAVING."},
    {"role":"Data Analyst","type":"Technical","diff":"Medium",
     "question":"Explain how you handle missing or heavily skewed data before feeding it into an analytics model.",
     "category":"Data Wrangling","hint":"MCAR/MAR/MNAR, imputation strategies, log transforms, IQR winsorization."},
    # Frontend / Backend
    {"role":"Frontend Developer","type":"Technical","diff":"Medium",
     "question":"Explain the JavaScript Event Loop: microtasks, macrotasks, and requestAnimationFrame. What is their execution order?",
     "category":"JavaScript Internals","hint":"Call stack → microtask queue (fully drained) → rAF → macrotask → paint."},
    {"role":"Backend Developer","type":"Technical","diff":"Medium",
     "question":"Explain the Saga pattern for distributed transactions. When would you choose choreography over orchestration?",
     "category":"Microservices","hint":"2PC bottlenecks, compensating transactions, event-driven vs coordinator model."},
]

def generate_question(role: str, itype: str, diff: str, previous: list) -> dict:
    # filter by role / type / difficulty, fallback progressively
    pool = [q for q in QUESTION_BANK if q["role"]==role and q["type"]==itype and q["diff"]==diff]
    if not pool:
        pool = [q for q in QUESTION_BANK if q["type"]==itype]
    if not pool:
        pool = list(QUESTION_BANK)
    fresh = [q for q in pool if q["question"] not in previous]
    chosen = random.choice(fresh if fresh else pool)
    return {
        "question": chosen["question"],
        "category": chosen["category"],
        "hint":     chosen["hint"],
        "expected_key_points": [
            "Core technical accuracy and depth",
            "Real-world trade-off analysis",
            "Clear structured explanation",
            "Measurable outcome or example"
        ]
    }

def evaluate_answer(question: str, answer: str, role: str, itype: str, diff: str, secs: int) -> dict:
    words = len(answer.strip().split())
    al    = answer.lower()

    # Base scores (out of 10)
    correctness   = 6.5
    clarity       = 7.0
    depth         = 6.0
    relevance     = 7.0
    communication = 7.0

    if words < 25:
        correctness -= 2.5; depth -= 3.0; clarity -= 2.0; communication -= 2.0
    elif 60 <= words <= 300:
        correctness += 1.8; depth += 2.2; clarity += 1.5; communication += 1.5
    elif words > 300:
        depth += 2.5; clarity -= 0.5

    markers = ["first","second","specifically","because","trade-off","example",
               "result","however","therefore","in contrast","I implemented","I designed"]
    if sum(1 for m in markers if m in al) >= 3:
        clarity += 1.5; communication += 1.5

    if itype == "Behavioral":
        star = sum([
            bool(re.search(r'(when i was|at company|during|in a project|we were)', al)),
            bool(re.search(r'(i decided|i implemented|i built|i scheduled|i analyzed)', al)),
            bool(re.search(r'(result|outcome|improved|reduced|increased|launched|saved)', al))
        ])
        if star >= 2: relevance += 1.8; correctness += 1.5

    # Cap at 10
    correctness   = round(min(9.8, max(3.0, correctness)), 1)
    clarity       = round(min(9.8, max(3.0, clarity)), 1)
    depth         = round(min(9.8, max(2.5, depth)), 1)
    relevance     = round(min(9.8, max(3.0, relevance)), 1)
    communication = round(min(9.8, max(3.0, communication)), 1)

    # Weighted total: 25%+20%+20%+20%+15% = 100%
    overall = round(
        correctness*0.25 + clarity*0.20 + depth*0.20 + relevance*0.20 + communication*0.15, 1
    )
    overall = max(3.5, min(9.8, overall))

    strengths, improvements = [], []
    if depth   >= 7.5: strengths.append("Strong technical depth with clear architectural reasoning.")
    else:              improvements.append("Elaborate further on underlying mechanics and trade-offs.")
    if clarity >= 7.5: strengths.append("Well-structured and easy to follow.")
    else:              improvements.append("Use numbered steps or bullet structure for clarity.")
    if words   >= 60:  strengths.append("Comprehensive response with good elaboration.")
    else:              improvements.append("Add a concrete real-world example or metric.")

    return {
        "overall_score": overall,
        "correctness":   correctness,
        "clarity":       clarity,
        "depth":         depth,
        "relevance":     relevance,
        "communication": communication,
        "strengths":     strengths[:3],
        "improvements":  improvements[:3],
        "feedback_summary": (
            f"Good response scoring {overall}/10. "
            + ("Adding measurable outcomes will push this into the top band." if overall < 8 else "Excellent answer demonstrating mastery!")
        ),
        "model_answer": (
            "A top-tier answer clearly defines the concept, compares alternative "
            "approaches with trade-offs, and concludes with a quantifiable real-world impact or example."
        )
    }

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="MockPrep API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "healthy", "app": "MockPrep", "version": "1.0.0"}

# ── Auth Routes ───────────────────────────────────────────────────────────────
@app.post("/api/auth/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(400, "Email already registered.")
    user = User(name=body.name, email=body.email.lower(), hashed_password=hash_pw(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": make_token(user.id), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email,
                     "created_at": user.created_at.isoformat()}}

@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_pw(body.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password.")
    return {"access_token": make_token(user.id), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email,
                     "created_at": user.created_at.isoformat()}}

@app.get("/api/auth/me")
def me(u: User = Depends(current_user)):
    return {"id": u.id, "name": u.name, "email": u.email, "created_at": u.created_at.isoformat()}

# ── Interview Routes ──────────────────────────────────────────────────────────
@app.post("/api/interview/session", status_code=201)
def create_session(body: SessionIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = InterviewSession(user_id=u.id, role=body.role,
                         interview_type=body.interview_type, difficulty=body.difficulty)
    db.add(s); db.commit(); db.refresh(s)
    return _session_dict(s)

@app.get("/api/interview/session/{sid}")
def get_session(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _get_session_or_404(sid, u.id, db)
    return _session_dict(s)

@app.post("/api/interview/generate-question")
def gen_question(body: GenQuestionIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    _get_session_or_404(body.session_id, u.id, db)
    q = generate_question(body.role, body.interview_type, body.difficulty, body.previous_questions)
    return q

@app.post("/api/interview/submit-answer")
def submit_answer(body: SubmitAnswerIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _get_session_or_404(body.session_id, u.id, db)
    ev = evaluate_answer(body.question_text, body.user_answer,
                         s.role, s.interview_type, s.difficulty, body.time_taken_seconds)
    r = QuestionResult(
        session_id=s.id, user_id=u.id,
        question_text=body.question_text, category=body.category,
        user_answer=body.user_answer,
        score=ev["overall_score"], correctness=ev["correctness"],
        clarity=ev["clarity"], depth=ev["depth"],
        relevance=ev["relevance"], communication=ev["communication"],
        feedback_summary=ev["feedback_summary"],
        strengths_json=json.dumps(ev["strengths"]),
        improvements_json=json.dumps(ev["improvements"]),
        model_answer=ev["model_answer"],
        time_taken_seconds=body.time_taken_seconds
    )
    db.add(r); db.commit(); db.refresh(r)
    # update session averages
    all_r = db.query(QuestionResult).filter(QuestionResult.session_id == s.id).all()
    s.average_score   = round(sum(x.score for x in all_r) / len(all_r), 1)
    s.total_questions = len(all_r)
    db.commit()
    return {
        "id": r.id, "session_id": s.id, "score": ev["overall_score"],
        "breakdown": {k: ev[k] for k in ["overall_score","correctness","clarity","depth","relevance","communication"]},
        "strengths": ev["strengths"], "improvements": ev["improvements"],
        "feedback_summary": ev["feedback_summary"], "model_answer": ev["model_answer"]
    }

@app.post("/api/interview/session/{sid}/complete")
def complete_session(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _get_session_or_404(sid, u.id, db)
    s.status = "COMPLETED"; s.completed_at = datetime.utcnow()
    db.commit(); db.refresh(s)
    return _session_dict(s)

# ── Dashboard Routes ──────────────────────────────────────────────────────────
@app.get("/api/dashboard/stats")
def dashboard_stats(u: User = Depends(current_user), db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == u.id)\
                 .order_by(InterviewSession.started_at.desc()).all()
    done = [s for s in sessions if s.total_questions > 0]
    avg  = round(sum(s.average_score for s in done) / len(done), 1) if done else 0.0
    from collections import defaultdict
    role_scores = defaultdict(list)
    for s in done: role_scores[s.role].append(s.average_score)
    best_role, best_avg = "None yet", 0.0
    for role, scores in role_scores.items():
        m = sum(scores)/len(scores)
        if m > best_avg: best_avg, best_role = m, f"{role} ({round(m,1)}/10)"
    return {
        "total_interviews":        len(sessions),
        "average_score":           avg,
        "total_questions_answered":sum(s.total_questions for s in sessions),
        "strongest_role":          best_role,
        "recent_sessions":         [_session_dict(s) for s in sessions[:10]],
        "score_trend":             [s.average_score for s in list(reversed(done))[-10:]]
    }

@app.get("/api/dashboard/session/{sid}/detail")
def session_detail(sid: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = _get_session_or_404(sid, u.id, db)
    results = db.query(QuestionResult).filter(QuestionResult.session_id == sid)\
                .order_by(QuestionResult.created_at.asc()).all()
    return {
        "session": _session_dict(s),
        "questions": [{
            "id": r.id,
            "question_text":    r.question_text,
            "category":         r.category,
            "user_answer":      r.user_answer,
            "score":            r.score,
            "breakdown":        {"correctness": r.correctness, "clarity": r.clarity,
                                 "depth": r.depth, "relevance": r.relevance,
                                 "communication": r.communication},
            "feedback_summary": r.feedback_summary,
            "strengths":        json.loads(r.strengths_json   or "[]"),
            "improvements":     json.loads(r.improvements_json or "[]"),
            "model_answer":     r.model_answer,
            "time_taken_seconds": r.time_taken_seconds,
            "created_at":       r.created_at.isoformat()
        } for r in results]
    }

# ── Helper functions ──────────────────────────────────────────────────────────
def _session_dict(s: InterviewSession) -> dict:
    return {
        "id": s.id, "user_id": s.user_id,
        "role": s.role, "interview_type": s.interview_type,
        "difficulty": s.difficulty, "status": s.status,
        "average_score": s.average_score, "total_questions": s.total_questions,
        "started_at":   s.started_at.isoformat(),
        "completed_at": s.completed_at.isoformat() if s.completed_at else None
    }

def _get_session_or_404(sid, uid, db):
    s = db.query(InterviewSession).filter(
        InterviewSession.id == sid, InterviewSession.user_id == uid).first()
    if not s:
        raise HTTPException(404, "Session not found.")
    return s

# ── Serve Frontend (SPA) ──────────────────────────────────────────────────────
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"msg": "API running. Frontend not found at: " + str(FRONTEND_DIR)}
