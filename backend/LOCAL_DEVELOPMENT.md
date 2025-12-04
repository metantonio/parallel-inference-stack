# Local Development with Ollama

This guide explains how to run the backend locally using Ollama for inference instead of Ray Serve GPU workers.

## Prerequisites

1. **Ollama Installation**
   - Download and install Ollama: https://ollama.ai/download
   - Ollama will automatically start as a service after installation

2. **Pull a Model**
   ```bash
   # Pull a model (choose one based on your needs)
   ollama pull llama2        # General purpose (3.8GB)
   ollama pull mistral       # Fast and capable (4.1GB)
   ollama pull codellama     # Code-focused (3.8GB)
   ollama pull llama2:13b    # Larger, more capable (7.3GB)
   ```

3. **Verify Ollama is Running**
   ```bash
   # Check if Ollama is accessible
   curl http://localhost:11434/api/tags
   ```

## Configuration

1. **Copy Environment File**
   ```bash
   cd backend/api
   cp .env.example .env
   ```

2. **Edit `.env` File**
   ```bash
   # Set inference mode to local
   INFERENCE_MODE=local
   
   # Configure Ollama settings
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2  # Use the model you pulled
   OLLAMA_TIMEOUT=120
   
   # For local development, you can use simpler services
   DATABASE_URL=sqlite:///./dev.db
   REDIS_URL=redis://localhost:6379/0
   CELERY_BROKER_URL=redis://localhost:6379/1
   CELERY_RESULT_BACKEND=redis://localhost:6379/2
   ```

## Running Locally

### Option 1: Without Docker (Recommended for Development)

1. **Install Dependencies**
   ```bash
   cd backend/api
   pip install -r requirements.txt
   ```

2. **Start Redis** (required for task queue)
   ```bash
   # Using Docker
   docker run -d -p 6379:6379 redis:alpine
   
   # Or install Redis locally
   # Windows: https://github.com/microsoftarchive/redis/releases
   # Mac: brew install redis && brew services start redis
   # Linux: sudo apt-get install redis-server
   ```

3. **Initialize Database**
   ```bash
   python init_db.py
   ```

4. **Start Celery Worker** (in one terminal)
   ```bash
   celery -A app.queue.celery_app worker --loglevel=info
   ```

5. **Start FastAPI Server** (in another terminal)
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Test the Setup**
   ```bash
   # Test Ollama worker directly
   python test_ollama_worker.py
   
   # Access API docs
   # Open http://localhost:8000/docs
   ```

### Option 2: With Docker Compose (Production-like)

1. **Update `docker-compose.yml`** to use local mode
   ```yaml
   environment:
     - INFERENCE_MODE=local
     - OLLAMA_BASE_URL=http://host.docker.internal:11434  # Access host's Ollama
   ```

2. **Start Services**
   ```bash
   docker-compose up
   ```

## Testing Inference

### Using the API

1. **Get Access Token**
   ```bash
   curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=testpass"
   ```

2. **Submit Inference Request**
   ```bash
   curl -X POST "http://localhost:8000/inference" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "data": {
         "prompt": "Explain what is machine learning in one sentence."
       },
       "priority": "normal"
     }'
   ```

3. **Check Result**
   ```bash
   curl -X GET "http://localhost:8000/inference/TASK_ID" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### Using the Test Script

```bash
cd backend/api
python test_ollama_worker.py
```

## Switching Between Modes

### Local Mode (Ollama)
```bash
# In .env
INFERENCE_MODE=local
```
- Uses Ollama running on localhost
- No GPU required
- Good for development and testing
- Restart backend after changing

### Production Mode (Ray Serve)
```bash
# In .env
INFERENCE_MODE=production
```
- Uses Ray Serve with GPU workers
- Requires Ray cluster running
- Production deployment
- Restart backend after changing

## Troubleshooting

### Ollama Not Found
```
Error: Ollama health check failed
```
**Solution**: Make sure Ollama is installed and running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama (if not running)
# It should auto-start, but you can manually start it from the app
```

### Model Not Found
```
Warning: Model 'llama2' not found in Ollama
```
**Solution**: Pull the model
```bash
ollama pull llama2
```

### Redis Connection Error
```
Error: Redis connection refused
```
**Solution**: Start Redis
```bash
docker run -d -p 6379:6379 redis:alpine
```

### Celery Worker Not Processing Tasks
**Solution**: Make sure Celery worker is running
```bash
celery -A app.queue.celery_app worker --loglevel=info
```

## Performance Considerations

### Local Mode (Ollama)
- **Pros**: Easy setup, no GPU required, good for development
- **Cons**: Slower than GPU inference, single-threaded
- **Best for**: Development, testing, small workloads

### Production Mode (Ray Serve)
- **Pros**: Fast GPU inference, parallel processing, scalable
- **Cons**: Requires GPU, more complex setup
- **Best for**: Production, high throughput, large workloads

## Next Steps

1. Test the local setup with the test script
2. Submit inference requests via the API
3. Monitor logs for any issues
4. When ready for production, switch to `INFERENCE_MODE=production`
