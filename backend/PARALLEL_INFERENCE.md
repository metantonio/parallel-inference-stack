# Parallel Inference Capabilities

## Summary

**Current Demo (`demo_api.py`)**: ❌ **Sequential** - Processes one request at a time

**Enhanced Demo (`demo_api_parallel.py`)**: ✅ **Parallel** - Can handle multiple concurrent requests

---

## Understanding Parallel Inference

### Ollama's Limitation

**Important**: Ollama itself processes requests **sequentially** (one at a time). This is a limitation of Ollama, not our API.

However, we can still achieve parallelism at the **API level**:

### What We Can Parallelize

1. **Request Handling**: Accept multiple requests simultaneously
2. **Task Queuing**: Queue requests efficiently
3. **Async Processing**: Process tasks in the background
4. **Batch Submission**: Submit multiple requests at once

### What We Cannot Parallelize (with single Ollama instance)

- ❌ Actual LLM inference (Ollama limitation)
- ❌ GPU utilization (single model loaded)

---

## Parallel API Features

### 1. Async Mode

Submit a request and get task_id immediately:

```python
POST /inference/async
{
  "prompt": "What is Python?"
}

Response:
{
  "task_id": "abc-123",
  "status": "queued",
  "message": "Task queued"
}
```

Then check status:

```python
GET /tasks/abc-123

Response:
{
  "task_id": "abc-123",
  "status": "completed",
  "result": {...}
}
```

### 2. Batch Processing

Submit multiple requests at once:

```python
POST /inference/batch
[
  {"prompt": "Request 1"},
  {"prompt": "Request 2"},
  {"prompt": "Request 3"}
]

Response:
{
  "task_ids": ["id1", "id2", "id3"],
  "count": 3
}
```

### 3. Concurrent Request Handling

The API can accept and queue up to `MAX_CONCURRENT_REQUESTS` (default: 5) requests simultaneously.

---

## True Parallel Inference (Production)

For **true parallel inference** across multiple GPUs/workers, you need the **full production stack**:

### Production Setup (Ray Serve)

```
┌─────────────────────────────────────────┐
│         FastAPI API                     │
│  (Handles requests, authentication)     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Redis + Celery                  │
│     (Task queue, load balancing)        │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┬─────────┐
        │                   │         │
┌───────▼────────┐  ┌──────▼──────┐  │
│  Ray Worker 1  │  │ Ray Worker 2│  │...
│  (GPU 1)       │  │  (GPU 2)    │  │
└────────────────┘  └─────────────┘  │
```

**Benefits**:
- ✅ Multiple GPUs processing simultaneously
- ✅ True parallel inference
- ✅ Load balancing across workers
- ✅ Horizontal scaling

**Requirements**:
- Redis (task queue)
- Celery (worker management)
- Ray Serve (GPU worker orchestration)
- Multiple GPUs

---

## Local Parallel Demo

### Start Parallel API

```bash
# Stop current demo if running
# Ctrl+C in the terminal running demo_api.py

# Start parallel version
cd backend/api
uvicorn demo_api_parallel:app --reload --port 8000
```

### Run Parallel Demo

```bash
python demo_parallel.py
```

This will demonstrate:
1. Sequential processing (baseline)
2. Async parallel request handling
3. Batch processing
4. Performance comparison

---

## Performance Expectations

### With Single Ollama Instance

**Sequential**: 5 requests × 10s each = **50 seconds**

**Async/Parallel API**: 
- Submission: ~1 second (all requests queued)
- Processing: Still ~50 seconds (Ollama processes sequentially)
- **Total**: ~51 seconds

**Benefit**: Non-blocking API, better user experience, but same total processing time.

### With Production Setup (Multiple GPUs)

**3 GPUs with Ray Serve**:
- 5 requests distributed across 3 workers
- Worker 1: 2 requests × 10s = 20s
- Worker 2: 2 requests × 10s = 20s  
- Worker 3: 1 request × 10s = 10s
- **Total**: ~20 seconds (2.5x speedup!)

---

## Comparison Table

| Feature | Simple Demo | Parallel Demo | Production (Ray) |
|---------|-------------|---------------|------------------|
| Async requests | ❌ | ✅ | ✅ |
| Task queuing | ❌ | ✅ | ✅ |
| Batch submission | ❌ | ✅ | ✅ |
| True parallel inference | ❌ | ❌ | ✅ |
| Multiple GPUs | ❌ | ❌ | ✅ |
| Redis required | ❌ | ❌ | ✅ |
| Horizontal scaling | ❌ | ❌ | ✅ |

---

## Files

### APIs

- [demo_api.py](file:///c:/Repositorios/paralell-test/backend/api/demo_api.py) - Simple sequential API
- [demo_api_parallel.py](file:///c:/Repositorios/paralell-test/backend/api/demo_api_parallel.py) - Parallel-capable API

### Tests

- [demo_client.py](file:///c:/Repositorios/paralell-test/backend/api/demo_client.py) - Simple API tests
- [demo_parallel.py](file:///c:/Repositorios/paralell-test/backend/api/demo_parallel.py) - Parallel processing demo

### Production

- [main.py](file:///c:/Repositorios/paralell-test/backend/api/app/main.py) - Full production API
- [queue.py](file:///c:/Repositorios/paralell-test/backend/api/app/queue.py) - Celery task queue
- [ray_worker.py](file:///c:/Repositorios/paralell-test/backend/workers/ray_worker.py) - Ray Serve GPU workers

---

## Recommendations

### For Local Development

Use **`demo_api_parallel.py`**:
- ✅ Async request handling
- ✅ Task queuing
- ✅ Batch processing
- ✅ No Redis required
- ✅ Good for testing API design

### For Production

Use **full stack** (main.py + Ray Serve):
- ✅ True parallel inference
- ✅ Multiple GPUs
- ✅ Horizontal scaling
- ✅ Load balancing
- ✅ Production-ready

---

## Next Steps

1. **Try Parallel Demo**:
   ```bash
   uvicorn demo_api_parallel:app --reload --port 8000
   python demo_parallel.py
   ```

2. **For Production**: Install Redis and set up Ray Serve for true parallel inference across multiple GPUs

3. **Hybrid Approach**: Use parallel API locally for development, switch to Ray Serve for production
