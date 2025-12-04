"""
Ollama Worker Implementation

This module implements a local inference worker using Ollama.
It provides the same interface as Ray workers for compatibility.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class OllamaWorker:
    """
    Ollama inference worker for local development
    
    This class handles:
    - Connection to local Ollama instance
    - Request formatting and validation
    - Inference execution
    - Error handling
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2", timeout: int = 120):
        """
        Initialize Ollama worker
        
        Args:
            base_url: Ollama API endpoint
            model: Model name to use for inference
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"Initialized OllamaWorker with model '{model}' at {base_url}")
    
    async def health_check(self) -> bool:
        """
        Check if Ollama is running and accessible
        
        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> list:
        """
        List available models in Ollama
        
        Returns:
            List of model names
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate text using Ollama
        
        Args:
            prompt: Input prompt for generation
            **kwargs: Additional generation parameters
        
        Returns:
            Dictionary with generation result
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            logger.info(f"Sending generation request to Ollama (model: {self.model})")
            
            # Send request to Ollama
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Generation completed in {processing_time:.2f}ms")
            
            return {
                "output": result.get("response", ""),
                "model": self.model,
                "processing_time_ms": processing_time,
                "total_duration": result.get("total_duration"),
                "load_duration": result.get("load_duration"),
                "prompt_eval_count": result.get("prompt_eval_count"),
                "eval_count": result.get("eval_count"),
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
        Chat completion using Ollama
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional chat parameters
        
        Returns:
            Dictionary with chat completion result
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
            
            logger.info(f"Sending chat request to Ollama (model: {self.model})")
            
            # Send request to Ollama
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.info(f"Chat completed in {processing_time:.2f}ms")
            
            return {
                "output": result.get("message", {}).get("content", ""),
                "message": result.get("message"),
                "model": self.model,
                "processing_time_ms": processing_time,
                "total_duration": result.get("total_duration"),
                "load_duration": result.get("load_duration"),
                "prompt_eval_count": result.get("prompt_eval_count"),
                "eval_count": result.get("eval_count"),
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
        logger.info("OllamaWorker closed")


# Singleton instance
_ollama_worker: Optional[OllamaWorker] = None


async def get_ollama_worker(base_url: str = "http://localhost:11434", 
                            model: str = "llama2", 
                            timeout: int = 120) -> OllamaWorker:
    """
    Get or create Ollama worker singleton
    
    Args:
        base_url: Ollama API endpoint
        model: Model name to use
        timeout: Request timeout in seconds
    
    Returns:
        OllamaWorker instance
    """
    global _ollama_worker
    
    if _ollama_worker is None:
        _ollama_worker = OllamaWorker(base_url=base_url, model=model, timeout=timeout)
        
        # Verify Ollama is accessible
        if not await _ollama_worker.health_check():
            logger.warning("Ollama health check failed - service may not be running")
        else:
            models = await _ollama_worker.list_models()
            logger.info(f"Available Ollama models: {models}")
            if model not in models:
                logger.warning(f"Model '{model}' not found in Ollama. Available models: {models}")
    
    return _ollama_worker


async def close_ollama_worker():
    """Close the Ollama worker singleton"""
    global _ollama_worker
    if _ollama_worker is not None:
        await _ollama_worker.close()
        _ollama_worker = None
