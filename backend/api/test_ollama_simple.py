"""
Simple Ollama Test using requests library

This is a simpler test that uses the synchronous requests library
to verify Ollama is working before testing the async worker.

Usage:
    python test_ollama_simple.py
"""

import requests
import json
import os

def test_ollama_simple():
    """Simple synchronous test of Ollama"""
    
    print("=" * 70)
    print("SIMPLE OLLAMA TEST")
    print("=" * 70)
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
    
    print(f"\n📋 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    # Test 1: Health check
    print(f"\n🏥 Test 1: Health check...")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("   ✓ Ollama is running")
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            print(f"   Available models: {', '.join(models)}")
            if model not in models:
                print(f"   ⚠ Warning: Model '{model}' not found!")
                print(f"   Run: ollama pull {model}")
                return False
        else:
            print(f"   ✗ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running")
        return False
    
    # Test 2: Simple generation
    print(f"\n💬 Test 2: Simple text generation...")
    prompt = "What is 2+2? Answer with just the number."
    print(f"   Prompt: '{prompt}'")
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            output = result.get("response", "").strip()
            print(f"   ✓ Generation successful!")
            print(f"   Response: {output[:200]}")
            
            # Show timing info
            total_duration = result.get("total_duration", 0) / 1e9  # Convert to seconds
            print(f"   Total time: {total_duration:.2f}s")
        else:
            print(f"   ✗ Generation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test 3: Chat completion
    print(f"\n💭 Test 3: Chat completion...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": "Say 'Hello World' and nothing else."}
    ]
    print(f"   User message: '{messages[1]['content']}'")
    
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            output = result.get("message", {}).get("content", "").strip()
            print(f"   ✓ Chat successful!")
            print(f"   Response: {output[:200]}")
            
            # Show timing info
            total_duration = result.get("total_duration", 0) / 1e9
            print(f"   Total time: {total_duration:.2f}s")
        else:
            print(f"   ✗ Chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\n📝 Ollama is working correctly!")
    print("   You can now test the async worker with: python test_ollama_integration.py")
    
    return True


if __name__ == "__main__":
    import sys
    success = test_ollama_simple()
    sys.exit(0 if success else 1)
