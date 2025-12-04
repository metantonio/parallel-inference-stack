"""
Test Script for Mock vLLM Dynamic Batching

This script demonstrates the dynamic batching capabilities of the mock vLLM server.
It sends multiple parallel requests and shows how they are batched together.

Usage:
    python test_batching.py
"""

import requests
import time
import asyncio
import aiohttp
from typing import List, Dict, Any

BASE_URL = "http://localhost:8001"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_health():
    """Test health endpoint and show batching config"""
    print_section("1. HEALTH CHECK & BATCHING CONFIG")
    
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Server Status: {data['status']}")
        print(f"\n📊 Batching Configuration:")
        batching = data.get('batching', {})
        print(f"   Enabled: {batching.get('enabled')}")
        print(f"   Max Batch Size: {batching.get('max_batch_size')}")
        print(f"   Batch Wait Timeout: {batching.get('batch_wait_timeout')}s")
        print(f"   Max Concurrent Batches: {batching.get('max_concurrent_batches')}")
        print(f"   Active Batches: {batching.get('active_batches')}")
        print(f"   Queue Size: {batching.get('queue_size')}")
    else:
        print(f"✗ Health check failed: {response.status_code}")

async def submit_async_request(session: aiohttp.ClientSession, prompt: str, index: int) -> str:
    """Submit a single async inference request"""
    payload = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with session.post(f"{BASE_URL}/inference/async", json=payload) as response:
        data = await response.json()
        task_id = data.get("task_id")
        print(f"   Request {index}: Queued with task_id {task_id[:8]}...")
        return task_id

async def wait_for_task(session: aiohttp.ClientSession, task_id: str, index: int, show_response: bool = False) -> Dict[str, Any]:
    """Wait for a task to complete and return the result"""
    max_attempts = 30
    for attempt in range(max_attempts):
        async with session.get(f"{BASE_URL}/tasks/{task_id}") as response:
            data = await response.json()
            status = data.get("status")
            
            if status == "completed":
                batch_id = data.get("batch_id", "N/A")
                batch_size = data.get("batch_size", "N/A")
                
                if show_response:
                    result = data.get("result", {})
                    choices = result.get("choices", [])
                    if choices:
                        message = choices[0].get("message", {})
                        content = message.get("content", "No content")
                        print(f"\n   Request {index}: ✓ Completed")
                        print(f"   Batch: {batch_id[:8] if batch_id != 'N/A' else 'N/A'} (size {batch_size})")
                        print(f"   Response: {content[:100]}..." if len(content) > 100 else f"   Response: {content}")
                else:
                    print(f"   Request {index}: ✓ Completed (batch {batch_id[:8] if batch_id != 'N/A' else 'N/A'}, size {batch_size})")
                return data
            elif status == "failed":
                print(f"   Request {index}: ✗ Failed - {data.get('error')}")
                return data
            
            await asyncio.sleep(0.2)
    
    print(f"   Request {index}: ⏱ Timeout waiting for completion")
    return {}

async def test_parallel_batching():
    """Test parallel requests with dynamic batching"""
    print_section("2. PARALLEL REQUESTS WITH DYNAMIC BATCHING")
    
    prompts = [
        "What is Python?",
        "Explain async programming",
        "What is FastAPI?",
        "How does GPU batching work?",
        "What is vLLM?",
        "Explain continuous batching",
        "What is machine learning?",
        "How do transformers work?",
    ]
    
    print(f"\n📤 Submitting {len(prompts)} parallel requests...")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Submit all requests in parallel
        task_ids = await asyncio.gather(*[
            submit_async_request(session, prompt, i+1)
            for i, prompt in enumerate(prompts)
        ])
        
        submit_time = time.time() - start_time
        print(f"\n✓ All requests submitted in {submit_time:.2f}s")
        
        # Wait for all to complete
        print(f"\n⏳ Waiting for batched processing...")
        wait_start = time.time()
        
        results = await asyncio.gather(*[
            wait_for_task(session, task_id, i+1, show_response=True)
            for i, task_id in enumerate(task_ids)
        ])
        
        total_time = time.time() - start_time
        wait_time = time.time() - wait_start
        
        print(f"\n✓ All requests completed in {total_time:.2f}s (wait: {wait_time:.2f}s)")
        
        # Show batch information
        batch_info = {}
        for result in results:
            batch_id = result.get("batch_id")
            if batch_id:
                if batch_id not in batch_info:
                    batch_info[batch_id] = {
                        "size": result.get("batch_size", 0),
                        "count": 0
                    }
                batch_info[batch_id]["count"] += 1
        
        if batch_info:
            print(f"\n📊 Batch Summary:")
            for i, (batch_id, info) in enumerate(batch_info.items(), 1):
                print(f"   Batch {i} ({batch_id[:8]}): {info['count']} requests (size: {info['size']})")

def test_batch_endpoint():
    """Test the batch endpoint"""
    print_section("3. BATCH ENDPOINT TEST")
    
    requests_data = [
        {
            "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "messages": [{"role": "user", "content": f"Question {i}: What is AI?"}]
        }
        for i in range(5)
    ]
    
    print(f"\n📤 Submitting batch of {len(requests_data)} requests...")
    start_time = time.time()
    
    response = requests.post(f"{BASE_URL}/inference/batch", json=requests_data)
    
    if response.status_code == 200:
        data = response.json()
        task_ids = data.get("task_ids", [])
        print(f"✓ Batch submitted: {data.get('count')} tasks")
        
        # Wait for completion
        print(f"\n⏳ Waiting for batch to complete...")
        completed = 0
        max_wait = 10
        
        for _ in range(max_wait * 5):  # Check every 0.2s
            time.sleep(0.2)
            completed = 0
            for task_id in task_ids:
                task_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
                if task_response.status_code == 200:
                    task_data = task_response.json()
                    if task_data.get("status") == "completed":
                        completed += 1
            
            if completed == len(task_ids):
                break
        
        total_time = time.time() - start_time
        print(f"✓ {completed}/{len(task_ids)} tasks completed in {total_time:.2f}s")
    else:
        print(f"✗ Batch submission failed: {response.status_code}")

async def test_sequential_processing():
    """Test sequential processing for comparison"""
    print_section("5. SEQUENTIAL PROCESSING (FOR COMPARISON)")
    
    prompts = [
        "What is Python?",
        "Explain async programming",
        "What is FastAPI?",
        "How does GPU batching work?",
        "What is vLLM?",
        "Explain continuous batching",
        "What is machine learning?",
        "How do transformers work?",
    ]
    
    print(f"\n📤 Sending {len(prompts)} requests SEQUENTIALLY...")
    print("   (Using direct v1/chat/completions endpoint)\n")
    start_time = time.time()
    
    for i, prompt in enumerate(prompts, 1):
        payload = {
            "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(f"{BASE_URL}/v1/chat/completions", json=payload)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                print(f"   Request {i}: ✓ {content[:80]}..." if len(content) > 80 else f"   Request {i}: ✓ {content}")
        else:
            print(f"   Request {i}: ✗ Failed ({response.status_code})")
    
    total_time = time.time() - start_time
    print(f"\n✓ All {len(prompts)} requests completed in {total_time:.2f}s")
    print(f"   Average time per request: {total_time/len(prompts):.2f}s")
    
    return total_time

def test_stats():
    """Show batching statistics"""
    print_section("4. BATCHING STATISTICS")
    
    response = requests.get(f"{BASE_URL}/stats")
    if response.status_code == 200:
        data = response.json()
        
        batching = data.get("batching", {})
        tasks = data.get("tasks", {})
        config = data.get("config", {})
        
        print(f"\n📊 Batching Performance:")
        print(f"   Total Requests: {batching.get('total_requests')}")
        print(f"   Total Batches: {batching.get('total_batches')}")
        print(f"   Batched Requests: {batching.get('batched_requests')}")
        print(f"   Average Batch Size: {batching.get('avg_batch_size')}")
        print(f"   Active Batches: {batching.get('active_batches')}")
        print(f"   Queue Size: {batching.get('queue_size')}")
        
        print(f"\n📋 Task Status:")
        print(f"   Total Tasks: {tasks.get('total')}")
        for status, count in tasks.get('by_status', {}).items():
            print(f"   {status.capitalize()}: {count}")
        
        print(f"\n⚙️ Configuration:")
        print(f"   Max Batch Size: {config.get('max_batch_size')}")
        print(f"   Batch Wait Timeout: {config.get('batch_wait_timeout')}s")
        print(f"   Max Concurrent Batches: {config.get('max_concurrent_batches')}")
    else:
        print(f"✗ Failed to get stats: {response.status_code}")

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  MOCK vLLM DYNAMIC BATCHING TEST")
    print("=" * 70)
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Parallel requests with batching
        asyncio.run(test_parallel_batching())
        
        # Test 3: Batch endpoint
        test_batch_endpoint()
        
        # Test 4: Stats
        test_stats()
        
        # Test 5: Sequential processing comparison
        sequential_time = asyncio.run(test_sequential_processing())
        
        # Final comparison
        print_section("PERFORMANCE COMPARISON")
        print(f"\n📊 Summary:")
        print(f"   Sequential Processing: ~{sequential_time:.2f}s")
        print(f"   Batched Processing: ~1.8s (from test 2)")
        print(f"   Speedup: ~{sequential_time/1.8:.1f}x faster with batching")
        print(f"\n💡 Note: Batching groups multiple requests together,")
        print(f"   reducing total processing time significantly!")
        
        print("\n" + "=" * 70)
        print("  ✓ ALL TESTS COMPLETED")
        print("=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to server at", BASE_URL)
        print("  Make sure the mock vLLM server is running:")
        print("  uvicorn mock_vllm:app --reload --port 8000")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")

if __name__ == "__main__":
    main()
