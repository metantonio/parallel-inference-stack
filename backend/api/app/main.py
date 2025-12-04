from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import asyncio
import logging
from datetime import datetime
import uuid

from .config import settings
from .database import get_db, SessionLocal
from .models import InferenceRequest, TaskStatus
from .queue import enqueue_inference_task, get_task_status, get_task_result
from .auth import get_current_user, User, Token, create_access_token, get_user, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Inference API",
    description="Parallel GPU-based AI inference system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Request/Response Models
# ============================================

class InferenceRequestPayload(BaseModel):
    """Request payload for inference"""
    data: Dict[str, Any] = Field(..., description="Input data for inference")
    priority: str = Field("normal", description="Priority: high, normal, low")
    model_version: Optional[str] = Field(None, description="Specific model version")
    batch_size: Optional[int] = Field(None, description="Override batch size")
    timeout: Optional[int] = Field(60, description="Timeout in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {"text": "Hello, world!"},
                "priority": "normal",
                "model_version": "v1.0.0",
                "timeout": 60
            }
        }

class InferenceResponsePayload(BaseModel):
    """Response payload for inference submission"""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    estimated_wait_time: Optional[int] = Field(None, description="Estimated wait time in seconds")
    queue_position: Optional[int] = Field(None, description="Position in queue")
    
class TaskResultPayload(BaseModel):
    """Response payload for task result"""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None

# ============================================
# Health Check Endpoints
# ============================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancer"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check(db: SessionLocal = Depends(get_db)):
    """Detailed health check with component status"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        from .queue import redis_client
        redis_client.ping()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ray cluster
    try:
        import ray
        if ray.is_initialized():
            health_status["components"]["ray"] = "healthy"
        else:
            health_status["components"]["ray"] = "not initialized"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["components"]["ray"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

# ============================================
# Auth Endpoints
# ============================================

@app.post("/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    logger.info(f"Endpoint /token called")
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password...",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================
# Inference Endpoints
# ============================================

@app.post("/inference", response_model=InferenceResponsePayload, tags=["Inference"])
async def submit_inference(
    request: InferenceRequestPayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    """
    Submit an inference request
    
    The request is queued and processed asynchronously by GPU workers.
    Returns a task_id that can be used to check status and retrieve results.
    """
    try:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Validate priority
        if request.priority not in ["high", "normal", "low"]:
            raise HTTPException(status_code=400, detail="Invalid priority")
        
        # Create database record
        db_request = InferenceRequest(
            task_id=task_id,
            user_id=current_user.id,
            status=TaskStatus.QUEUED,
            priority=request.priority,
            model_version=request.model_version,
            input_data=request.data,
            created_at=datetime.utcnow()
        )
        db.add(db_request)
        db.commit()
        
        # Enqueue task
        queue_info = await enqueue_inference_task(
            task_id=task_id,
            data=request.data,
            priority=request.priority,
            model_version=request.model_version,
            timeout=request.timeout,
            user_id=current_user.id
        )
        
        logger.info(f"Task {task_id} queued for user {current_user.id}")
        
        return InferenceResponsePayload(
            task_id=task_id,
            status="queued",
            estimated_wait_time=queue_info.get("estimated_wait_time"),
            queue_position=queue_info.get("queue_position")
        )
        
    except Exception as e:
        logger.error(f"Error submitting inference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit inference: {str(e)}")

@app.get("/inference/{task_id}", response_model=TaskResultPayload, tags=["Inference"])
async def get_inference_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    """
    Get inference result by task ID
    
    Returns the current status and result (if completed) of the inference task.
    """
    try:
        # Check database for task
        db_request = db.query(InferenceRequest).filter(
            InferenceRequest.task_id == task_id,
            InferenceRequest.user_id == current_user.id
        ).first()
        
        if not db_request:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get latest status from queue
        task_status = await get_task_status(task_id)
        
        # Update database if status changed
        if task_status["status"] != db_request.status:
            db_request.status = task_status["status"]
            if task_status["status"] == TaskStatus.PROCESSING:
                db_request.started_at = datetime.utcnow()
            elif task_status["status"] in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                db_request.completed_at = datetime.utcnow()
            db.commit()
        
        # Get result if completed
        result = None
        error = None
        if task_status["status"] == TaskStatus.COMPLETED:
            result = await get_task_result(task_id)
        elif task_status["status"] == TaskStatus.FAILED:
            error = task_status.get("error", "Unknown error")
        
        # Calculate processing time
        processing_time = None
        if db_request.started_at and db_request.completed_at:
            processing_time = (db_request.completed_at - db_request.started_at).total_seconds()
        
        return TaskResultPayload(
            task_id=task_id,
            status=task_status["status"],
            result=result,
            error=error,
            created_at=db_request.created_at,
            started_at=db_request.started_at,
            completed_at=db_request.completed_at,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inference result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")

@app.delete("/inference/{task_id}", tags=["Inference"])
async def cancel_inference(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    """
    Cancel a pending inference task
    
    Only tasks in 'queued' status can be cancelled.
    """
    try:
        # Check database for task
        db_request = db.query(InferenceRequest).filter(
            InferenceRequest.task_id == task_id,
            InferenceRequest.user_id == current_user.id
        ).first()
        
        if not db_request:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if db_request.status != TaskStatus.QUEUED:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel task in status: {db_request.status}"
            )
        
        # Cancel task in queue
        from .queue import cancel_task
        await cancel_task(task_id)
        
        # Update database
        db_request.status = TaskStatus.CANCELLED
        db_request.completed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Task {task_id} cancelled by user {current_user.id}")
        
        return {"status": "cancelled", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling inference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")

# ============================================
# Batch Inference Endpoints
# ============================================

@app.post("/inference/batch", tags=["Inference"])
async def submit_batch_inference(
    requests: List[InferenceRequestPayload],
    current_user: User = Depends(get_current_user),
    db: SessionLocal = Depends(get_db)
):
    """
    Submit multiple inference requests as a batch
    
    Returns a list of task IDs for all submitted requests.
    """
    if len(requests) > 100:
        raise HTTPException(status_code=400, detail="Batch size limited to 100 requests")
    
    task_ids = []
    for req in requests:
        response = await submit_inference(req, BackgroundTasks(), current_user, db)
        task_ids.append(response.task_id)
    
    return {"task_ids": task_ids, "count": len(task_ids)}

# ============================================
# Metrics Endpoints
# ============================================

@app.get("/metrics/queue", tags=["Metrics"])
async def get_queue_metrics(current_user: User = Depends(get_current_user)):
    """Get current queue metrics"""
    from .queue import get_queue_metrics
    
    metrics = await get_queue_metrics()
    return metrics

@app.get("/metrics/gpu", tags=["Metrics"])
async def get_gpu_metrics(current_user: User = Depends(get_current_user)):
    """Get GPU utilization metrics"""
    try:
        import ray
        if not ray.is_initialized():
            raise HTTPException(status_code=503, detail="Ray cluster not available")
        
        # Get Ray cluster resources
        resources = ray.cluster_resources()
        available_resources = ray.available_resources()
        
        return {
            "total_gpus": resources.get("GPU", 0),
            "available_gpus": available_resources.get("GPU", 0),
            "gpu_utilization": 1 - (available_resources.get("GPU", 0) / max(resources.get("GPU", 1), 1))
        }
    except Exception as e:
        logger.error(f"Error getting GPU metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# Error Handlers
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Inference API")
    # Initialize connections, warm up models, etc.

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Inference API")
    # Cleanup connections, save state, etc.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
