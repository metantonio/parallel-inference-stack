"""
Mock vLLM Server

This script simulates a vLLM server for testing purposes.
It implements the OpenAI-compatible API endpoints used by the vLLM worker.
It also includes authentication endpoints for frontend integration.

Usage:
    uvicorn mock_vllm:app --port 8000
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import timedelta
import time
import uuid
import sys
import os
import asyncio
import httpx
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Add app and workers directory to path for imports
workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
if workers_path not in sys.path:
    sys.path.insert(0, workers_path)

# Add app directory to path for imports
app_path = os.path.join(os.path.dirname(__file__), 'app')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

from app.database import get_db, SessionLocal
from app.auth import (
    get_current_user, 
    User, 
    Token, 
    create_access_token, 
    get_user, 
    verify_password, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

app = FastAPI(title="Mock vLLM Server with Dynamic Batching")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration for batching and vLLM connection
MAX_BATCH_SIZE = int(os.getenv("VLLM_MAX_BATCH_SIZE", "32"))
BATCH_WAIT_TIMEOUT = float(os.getenv("VLLM_BATCH_WAIT_TIMEOUT", "0.1"))  # seconds
MAX_CONCURRENT_BATCHES = int(os.getenv("VLLM_MAX_CONCURRENT_BATCHES", "4"))

# Real vLLM server configuration
REAL_VLLM_URL = os.getenv("REAL_VLLM_URL", "http://localhost:8002")  # Real vLLM on different port
REAL_VLLM_MODEL = os.getenv("REAL_VLLM_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
USE_REAL_VLLM = os.getenv("USE_REAL_VLLM", "false").lower() == "true"

# Task storage for async processing
tasks: Dict[str, Dict[str, Any]] = {}
batch_queue: List[Dict[str, Any]] = []
batch_lock = asyncio.Lock()
active_batches = 0
batch_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)

# HTTP client for real vLLM
vllm_client: Optional[httpx.AsyncClient] = None

# Statistics
stats = {
    "total_requests": 0,
    "total_batches": 0,
    "batched_requests": 0,
    "avg_batch_size": 0.0,
    "real_vllm_enabled": USE_REAL_VLLM,
}

# Models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class CompletionRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

class AsyncInferenceResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatus(BaseModel):
    task_id: str
    status: str  # queued, processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float
    completed_at: Optional[float] = None
    batch_id: Optional[str] = None
    batch_size: Optional[int] = None

# ============================================
# Batch Processing Logic
# ============================================

async def call_real_vllm(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the real vLLM server for inference
    
    Args:
        request: Request payload with model, messages, etc.
    
    Returns:
        Response from vLLM server
    """
    global vllm_client
    
    if vllm_client is None:
        vllm_client = httpx.AsyncClient(timeout=120.0)
    
    try:
        # Determine endpoint based on request type
        if "messages" in request:
            endpoint = f"{REAL_VLLM_URL}/v1/chat/completions"
        else:
            endpoint = f"{REAL_VLLM_URL}/v1/completions"
        
        response = await vllm_client.post(endpoint, json=request)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"vLLM API error: {response.status_code} - {response.text}")
    
    except Exception as e:
        logger.error(f"Error calling real vLLM: {str(e)}")
        # Fallback to mock response if real vLLM fails
        return None

async def process_batch(batch_items: List[Dict[str, Any]]):
    """
    Process a batch of requests.
    If USE_REAL_VLLM is True, forwards to real vLLM server.
    Otherwise, returns mock responses.
    """
    global active_batches, stats
    
    batch_id = str(uuid.uuid4())
    batch_size = len(batch_items)
    
    async with batch_semaphore:
        active_batches += 1
        stats["total_batches"] += 1
        stats["batched_requests"] += batch_size
        stats["avg_batch_size"] = stats["batched_requests"] / stats["total_batches"]
        
        start_time = time.time()
        
        if USE_REAL_VLLM:
            # Call real vLLM for each item in the batch
            # Note: vLLM handles its own internal batching
            tasks_to_process = []
            for item in batch_items:
                task_id = item["task_id"]
                request = item["request"]
                tasks_to_process.append((task_id, call_real_vllm(request)))
            
            # Process all requests in parallel (vLLM will batch them internally)
            results = await asyncio.gather(*[task for _, task in tasks_to_process], return_exceptions=True)
            
            # Update task results
            for i, (task_id, _) in enumerate(tasks_to_process):
                result = results[i]
                
                if isinstance(result, Exception) or result is None:
                    # Fallback to mock if vLLM fails
                    request = batch_items[i]["request"]
                    if "messages" in request:
                        content = request["messages"][-1]["content"] if request["messages"] else ""
                        response_text = f"[Mock fallback] Response to: {content}"
                    else:
                        response_text = f"[Mock fallback] Completion for: {request.get('prompt', '')}"
                    
                    result = {
                        "id": f"mock-{batch_id}",
                        "object": "chat.completion" if "messages" in request else "text_completion",
                        "created": int(time.time()),
                        "model": request.get("model", REAL_VLLM_MODEL),
                        "choices": [{
                            "index": 0,
                            "message": {"role": "assistant", "content": response_text} if "messages" in request else None,
                            "text": response_text if "prompt" in request else None,
                            "finish_reason": "stop"
                        }],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
                    }
                
                # Store result
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["completed_at"] = time.time()
                tasks[task_id]["batch_id"] = batch_id
                tasks[task_id]["batch_size"] = batch_size
                tasks[task_id]["result"] = result
                
                # Add batch info to result
                if "batch_info" not in tasks[task_id]["result"]:
                    tasks[task_id]["result"]["batch_info"] = {}
                tasks[task_id]["result"]["batch_info"].update({
                    "batch_id": batch_id,
                    "batch_size": batch_size,
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "real_vllm": True
                })
        else:
            # Mock mode - simulate batched GPU processing
            base_time = 0.5
            batch_overhead = 0.1 * batch_size
            processing_time = base_time + batch_overhead
            
            await asyncio.sleep(processing_time)
            
            # Process all items in the batch with mock responses
            for item in batch_items:
                task_id = item["task_id"]
                request = item["request"]
                
                # Generate mock response
                if "messages" in request:
                    content = request["messages"][-1]["content"] if request["messages"] else ""
                    response_text = f"[Batched mock response {batch_id[:8]}] Mock response to: {content}"
                else:
                    response_text = f"[Batched mock response {batch_id[:8]}] Mock completion for: {request.get('prompt', '')}"
                
                # Update task with result
                tasks[task_id]["status"] = "completed"
                tasks[task_id]["completed_at"] = time.time()
                tasks[task_id]["batch_id"] = batch_id
                tasks[task_id]["batch_size"] = batch_size
                tasks[task_id]["result"] = {
                    "id": f"batch-{batch_id}",
                    "object": "chat.completion" if "messages" in request else "text_completion",
                    "created": int(time.time()),
                    "model": request.get("model", "Qwen/Qwen2.5-Coder-7B-Instruct"),
                    "choices": [{
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text} if "messages" in request else None,
                        "text": response_text if "prompt" in request else None,
                        "finish_reason": "stop"
                    }],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                    "batch_info": {
                        "batch_id": batch_id,
                        "batch_size": batch_size,
                        "processing_time_ms": processing_time * 1000,
                        "real_vllm": False
                    }
                }
        
        active_batches -= 1

async def batch_processor():
    """
    Background task that continuously processes the batch queue.
    Simulates vLLM's continuous batching mechanism.
    """
    while True:
        await asyncio.sleep(BATCH_WAIT_TIMEOUT)
        
        async with batch_lock:
            if not batch_queue:
                continue
            
            # Take up to MAX_BATCH_SIZE items from queue
            batch_items = batch_queue[:MAX_BATCH_SIZE]
            del batch_queue[:len(batch_items)]
            
            # Update task statuses to processing
            for item in batch_items:
                tasks[item["task_id"]]["status"] = "processing"
        
        # Process the batch
        if batch_items:
            asyncio.create_task(process_batch(batch_items))

# Endpoints

# ============================================
# Auth Endpoints
# ============================================

@app.post("/token", response_model=Token, tags=["Auth"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: SessionLocal = Depends(get_db)
):
    """
    Login endpoint for user authentication
    
    Returns a JWT access token that can be used for authenticated requests.
    """
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ============================================
# Health Check Endpoints
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint with batching stats"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "batching": {
            "enabled": True,
            "max_batch_size": MAX_BATCH_SIZE,
            "batch_wait_timeout": BATCH_WAIT_TIMEOUT,
            "max_concurrent_batches": MAX_CONCURRENT_BATCHES,
            "active_batches": active_batches,
            "queue_size": len(batch_queue)
        },
        "stats": stats
    }

# ============================================
# vLLM API Endpoints
# ============================================

@app.get("/v1/models")
async def list_models():
    """List available models"""
    return {
        "object": "list",
        "data": [
            {
                "id": "Qwen/Qwen2.5-Coder-7B-Instruct",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "vllm"
            }
        ]
    }

@app.post("/inference/async", response_model=AsyncInferenceResponse)
async def async_inference(request: ChatCompletionRequest):
    """
    Submit an inference task asynchronously (queued for batching)
    Returns task_id immediately
    """
    task_id = str(uuid.uuid4())
    stats["total_requests"] += 1
    
    # Store task
    tasks[task_id] = {
        "status": "queued",
        "created_at": time.time(),
        "request": request.dict()
    }
    
    # Add to batch queue
    async with batch_lock:
        batch_queue.append({
            "task_id": task_id,
            "request": request.dict()
        })
    
    return AsyncInferenceResponse(
        task_id=task_id,
        status="queued",
        message=f"Task queued for batching. Check status at /tasks/{task_id}"
    )

@app.post("/inference/batch")
async def batch_inference(requests: List[ChatCompletionRequest]):
    """
    Submit multiple inference tasks at once
    All tasks will be queued and processed with dynamic batching
    """
    task_ids = []
    
    for req in requests:
        task_id = str(uuid.uuid4())
        stats["total_requests"] += 1
        
        # Store task
        tasks[task_id] = {
            "status": "queued",
            "created_at": time.time(),
            "request": req.dict()
        }
        
        # Add to batch queue
        async with batch_lock:
            batch_queue.append({
                "task_id": task_id,
                "request": req.dict()
            })
        
        task_ids.append(task_id)
    
    return {
        "task_ids": task_ids,
        "count": len(task_ids),
        "message": f"Submitted {len(task_ids)} tasks for batched processing"
    }

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
        completed_at=task.get("completed_at"),
        batch_id=task.get("batch_id"),
        batch_size=task.get("batch_size")
    )

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
                "completed_at": task.get("completed_at"),
                "batch_id": task.get("batch_id"),
                "batch_size": task.get("batch_size")
            }
            for tid, task in filtered_tasks.items()
        ],
        "total": len(filtered_tasks)
    }

@app.get("/stats")
async def get_stats():
    """Get batching statistics"""
    status_counts = defaultdict(int)
    for task in tasks.values():
        status_counts[task["status"]] += 1
    
    return {
        "batching": {
            "total_requests": stats["total_requests"],
            "total_batches": stats["total_batches"],
            "batched_requests": stats["batched_requests"],
            "avg_batch_size": round(stats["avg_batch_size"], 2),
            "active_batches": active_batches,
            "queue_size": len(batch_queue)
        },
        "tasks": {
            "total": len(tasks),
            "by_status": dict(status_counts)
        },
        "config": {
            "max_batch_size": MAX_BATCH_SIZE,
            "batch_wait_timeout": BATCH_WAIT_TIMEOUT,
            "max_concurrent_batches": MAX_CONCURRENT_BATCHES
        },
        "timestamp": time.time()
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Mock chat completion"""
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Mock response to: {request.messages[-1].content}"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

@app.post("/v1/completions")
async def completions(request: CompletionRequest):
    """Mock text completion"""
    return {
        "id": f"cmpl-{uuid.uuid4()}",
        "object": "text_completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "text": f"Mock completion for: {request.prompt}",
                "index": 0,
                "logprobs": None,
                "finish_reason": "length"
            }
        ],
        "usage": {
            "prompt_tokens": 5,
            "completion_tokens": 10,
            "total_tokens": 15
        }
    }

@app.on_event("startup")
async def startup_event():
    """Start the batch processor on startup"""
    asyncio.create_task(batch_processor())
    print("=" * 70)
    if USE_REAL_VLLM:
        print("🚀 vLLM Batching Proxy Started (REAL vLLM MODE)")
    else:
        print("🚀 Mock vLLM Server with Dynamic Batching Started (MOCK MODE)")
    print("=" * 70)
    print(f"📋 Batching Configuration:")
    print(f"   Max Batch Size: {MAX_BATCH_SIZE}")
    print(f"   Batch Wait Timeout: {BATCH_WAIT_TIMEOUT}s")
    print(f"   Max Concurrent Batches: {MAX_CONCURRENT_BATCHES}")
    if USE_REAL_VLLM:
        print(f"\n🔗 Real vLLM Connection:")
        print(f"   vLLM URL: {REAL_VLLM_URL}")
        print(f"   Model: {REAL_VLLM_MODEL}")
        print(f"   Mode: PROXY (forwards to real vLLM)")
    else:
        print(f"\n🎭 Mock Mode:")
        print(f"   Returns simulated responses")
        print(f"   Set USE_REAL_VLLM=true to enable real vLLM")
    print()
    print(f"📚 API Documentation:")
    print(f"   Swagger UI: http://localhost:8001/docs")
    print()
    print(f"🔗 Endpoints:")
    print(f"   POST /token - User authentication")
    print(f"   GET  /health - Health check with batching stats")
    print(f"   POST /inference/async - Async inference (queued for batching)")
    print(f"   POST /inference/batch - Batch multiple requests")
    print(f"   GET  /tasks/{{task_id}} - Get task status")
    print(f"   GET  /tasks - List all tasks")
    print(f"   GET  /stats - Batching statistics")
    print(f"   POST /v1/chat/completions - vLLM-compatible chat")
    print(f"   POST /v1/completions - vLLM-compatible completion")
    print(f"   GET  /v1/models - List models")
    print("=" * 70)
    print()
    print("💡 Dynamic Batching:")
    print(f"   - Requests are automatically batched for efficiency")
    print(f"   - Use /inference/async for non-blocking requests")
    print(f"   - Use /inference/batch to submit multiple requests at once")
    print(f"   - Check /stats to see batching performance")
    if USE_REAL_VLLM:
        print(f"   - Real LLM responses from vLLM server")
    print("=" * 70)

if __name__ == "__main__":
    import uvicorn
    print("Starting Mock vLLM Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
