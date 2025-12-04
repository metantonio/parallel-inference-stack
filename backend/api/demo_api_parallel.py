"""
Parallel Ollama API with AsyncIO

This version supports parallel inference by:
1. Using FastAPI's async capabilities
2. Allowing concurrent requests to Ollama
3. Processing multiple requests simultaneously

Note: Ollama itself processes requests sequentially, but this API
can handle multiple concurrent requests and queue them efficiently.

Usage:
    uvicorn demo_api_parallel:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import asyncio
import sys
import os
from datetime import datetime
import uuid
from collections import defaultdict

# Add workers directory to path
workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
if workers_path not in sys.path:
    sys.path.insert(0, workers_path)

from ollama_worker import get_ollama_worker

# Initialize FastAPI app
app = FastAPI(
    title="Parallel Ollama API",
    description="Ollama API with parallel request handling",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

# Task storage (in-memory for demo)
tasks: Dict[str, Dict[str, Any]] = {}
task_queue = asyncio.Queue()
active_tasks = 0
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

# Request/Response Models
class InferenceRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[list] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    async_mode: bool = False  # If True, returns task_id immediately
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is Python?",
                "async_mode": False
            }
        }

class AsyncInferenceResponse(BaseModel):
    task_id: str
    status: str
    message: str

class InferenceResponse(BaseModel):
    output: str
    model: str
    processing_time_ms: float
    status: str
    timestamp: str

class TaskStatus(BaseModel):
    task_id: str
    status: str  # queued, processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

# Background task processor
async def process_inference_task(task_id: str, data: Dict[str, Any]):
    """Process an inference task in the background"""
    global active_tasks
    
    try:
        # Update status to processing
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["started_at"] = datetime.utcnow().isoformat()
        
        # Acquire semaphore to limit concurrent requests
        async with task_semaphore:
            active_tasks += 1
            
            # Get Ollama worker
            worker = await get_ollama_worker(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_MODEL,
                timeout=OLLAMA_TIMEOUT
            )
            
            # Run inference
            result = await worker.inference(data)
            
            active_tasks -= 1
            
            if result.get("status") == "failed":
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = result.get("error", "Unknown error")
            else:
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["result"] = result
            
            tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()
            
    except Exception as e:
        active_tasks -= 1
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint with parallel processing info"""
    worker = await get_ollama_worker(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        timeout=OLLAMA_TIMEOUT
    )
    
    is_healthy = await worker.health_check()
    models = await worker.list_models() if is_healthy else []
    
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL,
        "available_models": models,
        "max_concurrent_requests": MAX_CONCURRENT_REQUESTS,
        "active_tasks": active_tasks,
        "total_tasks": len(tasks),
        "timestamp": datetime.utcnow().isoformat()
    }

# Direct inference endpoint (synchronous)
@app.post("/inference", response_model=InferenceResponse)
async def direct_inference(request: InferenceRequest):
    """
    Direct inference endpoint
    
    If async_mode=False: Waits for result (default)
    If async_mode=True: Returns task_id immediately
    """
    # Prepare data
    data = {}
    if request.prompt:
        data["prompt"] = request.prompt
    if request.messages:
        data["messages"] = request.messages
    if request.temperature is not None:
        data["temperature"] = request.temperature
    if request.max_tokens is not None:
        data["max_tokens"] = request.max_tokens
    
    if request.async_mode:
        # Async mode: return task_id immediately
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Start background task
        asyncio.create_task(process_inference_task(task_id, data))
        
        return {
            "output": f"Task queued with ID: {task_id}",
            "model": OLLAMA_MODEL,
            "processing_time_ms": 0,
            "status": "queued",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        # Sync mode: wait for result
        try:
            worker = await get_ollama_worker(
                base_url=OLLAMA_BASE_URL,
                model=OLLAMA_MODEL,
                timeout=OLLAMA_TIMEOUT
            )
            
            result = await worker.inference(data)
            
            if result.get("status") == "failed":
                raise HTTPException(status_code=500, detail=result.get("error", "Inference failed"))
            
            return InferenceResponse(
                output=result.get("output", ""),
                model=result.get("model", OLLAMA_MODEL),
                processing_time_ms=result.get("processing_time_ms", 0),
                status="success",
                timestamp=datetime.utcnow().isoformat()
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# Async inference endpoint
@app.post("/inference/async", response_model=AsyncInferenceResponse)
async def async_inference(request: InferenceRequest):
    """
    Submit an inference task asynchronously
    Returns task_id immediately
    """
    task_id = str(uuid.uuid4())
    
    # Prepare data
    data = {}
    if request.prompt:
        data["prompt"] = request.prompt
    if request.messages:
        data["messages"] = request.messages
    if request.temperature is not None:
        data["temperature"] = request.temperature
    if request.max_tokens is not None:
        data["max_tokens"] = request.max_tokens
    
    # Store task
    tasks[task_id] = {
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
        "data": data
    }
    
    # Start background processing
    asyncio.create_task(process_inference_task(task_id, data))
    
    return AsyncInferenceResponse(
        task_id=task_id,
        status="queued",
        message=f"Task queued. Check status at /tasks/{task_id}"
    )

# Batch inference endpoint
@app.post("/inference/batch")
async def batch_inference(requests: List[InferenceRequest]):
    """
    Submit multiple inference tasks at once
    Returns list of task_ids
    """
    task_ids = []
    
    for req in requests:
        task_id = str(uuid.uuid4())
        
        # Prepare data
        data = {}
        if req.prompt:
            data["prompt"] = req.prompt
        if req.messages:
            data["messages"] = req.messages
        if req.temperature is not None:
            data["temperature"] = req.temperature
        if req.max_tokens is not None:
            data["max_tokens"] = req.max_tokens
        
        # Store task
        tasks[task_id] = {
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Start background processing
        asyncio.create_task(process_inference_task(task_id, data))
        
        task_ids.append(task_id)
    
    return {
        "task_ids": task_ids,
        "count": len(task_ids),
        "message": f"Submitted {len(task_ids)} tasks for processing"
    }

# Get task status
@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get the status of an async inference task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    return TaskStatus(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )

# List all tasks
@app.get("/tasks")
async def list_tasks(status: Optional[str] = None):
    """List all tasks, optionally filtered by status"""
    filtered_tasks = tasks
    
    if status:
        filtered_tasks = {
            tid: task for tid, task in tasks.items()
            if task["status"] == status
        }
    
    return {
        "tasks": [
            {
                "task_id": tid,
                "status": task["status"],
                "created_at": task["created_at"],
                "completed_at": task.get("completed_at")
            }
            for tid, task in filtered_tasks.items()
        ],
        "total": len(filtered_tasks)
    }

# Stats endpoint
@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    status_counts = defaultdict(int)
    for task in tasks.values():
        status_counts[task["status"]] += 1
    
    return {
        "total_tasks": len(tasks),
        "active_tasks": active_tasks,
        "max_concurrent": MAX_CONCURRENT_REQUESTS,
        "status_breakdown": dict(status_counts),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    print("=" * 70)
    print("🚀 Parallel Ollama API Started")
    print("=" * 70)
    print(f"📋 Configuration:")
    print(f"   Ollama URL: {OLLAMA_BASE_URL}")
    print(f"   Model: {OLLAMA_MODEL}")
    print(f"   Max Concurrent Requests: {MAX_CONCURRENT_REQUESTS}")
    print()
    print(f"📚 API Documentation:")
    print(f"   Swagger UI: http://localhost:8000/docs")
    print()
    print(f"🔗 Endpoints:")
    print(f"   GET  /health - Health check with stats")
    print(f"   POST /inference - Sync/async inference")
    print(f"   POST /inference/async - Async inference")
    print(f"   POST /inference/batch - Batch inference")
    print(f"   GET  /tasks/{{task_id}} - Get task status")
    print(f"   GET  /tasks - List all tasks")
    print(f"   GET  /stats - Processing statistics")
    print("=" * 70)
    print()
    print("💡 Parallel Processing:")
    print(f"   - Can handle up to {MAX_CONCURRENT_REQUESTS} concurrent requests")
    print("   - Use async_mode=true for non-blocking requests")
    print("   - Use /inference/batch for multiple requests at once")
    print("=" * 70)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
