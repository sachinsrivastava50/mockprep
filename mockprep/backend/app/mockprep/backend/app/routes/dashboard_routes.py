import json
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, InterviewSession, QuestionResult
from ..schemas import DashboardAnalytics, RecentSessionSummary
from ..auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

@router.get("/stats", response_model=DashboardAnalytics)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == current_user.id
    ).order_by(InterviewSession.started_at.desc()).all()

    total_interviews = len(sessions)
    total_questions = sum(s.total_questions for s in sessions)
    
    # Calculate overall average score
    completed_sessions = [s for s in sessions if s.total_questions > 0]
    avg_score = 0.0
    if completed_sessions:
        avg_score = round(sum(s.average_score for s in completed_sessions) / len(completed_sessions), 1)

    # Determine strongest role
    role_scores = defaultdict(list)
    for s in completed_sessions:
        role_scores[s.role].append(s.average_score)

    strongest_role = "None yet"
    best_avg = 0.0
    for role, scores in role_scores.items():
        mean_score = sum(scores) / len(scores)
        if mean_score > best_avg:
            best_avg = mean_score
            strongest_role = f"{role} ({round(mean_score, 1)}/10)"

    # Score trend list (chronological order)
    chronological = list(reversed(completed_sessions))
    score_trend = [s.average_score for s in chronological[-10:]]

    recent_summaries = [RecentSessionSummary.from_orm(s) for s in sessions[:10]]

    return DashboardAnalytics(
        total_interviews=total_interviews,
        average_score=avg_score,
        total_questions_answered=total_questions,
        strongest_role=strongest_role,
        recent_sessions=recent_summaries,
        score_trend=score_trend
    )

@router.get("/session/{session_id}/detail")
def get_session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    results = db.query(QuestionResult).filter(
        QuestionResult.session_id == session.id
    ).order_by(QuestionResult.created_at.asc()).all()

    formatted_results = []
    for r in results:
        formatted_results.append({
            "id": r.id,
            "question_text": r.question_text,
            "category": r.category,
            "user_answer": r.user_answer,
            "score": r.score,
            "breakdown": {
                "correctness": r.correctness,
                "clarity": r.clarity,
                "depth": r.depth,
                "relevance": r.relevance,
                "communication": r.communication
            },
            "feedback_summary": r.feedback_summary,
            "strengths": json.loads(r.strengths_json) if r.strengths_json else [],
            "improvements": json.loads(r.improvements_json) if r.improvements_json else [],
            "model_answer": r.model_answer,
            "time_taken_seconds": r.time_taken_seconds,
            "created_at": r.created_at.isoformat()
        })

    return {
        "session": {
            "id": session.id,
            "role": session.role,
            "interview_type": session.interview_type,
            "difficulty": session.difficulty,
            "status": session.status,
            "average_score": session.average_score,
            "total_questions": session.total_questions,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        },
        "questions": formatted_results
    }
