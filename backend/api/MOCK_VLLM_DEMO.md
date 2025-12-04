# Mock vLLM Server - Batching Proxy with Real vLLM Support

## Overview

The `mock_vllm.py` server supports **two modes**:

1. **Mock Mode** (default): Returns simulated responses for testing batching logic
2. **Real vLLM Mode**: Acts as a batching proxy that forwards requests to a real vLLM server

## Quick Start

### Option 1: Mock Mode (No GPU Required - Works on Windows)

```powershell
# Start the mock server
uvicorn mock_vllm:app --port 8001

# Run tests
python test_batching.py
```

### Option 2: Real vLLM Mode (Requires GPU)

> **⚠️ WINDOWS COMPATIBILITY**  
> vLLM does **not** support Windows natively. Choose one of these options:

#### A) Use WSL2 (Recommended for Windows Users)

```powershell
# 1. Install WSL2 (if not already installed)
wsl --install
# Restart computer

# 2. In WSL2 Ubuntu terminal:
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen2.5-Coder-7B-Instruct \
    --port 8002 \
    --host 0.0.0.0

# 3. In Windows PowerShell:
$env:USE_REAL_VLLM="true"
$env:REAL_VLLM_URL="http://localhost:8002"
uvicorn mock_vllm:app --port 8001
```

#### B) Use Docker

```powershell
# 1. Pull and run vLLM container
docker run --gpus all -p 8002:8000 `
    vllm/vllm-openai:latest `
    --model Qwen/Qwen2.5-Coder-7B-Instruct

# 2. Start batching proxy
$env:USE_REAL_VLLM="true"
$env:REAL_VLLM_URL="http://localhost:8002"
uvicorn mock_vllm:app --port 8001
```

#### C) Use Remote vLLM Server

```powershell
# Connect to vLLM running on Linux server or cloud GPU
$env:USE_REAL_VLLM="true"
$env:REAL_VLLM_URL="http://your-server-ip:8002"
uvicorn mock_vllm:app --port 8001
```

#### D) Stay in Mock Mode (Recommended for Local Development)

```powershell
# No vLLM needed - perfect for testing batching logic
uvicorn mock_vllm:app --port 8001
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
REAL_VLLM_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

## How It Works

### Mock Mode
- ✅ Returns simulated responses instantly
- ✅ Simulates batching delays
- ✅ Perfect for testing batching logic without GPU
- ✅ **Works on Windows**

### Real vLLM Mode
- ✅ Forwards requests to real vLLM server
- ✅ vLLM handles its own internal continuous batching
- ✅ Returns actual LLM responses
- ✅ Falls back to mock if vLLM is unavailable
- ⚠️ **Requires Linux/WSL2/Docker**

## Testing

Run the test script:
```powershell
python test_batching.py
```

The script demonstrates:
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

### "pip install vllm" fails on Windows
**Solution**: vLLM doesn't support Windows. Use WSL2, Docker, or stay in Mock Mode.

### vLLM Connection Failed
If you see "Mock fallback" responses when `USE_REAL_VLLM=true`:

1. Check vLLM server is running: `curl http://localhost:8002/v1/models`
2. Verify `REAL_VLLM_URL` matches your vLLM server port
3. Check vLLM server logs for errors

### No Batching Observed
- Increase `VLLM_BATCH_WAIT_TIMEOUT` to allow more time for batch formation
- Submit more concurrent requests
- Check `/stats` endpoint for batching metrics

## Recommended Setup for Windows

**For Development/Testing:**
```powershell
# Use Mock Mode - no GPU or Linux required
uvicorn mock_vllm:app --port 8001
python test_batching.py
```

**For Production with Real LLM:**
1. Deploy vLLM on Linux server or cloud GPU (AWS, GCP, Azure)
2. Point `REAL_VLLM_URL` to that server
3. Run batching proxy on Windows

This gives you the best of both worlds: develop on Windows, deploy vLLM on Linux!