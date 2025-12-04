"""
Mock vLLM Server

This script simulates a vLLM server for testing purposes.
It implements the OpenAI-compatible API endpoints used by the vLLM worker.

Usage:
    uvicorn mock_vllm:app --port 8000
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time
import uuid

app = FastAPI(title="Mock vLLM Server")

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

# Endpoints

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

if __name__ == "__main__":
    import uvicorn
    print("Starting Mock vLLM Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
