"""
vLLM Worker Implementation

This worker uses vLLM for high-performance inference with dynamic batching.
vLLM provides continuous batching and much better GPU utilization than Ollama.

Installation:
    pip install vllm

Usage:
    1. Start vLLM server:
       vllm serve Qwen/Qwen2.5-Coder-7B-Instruct --port 11434
    
    2. Use this worker instead of ollama_worker
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class VLLMWorker:
    """
    vLLM inference worker with dynamic batching support
    
    This class provides the same interface as OllamaWorker but uses
    vLLM's OpenAI-compatible API for better performance.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", model: str = "Qwen/Qwen2.5-Coder-7B-Instruct", timeout: int = 120):
        """
        Initialize vLLM worker
        
        Args:
            base_url: vLLM server endpoint
            model: Model name (HuggingFace model ID)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"Initialized VLLMWorker with model '{model}' at {base_url}")
        logger.info("vLLM provides continuous batching for better GPU utilization")
    
    async def health_check(self) -> bool:
        """
        Check if vLLM server is running and accessible
        
        Returns:
            True if vLLM is healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"vLLM health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> list:
        """
        List available models in vLLM
        
        Returns:
            List of model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using vLLM
        
        Args:
            prompt: Input prompt for generation
            **kwargs: Additional generation parameters
        
        Returns:
            Dictionary with generation result
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare request payload (OpenAI format)
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 1.0),
                "stream": False
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Sending generation request to vLLM (model: {self.model})")
            
            # Send request to vLLM
            response = await self.client.post(
                f"{self.base_url}/v1/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"vLLM API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Generation completed in {processing_time:.2f}ms")
            
            # Extract output
            output = result["choices"][0]["text"] if result.get("choices") else ""
            
            return {
                "output": output,
                "model": self.model,
                "processing_time_ms": processing_time,
                "usage": result.get("usage", {}),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        """
        Chat completion using vLLM
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional chat parameters
        
        Returns:
            Dictionary with chat completion result
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare request payload (OpenAI format)
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 1.0),
                "stream": False
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Sending chat request to vLLM (model: {self.model})")
            
            # Send request to vLLM
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"vLLM API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Chat completed in {processing_time:.2f}ms")
            
            # Extract output
            message = result["choices"][0]["message"] if result.get("choices") else {}
            output = message.get("content", "")
            
            return {
                "output": output,
                "message": message,
                "model": self.model,
                "processing_time_ms": processing_time,
                "usage": result.get("usage", {}),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error during chat: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def inference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main inference method compatible with Ray worker interface
        
        Args:
            data: Input data dictionary
        
        Returns:
            Result dictionary
        """
        try:
            # Determine inference type based on input data
            if "messages" in data:
                # Chat completion
                return await self.chat(
                    messages=data["messages"],
                    **{k: v for k, v in data.items() if k != "messages"}
                )
            elif "prompt" in data or "text" in data:
                # Text generation
                prompt = data.get("prompt") or data.get("text", "")
                return await self.generate(
                    prompt=prompt,
                    **{k: v for k, v in data.items() if k not in ["prompt", "text"]}
                )
            else:
                # Default: treat entire data as prompt
                return await self.generate(
                    prompt=str(data),
                )
        
        except Exception as e:
            logger.error(f"Error in inference: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
        logger.info("VLLMWorker closed")


# Singleton instance
_vllm_worker: Optional[VLLMWorker] = None


async def get_vllm_worker(base_url: str = "http://localhost:8000", 
                          model: str = "Qwen/Qwen2.5-Coder-7B-Instruct", 
                          timeout: int = 120) -> VLLMWorker:
    """
    Get or create vLLM worker singleton
    
    Args:
        base_url: vLLM server endpoint
        model: Model name to use
        timeout: Request timeout in seconds
    
    Returns:
        VLLMWorker instance
    """
    global _vllm_worker
    
    if _vllm_worker is None:
        _vllm_worker = VLLMWorker(base_url=base_url, model=model, timeout=timeout)
        
        # Verify vLLM is accessible
        if not await _vllm_worker.health_check():
            logger.warning("vLLM health check failed - service may not be running")
            logger.warning("Start vLLM with: vllm serve <model-name>")
        else:
            models = await _vllm_worker.list_models()
            logger.info(f"Available vLLM models: {models}")
    
    return _vllm_worker


async def close_vllm_worker():
    """Close the vLLM worker singleton"""
    global _vllm_worker
    if _vllm_worker is not None:
        await _vllm_worker.close()
        _vllm_worker = None
