"""
Celery Tasks for Interview Processing
Defines tasks executed by worker nodes

Execution Flow:
1. Retrieve interview session from database
2. Update status to "processing"
3. Run video analysis pipeline
4. Run audio analysis pipeline
5. Run answer evaluation pipeline
6. Generate risk report using RiskScoringEngine
7. Store results in database
8. Update status to "completed"
"""

from workers.celery_app import celery_app
from workers.video_pipeline import run_video_analysis
from workers.audio_pipeline import run_audio_analysis
from workers.evaluation_pipeline import evaluate_answers
from workers.risk_engine import RiskScoringEngine
from database.db import SessionLocal
from database.models import InterviewSession
from datetime import datetime
import logging
import socket

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_interview_session(self, session_id):
    """
    Main interview processing task executed by worker nodes
    
    This is the primary task that orchestrates all interview analysis pipelines.
    
    Responsibilities:
    1. Update session status to "processing" with worker node info
    2. Run video monitoring pipeline
    3. Run audio monitoring pipeline
    4. Run answer evaluation pipeline
    5. Generate comprehensive risk report
    6. Store all results in database
    7. Update session status to "completed"
    
    Args:
        session_id: Unique identifier for the interview session
        
    Returns:
        dict: Results containing all analysis data and risk report
        
    Raises:
        Exception: On processing failure, task will retry with exponential backoff
    """
    session = SessionLocal()
    
    try:
        logger.info(f"Worker {socket.gethostname()} starting interview session processing: {session_id}")
        
        # Retrieve interview session from database
        interview = session.query(InterviewSession).filter(
            InterviewSession.session_id == session_id
        ).first()
        
        if not interview:
            logger.error(f"Interview session {session_id} not found in database")
            raise ValueError(f"Interview session {session_id} not found")
        
        # Update session status to "processing"
        interview.status = "processing"
        interview.assigned_node = socket.gethostname()
        interview.start_time = datetime.utcnow()
        session.commit()
        logger.info(f"Updated session {session_id} status to 'processing'")
        
        # ========== EXECUTION FLOW ==========
        
        # Step 1: Run video analysis
        logger.info(f"Step 1/3: Starting video analysis for session {session_id}")
        video_result = run_video_analysis(session_id)
        logger.info(f"Video analysis completed: {video_result}")
        
        # Step 2: Run audio analysis
        logger.info(f"Step 2/3: Starting audio analysis for session {session_id}")
        audio_result = run_audio_analysis(session_id)
        logger.info(f"Audio analysis completed: {audio_result}")
        
        # Step 3: Run answer evaluation
        logger.info(f"Step 3/3: Starting answer evaluation for session {session_id}")
        evaluation_result = evaluate_answers(session_id)
        logger.info(f"Answer evaluation completed: {evaluation_result}")
        
        # Step 4: Generate comprehensive risk report
        logger.info(f"Generating risk report for session {session_id}")
        risk_report = RiskScoringEngine.generate_risk_report(
            session_id, 
            video_result, 
            audio_result, 
            evaluation_result
        )
        
        final_risk_score = risk_report["final_risk_score"]
        risk_classification = risk_report["risk_classification"]
        logger.info(f"Risk report generated: {risk_classification} (score: {final_risk_score})")
        
        # Step 5: Store results in database
        logger.info(f"Storing results for session {session_id}")
        interview.risk_score = final_risk_score
        interview.video_analysis = video_result
        interview.audio_analysis = audio_result
        interview.evaluation_analysis = evaluation_result
        interview.status = "completed"
        interview.end_time = datetime.utcnow()
        session.commit()
        logger.info(f"Results stored successfully for session {session_id}")
        
        # Prepare response
        result = {
            "session_id": session_id,
            "status": "completed",
            "video_result": video_result,
            "audio_result": audio_result,
            "evaluation_result": evaluation_result,
            "risk_report": risk_report,
            "final_risk_score": final_risk_score,
            "risk_classification": risk_classification,
            "processed_by": socket.gethostname(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully completed processing for session {session_id}")
        return result
        
    except Exception as exc:
        logger.error(f"Error processing session {session_id}: {str(exc)}", exc_info=True)
        
        # Update session status to failed
        try:
            interview = session.query(InterviewSession).filter(
                InterviewSession.session_id == session_id
            ).first()
            if interview:
                interview.status = "failed"
                session.commit()
        except Exception as e:
            logger.error(f"Error updating status to failed: {str(e)}")
        
        # Retry with exponential backoff (2^retries seconds)
        retry_delay = 2 ** self.request.retries
        logger.info(f"Retrying task in {retry_delay} seconds (attempt {self.request.retries + 1}/3)")
        raise self.retry(exc=exc, countdown=retry_delay)
        
    finally:
        session.close()


def update_session_status(session_id: str, status: str, end_time: bool = False):
    """
    Update interview session status in database
    
    Args:
        session_id: Interview session identifier
        status: New status (pending, processing, completed, failed)
        end_time: Whether to set end_time to current timestamp
    """
    session = SessionLocal()
    try:
        interview = session.query(InterviewSession).filter(
            InterviewSession.session_id == session_id
        ).first()
        
        if interview:
            interview.status = status
            if end_time:
                interview.end_time = datetime.utcnow()
            session.commit()
            logger.info(f"Updated session {session_id} status to '{status}'")
        else:
            logger.warning(f"Session {session_id} not found for status update")
            
    except Exception as e:
        logger.error(f"Error updating session status: {str(e)}")
        session.rollback()
    finally:
        session.close()
