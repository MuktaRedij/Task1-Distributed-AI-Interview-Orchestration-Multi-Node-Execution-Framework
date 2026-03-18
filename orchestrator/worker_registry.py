"""
Worker Registry
Tracks all available worker nodes and their status

Responsibilities:
- Register worker nodes
- Track worker capacity and active tasks
- Maintain worker health status
- Provide worker availability queries
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from threading import Lock
import json
import redis
from config import REDIS_URL

logger = logging.getLogger(__name__)


class WorkerRegistry:
    """
    Centralized registry for tracking worker nodes in the system
    """
    
    # Redis key patterns
    WORKER_KEY_PREFIX = "worker:"
    WORKER_SET_KEY = "workers:all"
    WORKER_HEARTBEAT_KEY = "worker:heartbeat:"
    HEARTBEAT_TIMEOUT = 60  # seconds
    
    def __init__(self):
        """Initialize worker registry"""
        try:
            self.redis_url = REDIS_URL or "redis://localhost:6379/0"
            self.redis_client = self._connect_redis()
            self.local_workers: Dict[str, Dict[str, Any]] = {}
            self.lock = Lock()
            logger.info("Worker Registry initialized")
        except Exception as e:
            logger.error(f"Error initializing Worker Registry: {str(e)}")
            self.redis_client = None
    
    def _connect_redis(self) -> Optional[redis.Redis]:
        """Establish Redis connection"""
        try:
            client = redis.from_url(self.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {str(e)}")
            return None
    
    def register_worker(self, worker_id: str, capacity: int = 4) -> bool:
        """
        Register a new worker node
        
        Args:
            worker_id: Unique worker identifier
            capacity: Maximum concurrent tasks this worker can handle
            
        Returns:
            bool: True if successful
        """
        try:
            worker_data = {
                "worker_id": worker_id,
                "status": "healthy",
                "active_tasks": 0,
                "capacity": capacity,
                "registered_at": datetime.utcnow().isoformat(),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "total_tasks_processed": 0,
                "failed_tasks": 0
            }
            
            with self.lock:
                self.local_workers[worker_id] = worker_data
            
            # Store in Redis
            if self.redis_client:
                key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
                self.redis_client.hset(key, mapping=worker_data)
                self.redis_client.sadd(self.WORKER_SET_KEY, worker_id)
                self.redis_client.expire(key, timedelta(hours=24).total_seconds())
            
            logger.info(f"Registered worker: {worker_id} with capacity {capacity}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering worker: {str(e)}")
            return False
    
    def update_worker_status(self, worker_id: str, status: str) -> bool:
        """
        Update worker health status
        
        Args:
            worker_id: Worker identifier
            status: Status ("healthy", "degraded", "unhealthy")
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                if worker_id not in self.local_workers:
                    logger.warning(f"Worker {worker_id} not found in registry")
                    return False
                
                self.local_workers[worker_id]["status"] = status
                self.local_workers[worker_id]["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in Redis
            if self.redis_client:
                key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
                self.redis_client.hset(key, "status", status)
                self.redis_client.hset(key, "updated_at", datetime.utcnow().isoformat())
            
            logger.info(f"Updated worker {worker_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating worker status: {str(e)}")
            return False
    
    def heartbeat(self, worker_id: str, active_tasks: int) -> bool:
        """
        Process worker heartbeat signal
        
        Args:
            worker_id: Worker identifier
            active_tasks: Current number of active tasks on worker
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                if worker_id not in self.local_workers:
                    logger.warning(f"Received heartbeat from unknown worker: {worker_id}")
                    return False
                
                self.local_workers[worker_id]["active_tasks"] = active_tasks
                self.local_workers[worker_id]["last_heartbeat"] = datetime.utcnow().isoformat()
                self.local_workers[worker_id]["status"] = "healthy"
            
            # Update in Redis
            if self.redis_client:
                key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
                self.redis_client.hset(key, "active_tasks", active_tasks)
                self.redis_client.hset(key, "last_heartbeat", datetime.utcnow().isoformat())
                self.redis_client.hset(key, "status", "healthy")
                
                # Also store heartbeat timestamp
                hb_key = f"{self.WORKER_HEARTBEAT_KEY}{worker_id}"
                self.redis_client.setex(hb_key, self.HEARTBEAT_TIMEOUT, "ok")
            
            logger.debug(f"Heartbeat from {worker_id}: {active_tasks} active tasks")
            return True
            
        except Exception as e:
            logger.error(f"Error processing heartbeat: {str(e)}")
            return False
    
    def increment_active_tasks(self, worker_id: str) -> bool:
        """Increment active task count for a worker"""
        try:
            with self.lock:
                if worker_id not in self.local_workers:
                    return False
                self.local_workers[worker_id]["active_tasks"] += 1
            
            if self.redis_client:
                key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
                self.redis_client.hincrby(key, "active_tasks", 1)
            
            return True
        except Exception as e:
            logger.error(f"Error incrementing active tasks: {str(e)}")
            return False
    
    def decrement_active_tasks(self, worker_id: str) -> bool:
        """Decrement active task count for a worker"""
        try:
            with self.lock:
                if worker_id not in self.local_workers:
                    return False
                current = self.local_workers[worker_id]["active_tasks"]
                self.local_workers[worker_id]["active_tasks"] = max(0, current - 1)
                self.local_workers[worker_id]["total_tasks_processed"] += 1
            
            if self.redis_client:
                key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
                self.redis_client.hincrby(key, "active_tasks", -1)
                self.redis_client.hincrby(key, "total_tasks_processed", 1)
            
            return True
        except Exception as e:
            logger.error(f"Error decrementing active tasks: {str(e)}")
            return False
    
    def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get worker details"""
        with self.lock:
            return self.local_workers.get(worker_id)
    
    def get_all_workers(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered workers"""
        with self.lock:
            return dict(self.local_workers)
    
    def get_available_workers(self) -> List[Dict[str, Any]]:
        """
        Get workers that are healthy and have capacity
        
        Returns:
            list: Available worker details
        """
        available = []
        with self.lock:
            for worker in self.local_workers.values():
                if worker["status"] == "healthy" and worker["active_tasks"] < worker["capacity"]:
                    available.append(worker)
        
        return available
    
    def get_least_loaded_worker(self) -> Optional[Dict[str, Any]]:
        """
        Get the worker with the lowest active task count
        
        Returns:
            dict: Least loaded worker or None if none available
        """
        available = self.get_available_workers()
        if not available:
            return None
        
        # Sort by active_tasks and return the one with fewest
        return min(available, key=lambda w: w["active_tasks"])
    
    def get_worker_statistics(self) -> Dict[str, Any]:
        """Get overall worker registry statistics"""
        with self.lock:
            total_workers = len(self.local_workers)
            healthy_workers = sum(1 for w in self.local_workers.values() if w["status"] == "healthy")
            total_capacity = sum(w["capacity"] for w in self.local_workers.values())
            total_active_tasks = sum(w["active_tasks"] for w in self.local_workers.values())
            total_processed = sum(w.get("total_tasks_processed", 0) for w in self.local_workers.values())
            
            return {
                "total_workers": total_workers,
                "healthy_workers": healthy_workers,
                "unhealthy_workers": total_workers - healthy_workers,
                "total_capacity": total_capacity,
                "total_active_tasks": total_active_tasks,
                "capacity_utilization": round((total_active_tasks / total_capacity * 100) if total_capacity > 0 else 0, 2),
                "total_tasks_processed": total_processed
            }
    
    def detect_unhealthy_workers(self) -> List[str]:
        """
        Detect workers that haven't sent heartbeat recently
        
        Returns:
            list: List of unhealthy worker IDs
        """
        unhealthy = []
        timeout_threshold = datetime.utcnow() - timedelta(seconds=self.HEARTBEAT_TIMEOUT)
        
        with self.lock:
            for worker_id, worker in self.local_workers.items():
                last_hb = datetime.fromisoformat(worker["last_heartbeat"])
                if last_hb < timeout_threshold:
                    unhealthy.append(worker_id)
                    worker["status"] = "unhealthy"
        
        return unhealthy
    
    def deregister_worker(self, worker_id: str) -> bool:
        """Remove a worker from the registry"""
        try:
            with self.lock:
                if worker_id in self.local_workers:
                    del self.local_workers[worker_id]
            
            if self.redis_client:
                key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
                self.redis_client.delete(key)
                self.redis_client.srem(self.WORKER_SET_KEY, worker_id)
            
            logger.info(f"Deregistered worker: {worker_id}")
            return True
        except Exception as e:
            logger.error(f"Error deregistering worker: {str(e)}")
            return False
