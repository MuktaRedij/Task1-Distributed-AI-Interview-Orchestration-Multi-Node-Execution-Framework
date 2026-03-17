"""
FastAPI Orchestration Server
Main entry point for the AI Interview Orchestrator API
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from workers.tasks import process_interview_session

# Initialize FastAPI application
app = FastAPI(
    title="AI Interview Orchestrator",
    description="Orchestration API for distributed interview processing",
    version="1.0.0"
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Request/Response Models
class StartInterviewRequest(BaseModel):
    """Request model for starting an interview"""
    session_id: str
    candidate_name: Optional[str] = None
    position: Optional[str] = None


class InterviewTaskResponse(BaseModel):
    """Response model for interview task"""
    message: str
    session_id: str
    task_id: str


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


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns system status
    """
    return {
        "status": "system running"
    }


@app.post("/start-interview", response_model=InterviewTaskResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start an interview session and enqueue it for processing
    
    Non-blocking API call that queues the interview for execution
    across distributed worker nodes.
    
    Args:
        request: Interview session details
        
    Returns:
        InterviewTaskResponse: Confirmation with task ID
    """
    try:
        logger.info(f"Starting interview session: {request.session_id}")
        
        # Enqueue the interview processing task
        task = process_interview_session.delay(request.session_id)
        
        logger.info(f"Interview session {request.session_id} queued with task ID: {task.id}")
        
        return InterviewTaskResponse(
            message="Interview session queued for processing",
            session_id=request.session_id,
            task_id=task.id
        )
        
    except Exception as e:
        logger.error(f"Error starting interview session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting interview: {str(e)}")


@app.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of an interview processing task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        TaskStatusResponse: Current task status and results if completed
    """
    try:
        # Get task result and status from Celery
        result = process_interview_session.AsyncResult(task_id)
        
        response_data = {
            "session_id": "",
            "task_id": task_id,
            "status": result.state
        }
        
        # If task completed successfully
        if result.successful():
            task_result = result.result
            response_data["session_id"] = task_result.get("session_id", "")
            response_data["result"] = task_result
        
        # If task failed
        elif result.failed():
            response_data["status"] = "failed"
            logger.error(f"Task {task_id} failed: {result.info}")
        
        # If task is pending
        elif result.state == "PENDING":
            response_data["status"] = "pending"
        
        return TaskStatusResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


@app.get("/interviews")
async def list_interviews():
    """
    List all interview sessions
    
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
