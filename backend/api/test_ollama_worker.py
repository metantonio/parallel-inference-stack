"""
Test script for Ollama worker

This script tests the Ollama worker functionality in isolation.
Run this to verify Ollama integration before running the full backend.

Prerequisites:
1. Ollama installed and running (https://ollama.ai/download)
2. A model pulled (e.g., `ollama pull llama2`)

Usage:
    python test_ollama_worker.py
"""

import asyncio
import sys
import os

# Add workers directory to path
workers_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'workers')
sys.path.insert(0, workers_path)

from ollama_worker import get_ollama_worker


async def test_ollama_worker():
    """Test Ollama worker functionality"""
    
    print("=" * 60)
    print("Ollama Worker Test")
    print("=" * 60)
    
    # Configuration
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama2")
    
    print(f"\nConfiguration:")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")
    
    # Get worker
    print(f"\n1. Initializing Ollama worker...")
    worker = await get_ollama_worker(base_url=base_url, model=model)
    
    # Health check
    print(f"\n2. Running health check...")
    is_healthy = await worker.health_check()
    if is_healthy:
        print("   ✓ Ollama is running and accessible")
    else:
        print("   ✗ Ollama health check failed")
        print("   Make sure Ollama is running: https://ollama.ai/download")
        return
    
    # List models
    print(f"\n3. Listing available models...")
    models = await worker.list_models()
    if models:
        print(f"   Available models: {', '.join(models)}")
        if model not in models:
            print(f"   ⚠ Warning: Model '{model}' not found!")
            print(f"   Run: ollama pull {model}")
    else:
        print("   No models found")
        return
    
    # Test text generation
    print(f"\n4. Testing text generation...")
    test_prompt = "Say hello in one sentence."
    print(f"   Prompt: {test_prompt}")
    
    result = await worker.generate(prompt=test_prompt)
    
    if result.get("status") == "success":
        print(f"   ✓ Generation successful")
        print(f"   Response: {result.get('output', '')[:100]}...")
        print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
    else:
        print(f"   ✗ Generation failed: {result.get('error')}")
    
    # Test chat completion
    print(f"\n5. Testing chat completion...")
    test_messages = [
        {"role": "user", "content": "What is 2+2? Answer in one sentence."}
    ]
    print(f"   Message: {test_messages[0]['content']}")
    
    result = await worker.chat(messages=test_messages)
    
    if result.get("status") == "success":
        print(f"   ✓ Chat successful")
        print(f"   Response: {result.get('output', '')[:100]}...")
        print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
    else:
        print(f"   ✗ Chat failed: {result.get('error')}")
    
    # Test inference method (Ray-compatible interface)
    print(f"\n6. Testing inference method (Ray-compatible)...")
    test_data = {
        "prompt": "Count from 1 to 3."
    }
    print(f"   Data: {test_data}")
    
    result = await worker.inference(data=test_data)
    
    if result.get("status") == "success":
        print(f"   ✓ Inference successful")
        print(f"   Response: {result.get('output', '')[:100]}...")
        print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
    else:
        print(f"   ✗ Inference failed: {result.get('error')}")
    
    # Close worker
    await worker.close()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ollama_worker())
