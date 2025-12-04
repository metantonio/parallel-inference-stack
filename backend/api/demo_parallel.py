"""
Parallel Inference Demo

This script demonstrates parallel inference capabilities by:
1. Submitting multiple requests simultaneously
2. Showing concurrent processing
3. Comparing sequential vs parallel performance

Usage:
    1. Start parallel API: uvicorn demo_api_parallel:app --reload --port 8000
    2. Run this script: python demo_parallel.py
"""

import requests
import time
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_sequential():
    """Test sequential processing (one at a time)"""
    print_section("1. SEQUENTIAL PROCESSING (Baseline)")
    
    prompts = [
        "Count from 1 to 3",
        "What is 2+2?",
        "Say hello",
        "What is Python?",
        "Count from 10 to 12"
    ]
    
    print(f"Submitting {len(prompts)} requests sequentially...")
    start = time.time()
    
    results = []
    for i, prompt in enumerate(prompts, 1):
        print(f"  Request {i}/{len(prompts)}: '{prompt[:30]}...'")
        req_start = time.time()
        
        try:
            response = requests.post(
                f"{BASE_URL}/inference",
                json={"prompt": prompt, "temperature": 0.1},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                req_time = time.time() - req_start
                results.append({
                    "prompt": prompt,
                    "output": data["output"][:50],
                    "time": req_time
                })
                print(f"    ✓ Completed in {req_time:.2f}s")
            else:
                print(f"    ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    total_time = time.time() - start
    
    print(f"\n📊 Sequential Results:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average per request: {total_time/len(prompts):.2f}s")
    print(f"   Completed: {len(results)}/{len(prompts)}")
    
    return total_time

def test_async_parallel():
    """Test async parallel processing"""
    print_section("2. ASYNC PARALLEL PROCESSING")
    
    prompts = [
        "Count from 1 to 3",
        "What is 2+2?",
        "Say hello",
        "What is Python?",
        "Count from 10 to 12"
    ]
    
    print(f"Submitting {len(prompts)} requests in parallel (async mode)...")
    start = time.time()
    
    # Submit all tasks
    task_ids = []
    for i, prompt in enumerate(prompts, 1):
        print(f"  Submitting {i}/{len(prompts)}: '{prompt[:30]}...'")
        try:
            response = requests.post(
                f"{BASE_URL}/inference/async",
                json={"prompt": prompt, "temperature": 0.1},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                task_ids.append(data["task_id"])
                print(f"    ✓ Task ID: {data['task_id'][:8]}...")
            else:
                print(f"    ✗ Failed: {response.status_code}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    submit_time = time.time() - start
    print(f"\n✓ All tasks submitted in {submit_time:.2f}s")
    
    # Wait for completion
    print(f"\nWaiting for tasks to complete...")
    completed = 0
    max_wait = 120  # 2 minutes max
    check_start = time.time()
    
    while completed < len(task_ids) and (time.time() - check_start) < max_wait:
        completed = 0
        for task_id in task_ids:
            try:
                response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] in ["completed", "failed"]:
                        completed += 1
            except:
                pass
        
        if completed < len(task_ids):
            print(f"  Progress: {completed}/{len(task_ids)} completed", end="\r")
            time.sleep(1)
    
    total_time = time.time() - start
    
    print(f"\n\n📊 Async Parallel Results:")
    print(f"   Submission time: {submit_time:.2f}s")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Completed: {completed}/{len(task_ids)}")
    
    # Show results
    print(f"\n📝 Task Results:")
    for i, task_id in enumerate(task_ids, 1):
        try:
            response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = data["status"]
                if status == "completed":
                    output = data["result"]["output"][:40]
                    print(f"   {i}. ✓ {output}...")
                else:
                    print(f"   {i}. ✗ {status}")
        except Exception as e:
            print(f"   {i}. ✗ Error: {e}")
    
    return total_time

def test_batch():
    """Test batch processing"""
    print_section("3. BATCH PROCESSING")
    
    prompts = [
        "Count from 1 to 3",
        "What is 2+2?",
        "Say hello",
        "What is Python?",
        "Count from 10 to 12"
    ]
    
    print(f"Submitting {len(prompts)} requests as a batch...")
    start = time.time()
    
    # Prepare batch request
    batch_requests = [
        {"prompt": prompt, "temperature": 0.1}
        for prompt in prompts
    ]
    
    try:
        response = requests.post(
            f"{BASE_URL}/inference/batch",
            json=batch_requests,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            task_ids = data["task_ids"]
            submit_time = time.time() - start
            
            print(f"✓ Batch submitted in {submit_time:.2f}s")
            print(f"  Task IDs: {len(task_ids)}")
            
            # Wait for completion
            print(f"\nWaiting for batch to complete...")
            completed = 0
            max_wait = 120
            check_start = time.time()
            
            while completed < len(task_ids) and (time.time() - check_start) < max_wait:
                completed = 0
                for task_id in task_ids:
                    try:
                        response = requests.get(f"{BASE_URL}/tasks/{task_id}", timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            if data["status"] in ["completed", "failed"]:
                                completed += 1
                    except:
                        pass
                
                if completed < len(task_ids):
                    print(f"  Progress: {completed}/{len(task_ids)} completed", end="\r")
                    time.sleep(1)
            
            total_time = time.time() - start
            
            print(f"\n\n📊 Batch Results:")
            print(f"   Submission time: {submit_time:.2f}s")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Completed: {completed}/{len(task_ids)}")
            
            return total_time
        else:
            print(f"✗ Batch submission failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_stats():
    """Show processing statistics"""
    print_section("4. PROCESSING STATISTICS")
    
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            
            print(f"📊 Overall Statistics:")
            print(f"   Total tasks processed: {data['total_tasks']}")
            print(f"   Currently active: {data['active_tasks']}")
            print(f"   Max concurrent: {data['max_concurrent']}")
            
            if data.get('status_breakdown'):
                print(f"\n📈 Status Breakdown:")
                for status, count in data['status_breakdown'].items():
                    print(f"   {status}: {count}")
        else:
            print(f"✗ Failed to get stats: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  PARALLEL INFERENCE DEMONSTRATION")
    print("=" * 70)
    print("\nThis demonstrates parallel processing capabilities:")
    print("1. Sequential processing (baseline)")
    print("2. Async parallel processing")
    print("3. Batch processing")
    
    # Check if API is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ API is not healthy. Make sure it's running:")
            print("   uvicorn demo_api_parallel:app --reload --port 8000")
            return
    except:
        print("\n❌ Cannot connect to API. Make sure it's running:")
        print("   uvicorn demo_api_parallel:app --reload --port 8000")
        return
    
    # Run tests
    results = {}
    
    results['sequential'] = test_sequential()
    time.sleep(2)
    
    results['async'] = test_async_parallel()
    time.sleep(2)
    
    results['batch'] = test_batch()
    time.sleep(2)
    
    test_stats()
    
    # Summary
    print_section("PERFORMANCE COMPARISON")
    
    if all(results.values()):
        print(f"⏱️  Sequential: {results['sequential']:.2f}s (baseline)")
        print(f"⏱️  Async Parallel: {results['async']:.2f}s")
        print(f"⏱️  Batch: {results['batch']:.2f}s")
        
        if results['async'] < results['sequential']:
            speedup = results['sequential'] / results['async']
            print(f"\n🚀 Async is {speedup:.2f}x faster than sequential!")
        
        if results['batch'] < results['sequential']:
            speedup = results['sequential'] / results['batch']
            print(f"🚀 Batch is {speedup:.2f}x faster than sequential!")
    
    print("\n" + "=" * 70)
    print("✅ Demonstration complete!")
    print("\n💡 Note: Ollama processes requests sequentially internally,")
    print("   but this API can queue and manage multiple requests efficiently.")
    print("=" * 70)

if __name__ == "__main__":
    main()
