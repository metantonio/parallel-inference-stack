# Deployment Guide

This guide covers deployment strategies for both on-premise and AWS environments.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [On-Premise Production Deployment](#on-premise-production-deployment)
3. [AWS Migration Guide](#aws-migration-guide)
4. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Prerequisites

- Docker 20.10+ with Docker Compose
- NVIDIA GPU with CUDA 11.8+
- NVIDIA Docker runtime (`nvidia-docker2`)
- 16GB+ RAM
- 50GB+ free disk space

### Step 1: Install NVIDIA Docker Runtime

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Step 2: Clone and Configure

```bash
# Clone repository
git clone <your-repo-url>
cd paralell-test

# Create environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Step 3: Download Models

```bash
# Create models directory
mkdir -p models

# Download your model (example)
# Replace with your actual model download
wget https://your-model-url/model.pt -O models/model_latest.pt
```

### Step 4: Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### Step 5: Verify Deployment

```bash
# Check API health
curl http://localhost/health

# Check Ray dashboard
open http://localhost:8265

# Check Grafana
open http://localhost:3000
# Default credentials: admin/admin
```

### Step 6: Test Inference

```bash
# Submit test request
curl -X POST http://localhost/api/inference \
  -H "Content-Type: application/json" \
  -d '{
    "data": {"text": "Hello, world!"},
    "priority": "normal"
  }'

# Get result (replace TASK_ID)
curl http://localhost/api/inference/TASK_ID
```

---

## On-Premise Production Deployment

### Option 1: Docker Compose (Small Scale)

For deployments with 1-3 GPU servers.

#### Prerequisites

- Ubuntu 22.04 LTS
- NVIDIA GPUs with drivers installed
- Docker + NVIDIA runtime
- Static IP or domain name
- SSL certificate

#### Deployment Steps

1. **Prepare Server**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install NVIDIA Docker
# (see Local Development Setup)

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Configure Production Settings**

```bash
# Edit docker-compose.yml
# - Update resource limits
# - Configure SSL certificates
# - Set production passwords
# - Configure backup volumes

# Edit NGINX config for SSL
cp nginx/nginx.conf nginx/nginx.prod.conf
# Uncomment SSL section and configure
```

3. **Deploy**

```bash
# Pull images
docker-compose pull

# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
docker-compose ps
```

4. **Configure Monitoring**

```bash
# Access Grafana
open https://your-domain:3000

# Import dashboards from monitoring/grafana/dashboards/
```

---

### Option 2: Kubernetes (Large Scale)

For deployments with 4+ GPU servers or requiring high availability.

#### Prerequisites

- Kubernetes cluster 1.28+
- NVIDIA GPU Operator installed
- kubectl configured
- Helm 3.x
- Persistent storage (NFS, Ceph, or cloud storage)

#### Install NVIDIA GPU Operator

```bash
# Add NVIDIA Helm repository
helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
helm repo update

# Install GPU Operator
helm install --wait --generate-name \
  -n gpu-operator --create-namespace \
  nvidia/gpu-operator
```

#### Deploy Application

```bash
# Create namespace
kubectl create namespace ai-inference

# Create secrets
kubectl create secret generic app-secrets \
  --from-literal=postgres-password=YOUR_PASSWORD \
  --from-literal=s3-access-key=YOUR_KEY \
  --from-literal=s3-secret-key=YOUR_SECRET \
  -n ai-inference

# Create PVC for models
kubectl apply -f kubernetes/models-pvc.yaml

# Upload models to PVC
kubectl cp models/ ai-inference/model-uploader:/models/

# Deploy application
kubectl apply -f kubernetes/deployment.yaml

# Verify deployment
kubectl get pods -n ai-inference
kubectl get svc -n ai-inference
```

#### Configure Ingress

```bash
# Install NGINX Ingress Controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Update kubernetes/deployment.yaml with your domain
# Apply ingress
kubectl apply -f kubernetes/deployment.yaml
```

#### Configure Monitoring

```bash
# Install Prometheus Operator
helm install prometheus-operator prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

# Apply custom ServiceMonitors
kubectl apply -f monitoring/kubernetes/
```

---

## AWS Migration Guide

### Architecture Mapping

| On-Premise | AWS Service | Notes |
|------------|-------------|-------|
| Kubernetes | Amazon EKS | Managed Kubernetes |
| GPU Nodes | EC2 P3/P4/G5 | GPU instances |
| PostgreSQL | Amazon RDS | Managed PostgreSQL |
| Redis | ElastiCache | Managed Redis |
| MinIO | Amazon S3 | Object storage |
| NGINX | ALB + API Gateway | Load balancing |
| Prometheus | CloudWatch | Monitoring |

### Migration Steps

#### Phase 1: Setup AWS Infrastructure

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI
aws configure

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
```

#### Phase 2: Create EKS Cluster

```bash
# Create cluster with GPU nodes
eksctl create cluster \
  --name ai-inference-cluster \
  --region us-east-1 \
  --nodegroup-name gpu-workers \
  --node-type p3.2xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed \
  --asg-access

# Install NVIDIA device plugin
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml
```

#### Phase 3: Setup Managed Services

```bash
# Create RDS PostgreSQL
aws rds create-db-instance \
  --db-instance-identifier ai-inference-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username postgres \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 100 \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name your-subnet-group

# Create ElastiCache Redis
aws elasticache create-cache-cluster \
  --cache-cluster-id ai-inference-redis \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-xxxxx

# Create S3 bucket
aws s3 mb s3://ai-inference-models
aws s3 mb s3://ai-inference-results
```

#### Phase 4: Update Configuration

```bash
# Update ConfigMap with AWS endpoints
kubectl edit configmap app-config -n ai-inference

# Update:
# - DATABASE_URL to RDS endpoint
# - REDIS_URL to ElastiCache endpoint
# - S3_ENDPOINT to s3.amazonaws.com
```

#### Phase 5: Deploy to EKS

```bash
# Build and push Docker images to ECR
aws ecr create-repository --repository-name ai-inference-api
aws ecr create-repository --repository-name ai-inference-ray

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t ai-inference-api backend/api/
docker tag ai-inference-api:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-inference-api:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-inference-api:latest

# Update kubernetes/deployment.yaml with ECR image URLs
# Deploy
kubectl apply -f kubernetes/deployment.yaml
```

#### Phase 6: Configure Load Balancer

```bash
# Install AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=ai-inference-cluster

# Update Ingress to use ALB
kubectl annotate ingress api-ingress \
  kubernetes.io/ingress.class=alb \
  alb.ingress.kubernetes.io/scheme=internet-facing \
  -n ai-inference
```

#### Phase 7: Cutover

```bash
# Test AWS deployment
kubectl get ingress -n ai-inference
# Get ALB URL

# Test endpoint
curl https://your-alb-url/health

# Update DNS to point to ALB
# Monitor traffic shift
```

### Cost Optimization on AWS

```bash
# Use Spot Instances for GPU workers
eksctl create nodegroup \
  --cluster ai-inference-cluster \
  --name gpu-workers-spot \
  --node-type p3.2xlarge \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --spot

# Configure S3 lifecycle policies
aws s3api put-bucket-lifecycle-configuration \
  --bucket ai-inference-results \
  --lifecycle-configuration file://s3-lifecycle.json

# Use Reserved Instances for baseline capacity
aws ec2 purchase-reserved-instances-offering \
  --reserved-instances-offering-id xxxxx \
  --instance-count 2
```

---

## Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Check Kubernetes GPU
kubectl describe node | grep nvidia.com/gpu
```

### High Latency

```bash
# Check queue depth
curl http://localhost/api/metrics/queue

# Check GPU utilization
curl http://localhost/api/metrics/gpu

# Check Ray dashboard
open http://localhost:8265

# Scale workers
docker-compose up -d --scale gpu-worker=5
# or
kubectl scale deployment gpu-worker --replicas=5 -n ai-inference
```

### Out of Memory

```bash
# Check GPU memory
nvidia-smi

# Reduce batch size
# Edit docker-compose.yml or kubernetes/deployment.yaml
# Set BATCH_SIZE=16 (or lower)

# Restart workers
docker-compose restart gpu-worker-1
# or
kubectl rollout restart deployment gpu-worker -n ai-inference
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose logs postgres
kubectl logs -l app=postgres -n ai-inference

# Test connection
docker-compose exec api-1 python -c "from app.database import engine; engine.connect()"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

### Redis Connection Issues

```bash
# Check Redis
docker-compose logs redis
kubectl logs -l app=redis -n ai-inference

# Test connection
docker-compose exec api-1 python -c "from app.queue import redis_client; print(redis_client.ping())"

# Clear Redis
docker-compose exec redis redis-cli FLUSHALL
```

---

## Monitoring and Maintenance

### Daily Checks

```bash
# Check service health
curl http://localhost/health/detailed

# Check queue metrics
curl http://localhost/api/metrics/queue

# Check GPU metrics
curl http://localhost/api/metrics/gpu

# Check logs
docker-compose logs --tail=100 -f
kubectl logs -l app=api-server --tail=100 -f -n ai-inference
```

### Weekly Maintenance

```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Backup database
docker-compose exec postgres pg_dump -U postgres inference > backup.sql

# Clean up old data
docker-compose exec postgres psql -U postgres -d inference -c "DELETE FROM requests WHERE created_at < NOW() - INTERVAL '30 days'"

# Check disk usage
df -h
docker system df
```

### Scaling Guidelines

| Metric | Action |
|--------|--------|
| Queue depth > 100 | Add GPU workers |
| CPU > 80% | Add API replicas |
| Memory > 85% | Increase node size |
| GPU util < 50% | Reduce workers |
| Latency > 100ms | Check bottlenecks |

---

## Security Hardening

### Production Checklist

- [ ] Change all default passwords
- [ ] Enable SSL/TLS everywhere
- [ ] Configure firewall rules
- [ ] Enable authentication on all endpoints
- [ ] Set up VPN for internal services
- [ ] Configure backup encryption
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Configure rate limiting
- [ ] Enable CORS properly
- [ ] Use secrets management (Vault/AWS Secrets Manager)
- [ ] Regular security updates
- [ ] Penetration testing
- [ ] Compliance review (GDPR, HIPAA, etc.)

---

## Support

For issues and questions:
- Check logs: `docker-compose logs` or `kubectl logs`
- Review metrics: Grafana dashboard
- Check Ray dashboard: http://localhost:8265
- Consult architecture documentation: [architecture.md](./architecture.md)
