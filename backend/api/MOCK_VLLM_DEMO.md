uvicorn mock_vllm:app --port 8001
uvicorn demo_api_parallel:app --reload --port 8000
npm run dev

New Features:

🔐 Authentication (from previous update)

Database-backed user login via /token endpoint
⚡ Dynamic Batching (new)

Simulates vLLM's continuous batching for GPU efficiency
Configurable batch size (default: 32), wait timeout (0.1s), and concurrent batches (4)
Background processor automatically groups requests
📡 New Endpoints:

POST /inference/async - Submit request, get task_id immediately
POST /inference/batch - Submit multiple requests at once
GET /tasks/{task_id} - Check task status and results
GET /tasks - List all tasks
GET /stats - View batching performance metrics
📊 Testing: Created test_batching.py to demonstrate:

Parallel request submission (8 concurrent requests)
Batch processing performance
Real-time statistics monitoring
Performance Example:

Sequential: 8 requests × 0.5s = 4.0s
Batched: 2 batches × 0.9s = ~1.8s (2.2x faster)
You can now test parallel GPU batching locally!

## Test Configuration (Optional)
You can adjust batching parameters via environment variables before starting:

```bash
# Windows PowerShell
$env:VLLM_MAX_BATCH_SIZE="16"
$env:VLLM_BATCH_WAIT_TIMEOUT="0.2"
uvicorn mock_vllm:app --reload --port 8001
```
Test:

```bash
cd .\backend\api
$env:VLLM_MAX_BATCH_SIZE="16"
$env:VLLM_BATCH_WAIT_TIMEOUT="0.2"
uvicorn mock_vllm:app --reload --port 8001

cd .\backend\api
python test_batching.py