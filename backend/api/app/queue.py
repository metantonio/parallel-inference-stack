from celery import Celery
from redis import Redis
from typing import Dict, Any, Optional
import json
import logging
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "inference_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=270,  # 4.5 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)

# Redis client for queue management
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Priority queue names
PRIORITY_QUEUES = {
    "high": "inference:queue:high",
    "normal": "inference:queue:normal",
    "low": "inference:queue:low"
}

# ============================================
# Queue Management Functions
# ============================================

async def enqueue_inference_task(
    task_id: str,
    data: Dict[str, Any],
    priority: str = "normal",
    model_version: Optional[str] = None,
    timeout: int = 60,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enqueue an inference task
    
    Args:
        task_id: Unique task identifier
        data: Input data for inference
        priority: Task priority (high, normal, low)
        model_version: Specific model version to use
        timeout: Task timeout in seconds
        user_id: User ID for tracking
    
    Returns:
        Queue information (position, estimated wait time)
    """
    try:
        # Prepare task payload
        task_payload = {
            "task_id": task_id,
            "data": data,
            "model_version": model_version,
            "timeout": timeout,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Get queue name based on priority
        queue_name = PRIORITY_QUEUES.get(priority, PRIORITY_QUEUES["normal"])
        
        # Add to Redis queue
        redis_client.rpush(queue_name, json.dumps(task_payload))
        
        # Store task metadata
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "queued",
                "priority": priority,
                "created_at": task_payload["created_at"]
            }
        )
        redis_client.expire(f"task:{task_id}", 86400)  # 24 hour TTL
        
        # Get queue position
        queue_position = redis_client.llen(queue_name)
        
        # Estimate wait time (rough estimate: 2 seconds per task)
        estimated_wait_time = queue_position * 2
        
        # Send task to Celery
        inference_task.apply_async(
            args=[task_payload],
            task_id=task_id,
            priority={"high": 9, "normal": 5, "low": 1}[priority],
            queue=priority
        )
        
        logger.info(f"Task {task_id} enqueued with priority {priority}")
        
        return {
            "queue_position": queue_position,
            "estimated_wait_time": estimated_wait_time
        }
        
    except Exception as e:
        logger.error(f"Error enqueueing task {task_id}: {str(e)}")
        raise

async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get current status of a task"""
    try:
        task_data = redis_client.hgetall(f"task:{task_id}")
        
        if not task_data:
            return {"status": "not_found"}
        
        # Check Celery task status
        celery_result = celery_app.AsyncResult(task_id)
        
        return {
            "status": task_data.get("status", "unknown"),
            "celery_status": celery_result.status,
            "created_at": task_data.get("created_at"),
            "started_at": task_data.get("started_at"),
            "completed_at": task_data.get("completed_at"),
            "error": task_data.get("error")
        }
        
    except Exception as e:
        logger.error(f"Error getting task status {task_id}: {str(e)}")
        raise

async def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
    """Get result of a completed task"""
    try:
        celery_result = celery_app.AsyncResult(task_id)
        
        if celery_result.ready():
            return celery_result.result
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting task result {task_id}: {str(e)}")
        raise

async def cancel_task(task_id: str):
    """Cancel a pending task"""
    try:
        # Revoke Celery task
        celery_app.control.revoke(task_id, terminate=True)
        
        # Update task status
        redis_client.hset(f"task:{task_id}", "status", "cancelled")
        
        logger.info(f"Task {task_id} cancelled")
        
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        raise

async def get_queue_metrics() -> Dict[str, Any]:
    """Get current queue metrics"""
    try:
        metrics = {
            "queues": {},
            "total_queued": 0,
            "total_processing": 0,
            "total_completed_24h": 0
        }
        
        # Get queue depths
        for priority, queue_name in PRIORITY_QUEUES.items():
            queue_depth = redis_client.llen(queue_name)
            metrics["queues"][priority] = queue_depth
            metrics["total_queued"] += queue_depth
        
        # Get processing count (active Celery tasks)
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        if active_tasks:
            metrics["total_processing"] = sum(len(tasks) for tasks in active_tasks.values())
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting queue metrics: {str(e)}")
        raise

# ============================================
# Celery Tasks
# ============================================

@celery_app.task(bind=True, name="inference_task")
def inference_task(self, task_payload: Dict[str, Any]):
    """
    Main inference task executed by Celery workers
    
    This task:
    1. Updates task status to 'processing'
    2. Routes to Ollama (local mode) or Ray Serve (production mode)
    3. Waits for result
    4. Updates task status to 'completed' or 'failed'
    """
    task_id = task_payload["task_id"]
    
    try:
        # Update status to processing
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "processing",
                "started_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Processing task {task_id} in {settings.INFERENCE_MODE} mode")
        
        # Route based on inference mode
        if settings.is_local_mode:
            # Local mode: Use Ollama
            result = _run_ollama_inference(task_payload)
        elif settings.is_vllm_mode:
            # vLLM mode: Use vLLM worker
            result = _run_vllm_inference(task_payload)
        else:
            # Production mode: Use Ray Serve
            result = _run_ray_inference(task_payload)
        
        # Update status to completed
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Task {task_id} completed successfully")
        
        return result
        
    except Exception as e:
        # Update status to failed
        redis_client.hset(
            f"task:{task_id}",
            mapping={
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )
        
        logger.error(f"Task {task_id} failed: {str(e)}")
        raise


def _run_ollama_inference(task_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run inference using Ollama (local mode)
    
    Args:
        task_payload: Task payload with input data
    
    Returns:
        Inference result
    """
    import asyncio
    import sys
    
    # Add workers directory to path
    import os
    workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
    if workers_path not in sys.path:
        sys.path.insert(0, workers_path)
    
    from ollama_worker import get_ollama_worker
    
    async def run_inference():
        worker = await get_ollama_worker(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        return await worker.inference(task_payload["data"])
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_inference())
        return result
    finally:
        loop.close()


def _run_vllm_inference(task_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run inference using vLLM (GPU batching mode)
    
    Args:
        task_payload: Task payload with input data
    
    Returns:
        Inference result
    """
    import asyncio
    import sys
    
    # Add workers directory to path
    import os
    workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
    if workers_path not in sys.path:
        sys.path.insert(0, workers_path)
    
    from vllm_worker import get_vllm_worker
    
    async def run_inference():
        worker = await get_vllm_worker(
            base_url=settings.VLLM_BASE_URL,
            model=settings.VLLM_MODEL,
            timeout=settings.VLLM_TIMEOUT
        )
        return await worker.inference(task_payload["data"])
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(run_inference())
        return result
    finally:
        loop.close()


def _run_ray_inference(task_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run inference using Ray Serve (production mode)
    
    Args:
        task_payload: Task payload with input data
    
    Returns:
        Inference result
    """
    import ray
    from ray import serve
    
    if not ray.is_initialized():
        ray.init(address=settings.RAY_ADDRESS)
    
    # Get model deployment handle
    model_handle = serve.get_deployment("InferenceModel").get_handle()
    
    # Run inference
    result = ray.get(model_handle.remote(task_payload["data"]))
    
    return result

