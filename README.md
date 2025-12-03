# AI Inference System by Antonio Martínez @metantonio

A production-ready, scalable AI inference system designed for parallel GPU processing with thousands of concurrent requests. Deploy on-premise and migrate seamlessly to AWS.

```mermaid
graph TB
    subgraph "Client Layer"
        UI[React Frontend]
    end
    
    subgraph "Gateway Layer"
        LB[NGINX Load Balancer]
        RL[Rate Limiter]
    end
    
    subgraph "API Layer"
        API1[FastAPI Server 1]
        API2[FastAPI Server 2]
        API3[FastAPI Server 3]
    end
    
    subgraph "Queue Layer"
        Redis[(Redis Queue)]
        PQ[Priority Queue]
    end
    
    subgraph "Worker Layer"
        Ray[Ray Serve Cluster]
        W1[GPU Worker 1<br/>GPU:0]
        W2[GPU Worker 2<br/>GPU:1]
        W3[GPU Worker 3<br/>GPU:2]
    end
    
    subgraph "Storage Layer"
        PG[(PostgreSQL)]
        Cache[(Redis Cache)]
        S3[(MinIO/S3)]
    end
    
    subgraph "Monitoring Layer"
        Prom[Prometheus]
        Graf[Grafana]
        DCGM[NVIDIA DCGM]
    end
    
    UI --> LB
    LB --> RL
    RL --> API1 & API2 & API3
    API1 & API2 & API3 --> Redis
    Redis --> PQ
    PQ --> Ray
    Ray --> W1 & W2 & W3
    
    API1 & API2 & API3 --> PG
    API1 & API2 & API3 --> Cache
    W1 & W2 & W3 --> S3
    
    W1 & W2 & W3 --> Prom
    API1 & API2 & API3 --> Prom
    Prom --> Graf
    W1 & W2 & W3 --> DCGM
    DCGM --> Prom
```

## 🚀 Features

- ✅ **Parallel GPU Processing**: Distribute workload across multiple GPUs automatically
- ✅ **High Throughput**: Handle 1000+ requests per second
- ✅ **Auto-Scaling**: Horizontal scaling based on load
- ✅ **Fault Tolerant**: Automatic retry, circuit breakers, and self-healing
- ✅ **Priority Queues**: High/Normal/Low priority request handling
- ✅ **Real-time Monitoring**: Prometheus + Grafana dashboards
- ✅ **Cloud Ready**: Zero-code migration to AWS
- ✅ **Production Grade**: Complete monitoring, logging, and security

## 📋 Table of Contents

- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Monitoring](#monitoring)
- [AWS Migration](#aws-migration)
- [Contributing](#contributing)

## 🏗️ Architecture

The system follows a microservices architecture with clear separation of concerns:

```
┌─────────────┐
│   Client    │
│  (React)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   NGINX     │  Load Balancer
│   Gateway   │  Rate Limiting
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   FastAPI Servers       │  Request Validation
│   (3+ replicas)         │  Authentication
└──────┬──────────────────┘
       │
       ▼
┌─────────────┐
│   Redis     │  Task Queue
│   Queue     │  Priority Queues
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   Ray Serve Cluster     │  GPU Orchestration
│   ┌─────┬─────┬─────┐   │  Dynamic Batching
│   │GPU 0│GPU 1│GPU 2│   │  Load Balancing
│   └─────┴─────┴─────┘   │
└─────────────────────────┘
```

**Key Components:**
- **Frontend**: React + TypeScript + Tailwind CSS
- **API Gateway**: NGINX with rate limiting
- **Backend**: FastAPI (Python) with async support
- **Queue**: Redis Streams + Celery
- **GPU Workers**: Ray Serve with automatic batching
- **Storage**: PostgreSQL + Redis + S3-compatible (MinIO)
- **Monitoring**: Prometheus + Grafana + NVIDIA DCGM

See [Architecture Documentation](docs/architecture.md) for details.

## 🛠️ Technology Stack

### Frontend
- React 18 + TypeScript
- Tailwind CSS
- React Query (TanStack Query)
- Vite

### Backend
- Python 3.11+
- FastAPI
- Celery
- asyncio

### GPU Processing
- Ray Serve
- PyTorch
- CUDA 11.8+

### Infrastructure
- Docker + Docker Compose
- Kubernetes (optional)
- NGINX

### Storage
- PostgreSQL 15
- Redis 7
- MinIO (S3-compatible)

### Monitoring
- Prometheus
- Grafana
- Loki
- NVIDIA DCGM

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ with Docker Compose
- NVIDIA GPU with CUDA 11.8+
- NVIDIA Docker runtime
- 16GB+ RAM
- 50GB+ free disk space

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/metantonio/parallel-inference-stack
cd paralell-test
```

2. **Install NVIDIA Docker Runtime**

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Download models**

```bash
mkdir -p models
# Place your model files in ./models/
```

5. **Start the system**

```bash
docker-compose up -d
```

6. **Verify deployment**

```bash
# Check health
curl http://localhost/health

# Access services
# - API: http://localhost/api
# - Frontend: http://localhost:5173
# - Ray Dashboard: http://localhost:8265
# - Grafana: http://localhost:3000 (admin/admin)
```

### Test Inference

```bash
# Submit request
curl -X POST http://localhost/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"text": "Hello, world!"},
    "priority": "normal"
  }'

# Response
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "queue_position": 1,
  "estimated_wait_time": 2
}

# Get result
curl http://localhost/api/inference/550e8400-e29b-41d4-a716-446655440000
```

## 📚 Deployment

### Local Development

See [Quick Start](#quick-start) above.

### On-Premise Production

**Option 1: Docker Compose** (1-3 GPU servers)

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Option 2: Kubernetes** (4+ GPU servers)

```bash
# Create namespace
kubectl create namespace ai-inference

# Deploy application
kubectl apply -f kubernetes/deployment.yaml

# Verify
kubectl get pods -n ai-inference
```

See [Deployment Guide](docs/deployment.md) for detailed instructions.

### AWS Deployment

The system is designed for seamless AWS migration:

```bash
# Create EKS cluster
eksctl create cluster -f kubernetes/eks-cluster.yaml

# Deploy to EKS
kubectl apply -f kubernetes/deployment.yaml

# Update endpoints (RDS, ElastiCache, S3)
kubectl edit configmap app-config -n ai-inference
```

**Component Mapping:**
- Kubernetes → Amazon EKS
- GPU Nodes → EC2 P3/P4/G5
- PostgreSQL → Amazon RDS
- Redis → ElastiCache
- MinIO → Amazon S3
- NGINX → ALB + API Gateway

See [AWS Migration Guide](docs/deployment.md#aws-migration-guide) for details.

## 📖 API Documentation

### Submit Inference

```http
POST /api/inference
Content-Type: application/json

{
  "data": {"text": "Your input"},
  "priority": "normal",
  "timeout": 60
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "queued",
  "queue_position": 1,
  "estimated_wait_time": 2
}
```

### Get Result

```http
GET /api/inference/{task_id}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "result": {...},
  "processing_time": 1.23
}
```

### Batch Inference

```http
POST /api/inference/batch
Content-Type: application/json

[
  {"data": {"text": "Input 1"}, "priority": "normal"},
  {"data": {"text": "Input 2"}, "priority": "high"}
]
```

**Interactive Documentation:**
- Swagger UI: http://localhost/api/docs
- ReDoc: http://localhost/api/redoc

## 📊 Monitoring

### Grafana Dashboards

Access Grafana at http://localhost:3000 (admin/admin)

**Available Dashboards:**
- System Overview
- API Performance
- GPU Utilization
- Queue Health
- Error Rates

### Prometheus Metrics

Access Prometheus at http://localhost:9090

**Key Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `queue_depth` - Current queue depth
- `gpu_utilization` - GPU utilization %
- `gpu_memory_used` - GPU memory usage

### Ray Dashboard

Access Ray Dashboard at http://localhost:8265

**Features:**
- Cluster status
- Worker health
- Task execution
- Resource utilization

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/1

# S3 Storage
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Ray
RAY_ADDRESS=ray-head:10001

# GPU Settings
BATCH_SIZE=32
MAX_BATCH_WAIT_MS=100
MODEL_PATH=/models
```

### Scaling

**Horizontal Scaling:**

```bash
# Docker Compose
docker-compose up -d --scale api-server=5 --scale gpu-worker=6

# Kubernetes
kubectl scale deployment api-server --replicas=5 -n ai-inference
kubectl scale deployment gpu-worker --replicas=6 -n ai-inference
```

**Auto-Scaling (Kubernetes):**

HPA is configured to scale based on:
- CPU utilization > 70%
- Memory utilization > 80%
- Queue depth > 100

## 🔒 Security

### Authentication

The API uses JWT tokens for authentication:

```bash
# Get token
curl -X POST http://localhost/api/auth/login \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer <token>" \
  http://localhost/api/inference
```

### SSL/TLS

For production, configure SSL in NGINX:

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... rest of config
}
```

### Secrets Management

Use environment variables or secrets management:

```bash
# Kubernetes
kubectl create secret generic app-secrets \
  --from-literal=db-password=xxx \
  -n ai-inference

# Docker Compose
# Use .env file (not committed to git)
```

## 🧪 Testing

### Unit Tests

```bash
# Backend
cd backend/api
pytest tests/

# Frontend
cd frontend
npm test
```

### Load Testing

```bash
# Install k6
brew install k6  # macOS
# or download from https://k6.io

# Run load test
k6 run tests/load-test.js
```

### Integration Tests

```bash
# Run full integration test suite
./scripts/integration-test.sh
```

## 📈 Performance

**Benchmarks** (3x NVIDIA V100 GPUs):

| Metric | Value |
|--------|-------|
| Throughput | 1200 req/s |
| Latency (p50) | 45ms |
| Latency (p95) | 120ms |
| Latency (p99) | 250ms |
| GPU Utilization | 85% |
| Max Concurrent | 5000+ |

## 🗺️ Roadmap

- [x] Core inference system
- [x] Multi-GPU support
- [x] Auto-scaling
- [x] Monitoring & logging
- [x] AWS migration guide
- [ ] Model versioning & A/B testing
- [ ] WebSocket support for real-time updates
- [ ] Multi-model serving
- [ ] Advanced caching strategies
- [ ] Cost optimization tools

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## 🙏 Acknowledgments

- Ray Team for Ray Serve
- FastAPI Team
- NVIDIA for CUDA and GPU support
- Open source community

---

**Built with ❤️ for high-performance AI inference**
