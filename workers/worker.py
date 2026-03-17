"""
Celery Worker Node
Starts worker service that processes interview tasks from the Redis queue

This file can be run directly or used as reference for worker deployment
"""

import logging
import subprocess
import sys
from config import WORKER_CONCURRENCY

logger = logging.getLogger(__name__)


def start_worker(concurrency: int = WORKER_CONCURRENCY, loglevel: str = "info"):
    """
    Start a Celery worker node
    
    The worker will:
    - Connect to Redis message broker
    - Listen for interview processing tasks
    - Process multiple sessions concurrently
    - Store results in database
    - Support graceful shutdown
    
    Args:
        concurrency: Number of concurrent worker processes (default: 4)
        loglevel: Logging level (debug, info, warning, error)
        
    Example:
        To start a worker with 4 concurrent processes:
        celery -A workers.celery_app worker --loglevel=info --concurrency=4
        
        To start a worker with specific hostname:
        celery -A workers.celery_app worker --loglevel=info --concurrency=4 -n worker1@%h
        
        To start multiple workers on different nodes:
        # Node 1:
        celery -A workers.celery_app worker -n worker1@%h --loglevel=info
        # Node 2:
        celery -A workers.celery_app worker -n worker2@%h --loglevel=info
    """
    logger.info(f"Starting Celery worker with concurrency={concurrency}")
    logger.info("Worker is ready to process interview sessions from the queue")
    
    # Build the Celery command
    command = [
        "celery",
        "-A", "workers.celery_app",
        "worker",
        f"--loglevel={loglevel}",
        f"--concurrency={concurrency}",
        "--time-limit=1800",  # 30 minutes hard limit per task
        "--soft-time-limit=1500",  # 25 minutes soft limit per task
    ]
    
    try:
        # Run the worker process
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        logger.error(f"Worker process failed: {e}")
        sys.exit(1)


def start_worker_with_autoscale(concurrency: int = WORKER_CONCURRENCY, loglevel: str = "info"):
    """
    Start a Celery worker with autoscaling enabled
    
    Autoscaling allows the worker to dynamically adjust the number of 
    concurrent processes based on workload.
    
    Args:
        concurrency: Maximum number of concurrent processes
        loglevel: Logging level
        
    Example:
        celery -A workers.celery_app worker --loglevel=info --autoscale=10,3
        This will scale between 3 and 10 processes based on load
    """
    logger.info(f"Starting Celery worker with autoscaling (max concurrency={concurrency})")
    
    # min_processes = concurrency / 2
    min_processes = max(1, concurrency // 2)
    max_processes = concurrency
    
    command = [
        "celery",
        "-A", "workers.celery_app",
        "worker",
        f"--loglevel={loglevel}",
        f"--autoscale={max_processes},{min_processes}",
        "--time-limit=1800",
        "--soft-time-limit=1500",
    ]
    
    try:
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
        sys.exit(0)


def get_worker_statistics():
    """
    Get statistics about the worker
    
    Returns:
        dict: Worker statistics including active tasks, processed tasks, etc.
    """
    from workers.celery_app import celery_app
    
    stats = celery_app.control.inspect().stats()
    active = celery_app.control.inspect().active()
    
    return {
        "stats": stats,
        "active_tasks": active
    }


if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse command line arguments
    concurrency = int(sys.argv[1]) if len(sys.argv) > 1 else WORKER_CONCURRENCY
    loglevel = sys.argv[2] if len(sys.argv) > 2 else "info"
    autoscale = sys.argv[3] == "autoscale" if len(sys.argv) > 3 else False
    
    if autoscale:
        start_worker_with_autoscale(concurrency, loglevel)
    else:
        start_worker(concurrency, loglevel)
