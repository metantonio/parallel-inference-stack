"""
Ray Serve GPU Worker Implementation

This module implements the GPU inference worker using Ray Serve.
It handles model loading, batching, and GPU allocation automatically.
"""

import ray
from ray import serve
import torch
import logging
import os
from typing import Dict, Any, List
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Model Loader
# ============================================

class ModelLoader:
    """Handles model loading and caching"""
    
    def __init__(self, model_path: str, model_version: str = "latest"):
        self.model_path = model_path
        self.model_version = model_version
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"Initializing ModelLoader on device: {self.device}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    def load_model(self):
        """
        Load the AI model
        
        Replace this with your actual model loading logic.
        This is a placeholder that works with any PyTorch model.
        """
        try:
            # Example: Load a pretrained model
            # For demonstration, we'll use a simple model
            # Replace with your actual model loading code
            
            model_file = os.path.join(self.model_path, f"model_{self.model_version}.pt")
            
            if os.path.exists(model_file):
                logger.info(f"Loading model from {model_file}")
                model = torch.load(model_file, map_location=self.device)
            else:
                logger.warning(f"Model file not found: {model_file}")
                logger.info("Creating dummy model for demonstration")
                # Create a simple dummy model
                model = torch.nn.Sequential(
                    torch.nn.Linear(768, 512),
                    torch.nn.ReLU(),
                    torch.nn.Linear(512, 256),
                    torch.nn.ReLU(),
                    torch.nn.Linear(256, 128)
                )
            
            model = model.to(self.device)
            model.eval()
            
            logger.info("Model loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise

# ============================================
# Ray Serve Deployment
# ============================================

@serve.deployment(
    name="InferenceModel",
    num_replicas=3,  # Number of replicas (should match number of GPUs)
    ray_actor_options={
        "num_gpus": 1,  # Each replica gets 1 GPU
        "num_cpus": 4   # 4 CPU cores per replica
    },
    max_concurrent_queries=10,  # Max concurrent requests per replica
    autoscaling_config={
        "min_replicas": 1,
        "max_replicas": 10,
        "target_num_ongoing_requests_per_replica": 5
    }
)
class InferenceModel:
    """
    Ray Serve deployment for GPU inference
    
    This class handles:
    - Model initialization and caching
    - Request batching
    - GPU inference
    - Error handling
    """
    
    def __init__(self):
        """Initialize the model on GPU"""
        self.model_path = os.getenv("MODEL_PATH", "/models")
        self.batch_size = int(os.getenv("BATCH_SIZE", "32"))
        self.max_batch_wait_ms = int(os.getenv("MAX_BATCH_WAIT_MS", "100"))
        
        logger.info("Initializing InferenceModel deployment")
        logger.info(f"Model path: {self.model_path}")
        logger.info(f"Batch size: {self.batch_size}")
        logger.info(f"Max batch wait: {self.max_batch_wait_ms}ms")
        
        # Load model
        self.loader = ModelLoader(self.model_path)
        self.model = self.loader.load_model()
        
        # Warm up model
        self._warmup()
        
        logger.info("InferenceModel deployment ready")
    
    def _warmup(self):
        """Warm up the model with a dummy inference"""
        try:
            logger.info("Warming up model...")
            dummy_input = torch.randn(1, 768).to(self.loader.device)
            with torch.no_grad():
                _ = self.model(dummy_input)
            logger.info("Model warmup complete")
        except Exception as e:
            logger.warning(f"Warmup failed: {str(e)}")
    
    @serve.batch(max_batch_size=32, batch_wait_timeout_s=0.1)
    async def handle_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle a batch of inference requests
        
        Ray Serve automatically batches requests for optimal GPU utilization.
        
        Args:
            requests: List of request dictionaries
        
        Returns:
            List of result dictionaries
        """
        batch_start = datetime.utcnow()
        logger.info(f"Processing batch of {len(requests)} requests")
        
        try:
            # Extract input data from requests
            batch_inputs = []
            for req in requests:
                # This is a placeholder - adapt to your actual input format
                input_data = req.get("data", {})
                
                # Convert input to tensor
                # Example: if input is text, you'd tokenize here
                # For now, we'll create dummy tensors
                if isinstance(input_data, dict) and "tensor" in input_data:
                    tensor = torch.tensor(input_data["tensor"])
                else:
                    # Create dummy tensor for demonstration
                    tensor = torch.randn(768)
                
                batch_inputs.append(tensor)
            
            # Stack into batch
            batch_tensor = torch.stack(batch_inputs).to(self.loader.device)
            
            # Run inference
            with torch.no_grad():
                batch_output = self.model(batch_tensor)
            
            # Convert outputs to list of dicts
            results = []
            for i, output in enumerate(batch_output):
                result = {
                    "output": output.cpu().numpy().tolist(),
                    "shape": list(output.shape),
                    "device": str(self.loader.device),
                    "batch_size": len(requests),
                    "processing_time_ms": (datetime.utcnow() - batch_start).total_seconds() * 1000
                }
                results.append(result)
            
            batch_time = (datetime.utcnow() - batch_start).total_seconds() * 1000
            logger.info(f"Batch processed in {batch_time:.2f}ms ({batch_time/len(requests):.2f}ms per request)")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            # Return error for all requests in batch
            error_result = {
                "error": str(e),
                "status": "failed"
            }
            return [error_result] * len(requests)
    
    async def __call__(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a single inference request
        
        This method is called by Ray Serve for each request.
        It delegates to handle_batch which automatically batches requests.
        
        Args:
            request: Request dictionary with input data
        
        Returns:
            Result dictionary
        """
        try:
            # The @serve.batch decorator will automatically batch these calls
            results = await self.handle_batch([request])
            return results[0]
            
        except Exception as e:
            logger.error(f"Error in inference: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }

# ============================================
# Alternative: Non-batched Deployment
# ============================================

@serve.deployment(
    name="InferenceModelNoBatch",
    num_replicas=3,
    ray_actor_options={"num_gpus": 1, "num_cpus": 4}
)
class InferenceModelNoBatch:
    """
    Non-batched version for comparison
    
    Use this if your model doesn't benefit from batching
    or if you need lower latency for individual requests.
    """
    
    def __init__(self):
        self.model_path = os.getenv("MODEL_PATH", "/models")
        self.loader = ModelLoader(self.model_path)
        self.model = self.loader.load_model()
        self._warmup()
    
    def _warmup(self):
        dummy_input = torch.randn(1, 768).to(self.loader.device)
        with torch.no_grad():
            _ = self.model(dummy_input)
    
    async def __call__(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process single request without batching"""
        try:
            start_time = datetime.utcnow()
            
            # Extract input
            input_data = request.get("data", {})
            
            # Convert to tensor
            if isinstance(input_data, dict) and "tensor" in input_data:
                input_tensor = torch.tensor(input_data["tensor"])
            else:
                input_tensor = torch.randn(768)
            
            input_tensor = input_tensor.unsqueeze(0).to(self.loader.device)
            
            # Run inference
            with torch.no_grad():
                output = self.model(input_tensor)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "output": output.cpu().numpy().tolist(),
                "shape": list(output.shape),
                "device": str(self.loader.device),
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in inference: {str(e)}")
            return {"error": str(e), "status": "failed"}

# ============================================
# Deployment Script
# ============================================

def deploy_model(use_batching: bool = True):
    """
    Deploy the model to Ray Serve
    
    Args:
        use_batching: Whether to use batched deployment
    """
    # Initialize Ray
    if not ray.is_initialized():
        ray.init(address="auto")  # Connect to existing cluster
    
    # Start Ray Serve
    serve.start(detached=True, http_options={"host": "0.0.0.0", "port": 8000})
    
    # Deploy model
    if use_batching:
        logger.info("Deploying batched model")
        InferenceModel.deploy()
    else:
        logger.info("Deploying non-batched model")
        InferenceModelNoBatch.deploy()
    
    logger.info("Model deployed successfully")
    logger.info("Ray Dashboard: http://localhost:8265")

if __name__ == "__main__":
    import sys
    
    # Check for batching flag
    use_batching = "--no-batch" not in sys.argv
    
    # Deploy model
    deploy_model(use_batching=use_batching)
    
    # Keep running
    logger.info("Press Ctrl+C to stop")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        serve.shutdown()
        ray.shutdown()
