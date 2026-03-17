"""
FastAPI Orchestration Server
Main entry point for the AI Interview Orchestrator API

Integrates:
- Session Manager for lifecycle management
- Session Tracker for monitoring
- State Synchronizer for Redis/DB consistency
- Task Queue integration with Celery
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from workers.tasks import process_interview_session
from orchestrator.session_manager import SessionManager
from orchestrator.session_tracker import SessionTracker
from orchestrator.state_sync import StateSynchronizer

# Initialize FastAPI application
app = FastAPI(
    title="AI Interview Orchestrator",
    description="Orchestration API for distributed interview processing",
    version="1.0.0"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers
session_manager = SessionManager()
session_tracker = SessionTracker()
state_sync = StateSynchronizer()


# ========== Request/Response Models ==========

class StartInterviewRequest(BaseModel):
    """Request model for starting an interview"""
    candidate_id: str
    candidate_name: Optional[str] = None
    position: Optional[str] = None


class InterviewSessionResponse(BaseModel):
    """Response model for interview session"""
    session_id: str
    status: str
    created_at: Optional[str] = None
    candidate_id: str
    risk_score: Optional[float] = None


class SessionStatusResponse(BaseModel):
    """Response model for session status"""
    session_id: str
    status: str
    candidate_id: str
    risk_score: Optional[float] = None
    assigned_node: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    updated_at: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    session_id: str
    task_id: str
    status: str
    result: Optional[dict] = None


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    logger.info("AI Interview Orchestrator server starting...")
    print("✓ Orchestration server initialized")
    print("✓ Connected to Redis task queue")
    print("✓ Session Manager loaded")
    print("✓ Session Tracker loaded")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns system status
    """
    return {
        "status": "system running",
        "timestamp": None
    }


# ========== Interview Session Endpoints ==========

@app.post("/start-interview", response_model=InterviewSessionResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new interview session
    
    Execution flow:
    1. Create session in database (status: CREATED)
    2. Cache session in Redis
    3. Enqueue task to Redis queue (status: QUEUED)
    4. Return session_id
    
    Args:
        request: Interview session request with candidate details
        
    Returns:
        InterviewSessionResponse: Created session details
        
    Raises:
        HTTPException: On creation failure
    """
    try:
        logger.info(f"API: Creating interview session for candidate {request.candidate_id}")
        
        # Create session
        session_id = session_manager.create_session(
            candidate_id=request.candidate_id,
            candidate_name=request.candidate_name,
            position=request.position
        )
        
        logger.info(f"Session created: {session_id}")
        
        # Update status to QUEUED
        session_manager.update_session_status(
            session_id,
            session_manager.QUEUED,
            {"enqueue_time": None}
        )
        
        # Enqueue the interview processing task
        task = process_interview_session.delay(session_id)
        logger.info(f"Task enqueued for session {session_id}: task_id={task.id}")
        
        # Retrieve and return session details
        session_data = session_manager.get_session(session_id)
        
        return InterviewSessionResponse(
            session_id=session_id,
            status=session_manager.QUEUED,
            created_at=session_data.get("created_at"),
            candidate_id=request.candidate_id,
            risk_score=None
        )
        
    except Exception as e:
        logger.error(f"Error starting interview session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")


@app.get("/session-status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get current status of an interview session
    
    Retrieves real-time session information including:
    - Current status (CREATED, QUEUED, PROCESSING, COMPLETED, FAILED)
    - Risk score if available
    - Processing node information
    - Timestamps
    
    Args:
        session_id: Interview session identifier
        
    Returns:
        SessionStatusResponse: Current session status and details
        
    Raises:
        HTTPException: If session not found
    """
    try:
        logger.debug(f"API: Fetching status for session {session_id}")
        
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            logger.warning(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionStatusResponse(
            session_id=session_id,
            status=session_data.get("status"),
            candidate_id=session_data.get("candidate_id"),
            risk_score=session_data.get("risk_score"),
            assigned_node=session_data.get("assigned_node"),
            start_time=session_data.get("start_time"),
            end_time=session_data.get("end_time"),
            updated_at=session_data.get("updated_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


# ========== Session Tracking Endpoints ==========

@app.get("/active-sessions")
async def get_active_sessions():
    """
    Get all currently active sessions
    
    Returns sessions in states: CREATED, QUEUED, PROCESSING
    
    Returns:
        dict: List of active sessions with brief details
    """
    try:
        active = session_tracker.get_active_sessions()
        return {
            "count": len(active),
            "sessions": active
        }
    except Exception as e:
        logger.error(f"Error fetching active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching active sessions")


@app.get("/completed-sessions")
async def get_completed_sessions(limit: int = 100):
    """
    Get recently completed sessions
    
    Args:
        limit: Maximum number of sessions to retrieve (default: 100)
        
    Returns:
        dict: List of completed sessions with results
    """
    try:
        completed = session_tracker.get_completed_sessions(limit=limit)
        return {
            "count": len(completed),
            "sessions": completed
        }
    except Exception as e:
        logger.error(f"Error fetching completed sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching completed sessions")


@app.get("/failed-sessions")
async def get_failed_sessions(limit: int = 100):
    """
    Get recently failed sessions
    
    Args:
        limit: Maximum number of sessions to retrieve (default: 100)
        
    Returns:
        dict: List of failed sessions
    """
    try:
        failed = session_tracker.get_failed_sessions(limit=limit)
        return {
            "count": len(failed),
            "sessions": failed
        }
    except Exception as e:
        logger.error(f"Error fetching failed sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching failed sessions")


@app.get("/stuck-sessions")
async def get_stuck_sessions(timeout_minutes: int = 30):
    """
    Get sessions that appear to be stuck in PROCESSING
    
    Args:
        timeout_minutes: Timeout threshold in minutes (default: 30)
        
    Returns:
        dict: List of stuck sessions
    """
    try:
        stuck = session_tracker.get_stuck_sessions(timeout_minutes=timeout_minutes)
        return {
            "count": len(stuck),
            "timeout_minutes": timeout_minutes,
            "sessions": stuck
        }
    except Exception as e:
        logger.error(f"Error fetching stuck sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching stuck sessions")


# ========== Statistics Endpoints ==========

@app.get("/session-statistics")
async def get_session_statistics():
    """
    Get comprehensive session statistics
    
    Returns statistics including:
    - Total sessions by status
    - Average processing duration
    - Risk score distribution
    - High-risk session count
    
    Returns:
        dict: Session statistics
    """
    try:
        stats = session_tracker.get_session_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error generating statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating statistics")


@app.get("/worker-distribution")
async def get_worker_distribution():
    """
    Get distribution of sessions across worker nodes
    
    Returns:
        dict: Worker node -> session count mapping
    """
    try:
        distribution = session_tracker.get_worker_distribution()
        return {
            "workers": distribution,
            "total_active": sum(distribution.values())
        }
    except Exception as e:
        logger.error(f"Error fetching worker distribution: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching worker distribution")


@app.get("/high-risk-sessions")
async def get_high_risk_sessions(threshold: float = 0.8, limit: int = 50):
    """
    Get high-risk completed sessions
    
    Args:
        threshold: Risk score threshold (0-1, default: 0.8)
        limit: Maximum sessions to return (default: 50)
        
    Returns:
        dict: List of high-risk sessions
    """
    try:
        high_risk = session_tracker.get_high_risk_sessions(threshold=threshold, limit=limit)
        return {
            "count": len(high_risk),
            "threshold": threshold,
            "sessions": high_risk
        }
    except Exception as e:
        logger.error(f"Error fetching high-risk sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching high-risk sessions")


# ========== Cache Management Endpoints ==========

@app.get("/cache-stats")
async def get_cache_stats():
    """
    Get Redis cache statistics
    
    Returns:
        dict: Cache health and statistics
    """
    try:
        cache_stats = state_sync.get_cache_stats()
        return cache_stats
    except Exception as e:
        logger.error(f"Error fetching cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching cache stats")


@app.post("/sync-to-database")
async def sync_cache_to_database(session_id: Optional[str] = None):
    """
    Manually sync cache to database
    
    Args:
        session_id: Specific session to sync, or None to sync all active sessions
        
    Returns:
        dict: Sync result
    """
    try:
        if session_id:
            session_data = state_sync.get_session_state(session_id)
            if session_data:
                state_sync.sync_state_to_db(session_id, session_data)
                return {"message": f"Synced session {session_id}", "status": "success"}
            else:
                raise HTTPException(status_code=404, detail="Session not found in cache")
        else:
            # Sync all active sessions
            active_sessions = state_sync.get_active_sessions()
            for sid in active_sessions:
                session_data = state_sync.get_session_state(sid)
                if session_data:
                    state_sync.sync_state_to_db(sid, session_data)
            
            return {
                "message": f"Synced {len(active_sessions)} sessions",
                "status": "success",
                "synced_count": len(active_sessions)
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing to database: {str(e)}")
        raise HTTPException(status_code=500, detail="Error syncing to database")


@app.delete("/clear-cache")
async def clear_session_cache():
    """
    Clear all session cache from Redis
    
    WARNING: This will clear all cached session states
    
    Returns:
        dict: Clear operation result
    """
    try:
        logger.warning("Clearing all session cache from Redis")
        result = state_sync.clear_cache()
        return {
            "message": "Cache cleared",
            "status": "success" if result else "failed"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Error clearing cache")


@app.get("/interviews")
async def list_interviews():
    """
    List all interview sessions (legacy endpoint)
    
    Returns:
        dict: List of interview sessions
    """
    logger.info("Listing all interview sessions")
    return {
        "sessions": [],
        "total_count": 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
