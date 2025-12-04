"""
Direct Ollama API Endpoint (No Redis Required)

This creates a simple FastAPI endpoint that directly calls Ollama
without requiring Redis or Celery. Perfect for local testing.

Usage:
    uvicorn demo_api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import sys
import os
from datetime import datetime

# Add workers directory to path
workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
if workers_path not in sys.path:
    sys.path.insert(0, workers_path)

from ollama_worker import get_ollama_worker

# Initialize FastAPI app
app = FastAPI(
    title="Ollama Demo API",
    description="Direct Ollama inference API (no Redis required)",
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

# Request/Response Models
class InferenceRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[list] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "What is Python? Answer in one sentence."
            }
        }

class InferenceResponse(BaseModel):
    output: str
    model: str
    processing_time_ms: float
    status: str
    timestamp: str

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
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
        "timestamp": datetime.utcnow().isoformat()
    }

# Direct inference endpoint
@app.post("/inference", response_model=InferenceResponse)
async def direct_inference(request: InferenceRequest):
    """
    Direct inference endpoint (no queue, immediate response)
    
    Supports both prompt-based and chat-based inference:
    - prompt: Simple text generation
    - messages: Chat completion
    """
    try:
        # Get Ollama worker
        worker = await get_ollama_worker(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            timeout=OLLAMA_TIMEOUT
        )
        
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
        
        # Run inference
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

# Chat endpoint
@app.post("/chat")
async def chat(messages: list):
    """
    Chat completion endpoint
    
    Example:
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ]
    }
    """
    try:
        worker = await get_ollama_worker(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            timeout=OLLAMA_TIMEOUT
        )
        
        result = await worker.chat(messages=messages)
        
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("error", "Chat failed"))
        
        return {
            "response": result.get("output", ""),
            "model": result.get("model", OLLAMA_MODEL),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Generate endpoint
@app.post("/generate")
async def generate(prompt: str, temperature: float = 0.7):
    """
    Simple text generation endpoint
    
    Example:
    {
        "prompt": "Write a hello world in Python",
        "temperature": 0.7
    }
    """
    try:
        worker = await get_ollama_worker(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            timeout=OLLAMA_TIMEOUT
        )
        
        result = await worker.generate(prompt=prompt, temperature=temperature)
        
        if result.get("status") == "failed":
            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
        
        return {
            "response": result.get("output", ""),
            "model": result.get("model", OLLAMA_MODEL),
            "processing_time_ms": result.get("processing_time_ms", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    print("=" * 70)
    print("🚀 Ollama Demo API Started")
    print("=" * 70)
    print(f"📋 Configuration:")
    print(f"   Ollama URL: {OLLAMA_BASE_URL}")
    print(f"   Model: {OLLAMA_MODEL}")
    print(f"   Timeout: {OLLAMA_TIMEOUT}s")
    print()
    print(f"📚 API Documentation:")
    print(f"   Swagger UI: http://localhost:8000/docs")
    print(f"   ReDoc: http://localhost:8000/redoc")
    print()
    print(f"🔗 Endpoints:")
    print(f"   GET  /health - Health check")
    print(f"   POST /inference - Direct inference")
    print(f"   POST /chat - Chat completion")
    print(f"   POST /generate - Text generation")
    print("=" * 70)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
