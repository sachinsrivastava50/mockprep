import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, InterviewSession, QuestionResult
from ..schemas import (
    CreateSessionRequest,
    SessionResponse,
    GenerateQuestionRequest,
    QuestionResponse,
    SubmitAnswerRequest,
    EvaluationResponse,
    WeightedScoreBreakdown
)
from ..auth import get_current_user
from ..ai_service import generate_interview_question, evaluate_interview_answer

router = APIRouter(prefix="/interview", tags=["Interview"])

@router.post("/session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_session = InterviewSession(
        user_id=current_user.id,
        role=payload.role,
        interview_type=payload.interview_type,
        difficulty=payload.difficulty,
        status="IN_PROGRESS",
        average_score=0.0,
        total_questions=0,
        started_at=datetime.utcnow()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return SessionResponse.from_orm(new_session)

@router.get("/session/{session_id}", response_model=SessionResponse)
def get_session(
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
    return SessionResponse.from_orm(session)

@router.post("/generate-question", response_model=QuestionResponse)
def api_generate_question(
    payload: GenerateQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session ownership
    session = db.query(InterviewSession).filter(
        InterviewSession.id == payload.session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Call AI service
    result = generate_interview_question(
        role=payload.role,
        interview_type=payload.interview_type,
        difficulty=payload.difficulty,
        previous_questions=payload.previous_questions
    )

    return QuestionResponse(
        question=result["question"],
        category=result.get("category", "General"),
        hint=result.get("hint", ""),
        expected_key_points=result.get("expected_key_points", [])
    )

@router.post("/submit-answer", response_model=EvaluationResponse)
def api_submit_answer(
    payload: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(InterviewSession).filter(
        InterviewSession.id == payload.session_id,
        InterviewSession.user_id == current_user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")

    # Evaluate answer using weighted scoring model out of 10
    eval_result = evaluate_interview_answer(
        question_text=payload.question_text,
        category=payload.category,
        user_answer=payload.user_answer,
        role=session.role,
        interview_type=session.interview_type,
        difficulty=session.difficulty,
        time_taken_seconds=payload.time_taken_seconds
    )

    # Save result to PostgreSQL / SQLite
    new_result = QuestionResult(
        session_id=session.id,
        user_id=current_user.id,
        question_text=payload.question_text,
        category=payload.category,
        user_answer=payload.user_answer,
        score=eval_result["overall_score"],
        correctness=eval_result["correctness"],
        clarity=eval_result["clarity"],
        depth=eval_result["depth"],
        relevance=eval_result["relevance"],
        communication=eval_result["communication"],
        feedback_summary=eval_result["feedback_summary"],
        strengths_json=json.dumps(eval_result["strengths"]),
        improvements_json=json.dumps(eval_result["improvements"]),
        model_answer=eval_result["model_answer"],
        time_taken_seconds=payload.time_taken_seconds
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    # Recalculate session average score
    all_results = db.query(QuestionResult).filter(QuestionResult.session_id == session.id).all()
    if all_results:
        total = sum(r.score for r in all_results)
        session.average_score = round(total / len(all_results), 1)
        session.total_questions = len(all_results)
        db.commit()

    breakdown = WeightedScoreBreakdown(
        overall_score=eval_result["overall_score"],
        correctness=eval_result["correctness"],
        clarity=eval_result["clarity"],
        depth=eval_result["depth"],
        relevance=eval_result["relevance"],
        communication=eval_result["communication"]
    )

    return EvaluationResponse(
        id=new_result.id,
        session_id=session.id,
        score=eval_result["overall_score"],
        breakdown=breakdown,
        strengths=eval_result["strengths"],
        improvements=eval_result["improvements"],
        feedback_summary=eval_result["feedback_summary"],
        model_answer=eval_result["model_answer"]
    )

@router.post("/session/{session_id}/complete", response_model=SessionResponse)
def complete_session(
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

    session.status = "COMPLETED"
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return SessionResponse.from_orm(session)
