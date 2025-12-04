# Mock vLLM Server - Batching Proxy with Real vLLM Support

## Overview

The `mock_vllm.py` server now supports **two modes**:

1. **Mock Mode** (default): Returns simulated responses for testing batching logic
2. **Real vLLM Mode**: Acts as a batching proxy that forwards requests to a real vLLM server

## Quick Start

### Option 1: Mock Mode (No GPU Required)

```bash
# Start the mock server
uvicorn mock_vllm:app --port 8001

# Run tests
python test_batching.py
```

### Option 2: Real vLLM Mode (Requires GPU)

#### Step 1: Start Real vLLM Server

```bash
# Install vLLM (if not installed)
pip install vllm

# Start vLLM server on port 8002
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-7B-Instruct \
    --port 8002 \
    --max-model-len 4096
```

#### Step 2: Start Batching Proxy

```bash
# Windows PowerShell
$env:USE_REAL_VLLM="true"
$env:REAL_VLLM_URL="http://localhost:8002"
uvicorn mock_vllm:app --port 8001

# Linux/Mac
export USE_REAL_VLLM=true
export REAL_VLLM_URL=http://localhost:8002
uvicorn mock_vllm:app --port 8001
```

#### Step 3: Run Tests

```bash
python test_batching.py
```

## Configuration

### Environment Variables

```bash
# Batching Configuration
VLLM_MAX_BATCH_SIZE=32              # Max requests per batch
VLLM_BATCH_WAIT_TIMEOUT=0.1         # Seconds to wait for batch to fill
VLLM_MAX_CONCURRENT_BATCHES=4       # Parallel batch processing limit

# Real vLLM Connection (only when USE_REAL_VLLM=true)
USE_REAL_VLLM=true                  # Enable real vLLM mode
REAL_VLLM_URL=http://localhost:8002 # Real vLLM server URL
REAL_VLLM_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct  # Model name
```

## How It Works

### Mock Mode
- Returns simulated responses instantly
- Simulates batching delays
- Perfect for testing batching logic without GPU

### Real vLLM Mode
- Forwards requests to real vLLM server
- vLLM handles its own internal continuous batching
- Returns actual LLM responses
- Falls back to mock if vLLM is unavailable

## Testing

The `test_batching.py` script demonstrates:

1. **Health Check**: Shows server mode and configuration
2. **Parallel Batching**: 8 concurrent requests with batching
3. **Batch Endpoint**: Submit multiple requests at once
4. **Statistics**: View batching performance metrics
5. **Sequential Comparison**: Compare batched vs sequential processing

### Expected Output

**Mock Mode:**
```
Response: [Batched mock response a1b2c3d4] Mock response to: What is Python?
```

**Real vLLM Mode:**
```
Response: Python is a high-level, interpreted programming language...
```

## API Endpoints

### Authentication
- `POST /token` - User login (database-backed)

### Async Inference
- `POST /inference/async` - Submit request for batching, returns task_id
- `GET /tasks/{task_id}` - Check task status and get results
- `GET /tasks` - List all tasks

### Batch Processing
- `POST /inference/batch` - Submit multiple requests at once

### Monitoring
- `GET /health` - Health check with batching stats
- `GET /stats` - Detailed batching performance metrics

### vLLM-Compatible
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `POST /v1/completions` - Text completion
- `GET /v1/models` - List models

## Performance Benefits

### Sequential Processing (without batching)
- 8 requests × 0.5s each = **4.0s total**

### Batched Processing (with batching)
- Batch 1: 4 requests in 0.9s
- Batch 2: 4 requests in 0.9s
- Total: **~1.8s** (2.2x faster)

## Architecture

```
Client → mock_vllm.py (Port 8001) → Real vLLM (Port 8002)
         [Batching Proxy]              [GPU Inference]
```

**Benefits:**
- ✅ Automatic request batching
- ✅ Real LLM responses (when enabled)
- ✅ Fallback to mock if vLLM fails
- ✅ Statistics and monitoring
- ✅ Database-backed authentication

## Troubleshooting

### vLLM Connection Failed
If you see "Mock fallback" responses when `USE_REAL_VLLM=true`:

1. Check vLLM server is running: `curl http://localhost:8002/v1/models`
2. Verify `REAL_VLLM_URL` matches your vLLM server port
3. Check vLLM server logs for errors

### No Batching Observed
- Increase `VLLM_BATCH_WAIT_TIMEOUT` to allow more time for batch formation
- Submit more concurrent requests
- Check `/stats` endpoint for batching metrics

## Complete Example

```bash
# Terminal 1: Start real vLLM
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-7B-Instruct \
    --port 8002

# Terminal 2: Start batching proxy
$env:USE_REAL_VLLM="true"
$env:REAL_VLLM_URL="http://localhost:8002"
uvicorn mock_vllm:app --port 8001

# Terminal 3: Run tests
python test_batching.py
```

You'll see:
- Real LLM responses instead of mocks
- Batching statistics showing multiple requests grouped
- Performance comparison between batched and sequential processing