"""
Demo Client for Ollama API

This script demonstrates the working Ollama integration by making
requests to the demo API.

Usage:
    1. Start the API: uvicorn demo_api:app --reload --port 8000
    2. Run this script: python demo_client.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_health():
    """Test health check endpoint"""
    print_section("1. HEALTH CHECK")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Status: {data['status']}")
            print(f"✓ Ollama URL: {data['ollama_url']}")
            print(f"✓ Model: {data['model']}")
            print(f"✓ Available models: {', '.join(data['available_models'])}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        print("\nMake sure the API is running:")
        print("  uvicorn demo_api:app --reload --port 8000")
        return False

def test_simple_generation():
    """Test simple text generation"""
    print_section("2. SIMPLE TEXT GENERATION")
    
    prompt = "What is 2+2? Answer with just the number."
    print(f"Prompt: '{prompt}'")
    print("Sending request...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json={"prompt": prompt, "temperature": 0.1},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            elapsed = time.time() - start
            
            print(f"\n✓ Response received in {elapsed:.2f}s")
            print(f"✓ Model: {data['model']}")
            print(f"✓ Processing time: {data['processing_time_ms']:.2f}ms")
            print(f"\n📝 Response:")
            print(f"   {data['response'][:200]}")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_chat_completion():
    """Test chat completion"""
    print_section("3. CHAT COMPLETION")
    
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant. Be concise."},
        {"role": "user", "content": "Explain what is Python in one sentence."}
    ]
    
    print(f"System: {messages[0]['content']}")
    print(f"User: {messages[1]['content']}")
    print("Sending request...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json=messages,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            elapsed = time.time() - start
            
            print(f"\n✓ Response received in {elapsed:.2f}s")
            print(f"✓ Model: {data['model']}")
            print(f"✓ Processing time: {data['processing_time_ms']:.2f}ms")
            print(f"\n📝 Assistant:")
            print(f"   {data['response'][:300]}")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_code_generation():
    """Test code generation"""
    print_section("4. CODE GENERATION")
    
    prompt = "Write a Python function to add two numbers. Just the function, no explanation."
    print(f"Prompt: '{prompt}'")
    print("Sending request...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json={"prompt": prompt, "temperature": 0.1},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            elapsed = time.time() - start
            
            print(f"\n✓ Response received in {elapsed:.2f}s")
            print(f"✓ Model: {data['model']}")
            print(f"✓ Processing time: {data['processing_time_ms']:.2f}ms")
            print(f"\n📝 Generated Code:")
            print("   " + "\n   ".join(data['response'][:400].split("\n")))
            if len(data['response']) > 400:
                print("   ...")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_inference_endpoint():
    """Test the main inference endpoint"""
    print_section("5. INFERENCE ENDPOINT (Ray-compatible)")
    
    data = {
        "prompt": "Count from 1 to 5, separated by commas."
    }
    
    print(f"Data: {data}")
    print("Sending request...")
    
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/inference",
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            elapsed = time.time() - start
            
            print(f"\n✓ Response received in {elapsed:.2f}s")
            print(f"✓ Model: {result['model']}")
            print(f"✓ Processing time: {result['processing_time_ms']:.2f}ms")
            print(f"✓ Status: {result['status']}")
            print(f"\n📝 Output:")
            print(f"   {result['output'][:200]}")
            return True
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  OLLAMA API DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates the working Ollama integration locally.")
    print("All requests are processed by Ollama without requiring Redis/Celery.")
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health()))
    if not results[-1][1]:
        print("\n❌ Cannot proceed without healthy API")
        return
    
    time.sleep(1)
    results.append(("Simple Generation", test_simple_generation()))
    
    time.sleep(1)
    results.append(("Chat Completion", test_chat_completion()))
    
    time.sleep(1)
    results.append(("Code Generation", test_code_generation()))
    
    time.sleep(1)
    results.append(("Inference Endpoint", test_inference_endpoint()))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ The Ollama integration is working correctly!")
        print("✅ You can now use this API for local development")
        print("\n📚 Try the interactive docs:")
        print("   http://localhost:8000/docs")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
