"""
Standalone Integration Test for Ollama Worker

This test verifies the complete Ollama integration without requiring
Redis, Celery, or the full backend stack.

Prerequisites:
- Ollama installed and running
- A model pulled (e.g., qwen2.5-coder:14b)

Usage:
    cd backend/api
    python test_ollama_integration.py
"""

import asyncio
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'workers'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from ollama_worker import get_ollama_worker, close_ollama_worker


async def test_complete_flow():
    """Test complete inference flow"""
    
    print("=" * 70)
    print("OLLAMA INTEGRATION TEST")
    print("=" * 70)
    
    # Configuration
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
    
    print(f"\n📋 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    try:
        # Step 1: Initialize worker
        print(f"\n🔧 Step 1: Initializing Ollama worker...")
        worker = await get_ollama_worker(base_url=base_url, model=model)
        print("   ✓ Worker initialized")
        
        # Step 2: Health check
        print(f"\n🏥 Step 2: Health check...")
        is_healthy = await worker.health_check()
        if not is_healthy:
            print("   ✗ Ollama is not accessible!")
            print("   Make sure Ollama is running: https://ollama.ai/download")
            return False
        print("   ✓ Ollama is healthy")
        
        # Step 3: List models
        print(f"\n📚 Step 3: Listing available models...")
        models = await worker.list_models()
        if not models:
            print("   ✗ No models found!")
            print(f"   Run: ollama pull {model}")
            return False
        print(f"   Available models: {', '.join(models)}")
        if model not in models:
            print(f"   ⚠ Warning: Model '{model}' not in list!")
            print(f"   Run: ollama pull {model}")
        
        # Step 4: Test simple generation
        print(f"\n💬 Step 4: Testing simple text generation...")
        prompt = "What is 2+2? Answer with just the number."
        print(f"   Prompt: '{prompt}'")
        
        result = await worker.generate(prompt=prompt)
        
        if result.get("status") == "success":
            output = result.get("output", "").strip()
            print(f"   ✓ Generation successful!")
            print(f"   Response: {output[:200]}")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        else:
            print(f"   ✗ Generation failed: {result.get('error')}")
            return False
        
        # Step 5: Test chat completion
        print(f"\n💭 Step 5: Testing chat completion...")
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": "Explain what is Python in one sentence."}
        ]
        print(f"   User message: '{messages[1]['content']}'")
        
        result = await worker.chat(messages=messages)
        
        if result.get("status") == "success":
            output = result.get("output", "").strip()
            print(f"   ✓ Chat successful!")
            print(f"   Response: {output[:200]}")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        else:
            print(f"   ✗ Chat failed: {result.get('error')}")
            return False
        
        # Step 6: Test Ray-compatible interface (prompt)
        print(f"\n🔄 Step 6: Testing Ray-compatible interface (prompt)...")
        data = {
            "prompt": "Count from 1 to 5, separated by commas."
        }
        print(f"   Data: {data}")
        
        result = await worker.inference(data=data)
        
        if result.get("status") == "success":
            output = result.get("output", "").strip()
            print(f"   ✓ Inference successful!")
            print(f"   Response: {output[:200]}")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        else:
            print(f"   ✗ Inference failed: {result.get('error')}")
            return False
        
        # Step 7: Test Ray-compatible interface (messages)
        print(f"\n🔄 Step 7: Testing Ray-compatible interface (messages)...")
        data = {
            "messages": [
                {"role": "user", "content": "Say 'Hello World' and nothing else."}
            ]
        }
        print(f"   Data: {data}")
        
        result = await worker.inference(data=data)
        
        if result.get("status") == "success":
            output = result.get("output", "").strip()
            print(f"   ✓ Inference successful!")
            print(f"   Response: {output[:200]}")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        else:
            print(f"   ✗ Inference failed: {result.get('error')}")
            return False
        
        # Step 8: Test code generation (relevant for qwen2.5-coder)
        print(f"\n💻 Step 8: Testing code generation...")
        data = {
            "prompt": "Write a Python function to add two numbers. Just the function, no explanation.",
            "temperature": 0.1  # Lower temperature for more deterministic output
        }
        print(f"   Prompt: '{data['prompt']}'")
        
        result = await worker.inference(data=data)
        
        if result.get("status") == "success":
            output = result.get("output", "").strip()
            print(f"   ✓ Code generation successful!")
            print(f"   Response:")
            print("   " + "\n   ".join(output[:300].split("\n")))
            if len(output) > 300:
                print("   ...")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.2f}ms")
        else:
            print(f"   ✗ Code generation failed: {result.get('error')}")
            return False
        
        # Cleanup
        await close_ollama_worker()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\n📝 Summary:")
        print("   - Ollama worker is functioning correctly")
        print("   - All inference methods work as expected")
        print("   - Ray-compatible interface is operational")
        print("   - Ready for integration with backend API")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    success = asyncio.run(test_complete_flow())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
