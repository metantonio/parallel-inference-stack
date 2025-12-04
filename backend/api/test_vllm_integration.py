"""
vLLM Integration Test

This script tests the vLLM worker integration.
It verifies that the worker can communicate with a vLLM-compatible API
(either real vLLM or a mock server).

Usage:
    python test_vllm_integration.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vllm_test")

# Add workers directory to path
workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
if workers_path not in sys.path:
    sys.path.insert(0, workers_path)

from vllm_worker import get_vllm_worker, close_vllm_worker

async def test_vllm_flow():
    """Test the complete vLLM worker flow"""
    
    print("=" * 70)
    print("vLLM INTEGRATION TEST")
    print("=" * 70)
    
    # Configuration
    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8001")
    model = os.getenv("VLLM_MODEL", "Qwen/Qwen2.5-Coder-7B-Instruct")
    
    print(f"Configuration:")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    print("-" * 70)
    
    try:
        # 1. Initialize Worker
        print("\n1. Initializing Worker...")
        worker = await get_vllm_worker(base_url=base_url, model=model)
        print("   ✓ Worker initialized")
        
        # 2. Health Check
        print("\n2. Health Check...")
        is_healthy = await worker.health_check()
        if is_healthy:
            print("   ✓ vLLM is healthy")
        else:
            print("   ✗ vLLM is NOT accessible")
            print("   Make sure the server is running!")
            return False
            
        # 3. List Models
        print("\n3. Listing Models...")
        models = await worker.list_models()
        print(f"   Available models: {models}")
        
        # 4. Text Generation
        print("\n4. Testing Text Generation...")
        prompt = "What is 2+2? Answer with just the number."
        print(f"   Prompt: '{prompt}'")
        
        result = await worker.generate(prompt=prompt, temperature=0.1)
        
        if result["status"] == "success":
            print(f"   ✓ Success!")
            print(f"   Output: {result['output'].strip()}")
            print(f"   Time: {result['processing_time_ms']:.2f}ms")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
            
        # 5. Chat Completion
        print("\n5. Testing Chat Completion...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello!"}
        ]
        
        result = await worker.chat(messages=messages)
        
        if result["status"] == "success":
            print(f"   ✓ Success!")
            print(f"   Output: {result['output'].strip()}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
            
        # 6. Ray-compatible Interface
        print("\n6. Testing Ray-compatible Interface...")
        data = {"prompt": "Count to 3"}
        
        result = await worker.inference(data)
        
        if result["status"] == "success":
            print(f"   ✓ Success!")
            print(f"   Output: {result['output'].strip()}")
        else:
            print(f"   ✗ Failed: {result.get('error')}")
            
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_vllm_worker()

if __name__ == "__main__":
    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success = loop.run_until_complete(test_vllm_flow())
        sys.exit(0 if success else 1)
    finally:
        loop.close()
