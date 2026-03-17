"""
Celery Tasks for Interview Processing
Defines tasks executed by worker nodes
"""

from workers.celery_app import celery_app
from workers.video_pipeline import run_video_analysis
from workers.audio_pipeline import run_audio_analysis
from workers.evaluation_pipeline import evaluate_answers
from database.db import SessionLocal
from database.models import InterviewSession
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_interview_session(self, session_id):
    """
    Main interview processing task
    
    Responsibilities:
    1. Start video monitoring pipeline
    2. Start audio monitoring pipeline
    3. Run answer evaluation
    4. Calculate final risk score
    5. Store results in database
    
    Args:
        session_id: Unique identifier for the interview session
        
    Returns:
        dict: Results containing risk score and analysis data
    """
    try:
        logger.info(f"Processing interview session: {session_id}")
        
        # Run video analysis
        logger.info(f"Starting video analysis for session {session_id}")
        video_result = run_video_analysis(session_id)
        
        # Run audio analysis
        logger.info(f"Starting audio analysis for session {session_id}")
        audio_result = run_audio_analysis(session_id)
        
        # Run answer evaluation
        logger.info(f"Starting answer evaluation for session {session_id}")
        evaluation_result = evaluate_answers(session_id)
        
        # Calculate risk score
        risk_score = calculate_risk_score(video_result, audio_result, evaluation_result)
        
        # Store results in database
        store_results(session_id, video_result, audio_result, evaluation_result, risk_score)
        
        logger.info(f"Completed processing for session {session_id} with risk score: {risk_score}")
        
        return {
            "session_id": session_id,
            "video_result": video_result,
            "audio_result": audio_result,
            "evaluation_result": evaluation_result,
            "risk_score": risk_score,
            "status": "completed"
        }
        
    except Exception as exc:
        logger.error(f"Error processing session {session_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def calculate_risk_score(video_result, audio_result, evaluation_result):
    """
    Calculate overall risk score from pipeline results
    
    Args:
        video_result: Results from video analysis pipeline
        audio_result: Results from audio analysis pipeline
        evaluation_result: Results from answer evaluation pipeline
        
    Returns:
        float: Combined risk score (0-100)
    """
    # Weighted risk scoring
    video_weight = 0.3
    audio_weight = 0.3
    evaluation_weight = 0.4
    
    video_risk = video_result.get("risk_score", 0) * video_weight
    audio_risk = audio_result.get("risk_score", 0) * audio_weight
    evaluation_risk = evaluation_result.get("risk_score", 0) * evaluation_weight
    
    final_risk = video_risk + audio_risk + evaluation_risk
    return round(final_risk, 2)


def store_results(session_id, video_result, audio_result, evaluation_result, risk_score):
    """
    Store interview processing results in database
    
    Args:
        session_id: Interview session identifier
        video_result: Video analysis results
        audio_result: Audio analysis results
        evaluation_result: Answer evaluation results
        risk_score: Calculated risk score
    """
    session = SessionLocal()
    try:
        # Update interview session record
        interview = session.query(InterviewSession).filter(
            InterviewSession.session_id == session_id
        ).first()
        
        if interview:
            interview.risk_score = risk_score
            interview.video_analysis = video_result
            interview.audio_analysis = audio_result
            interview.evaluation_analysis = evaluation_result
            interview.status = "completed"
            
            session.commit()
            logger.info(f"Stored results for session {session_id}")
        else:
            logger.warning(f"Interview session {session_id} not found")
            
    except Exception as e:
        logger.error(f"Error storing results for session {session_id}: {str(e)}")
        session.rollback()
    finally:
        session.close()
