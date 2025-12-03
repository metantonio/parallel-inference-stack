# Running the Backend Locally (Without Docker)

This guide explains how to run the backend API locally for development without Docker.

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use SQLite for development)
- Redis 7+ (optional, for queue functionality)

## Quick Start (Development Mode)

### 1. Install Dependencies

```bash
cd backend/api
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in `backend/api/`:

```bash
# For local development with SQLite (no PostgreSQL needed)
DATABASE_URL=sqlite:///./dev.db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Configuration
JWT_SECRET_KEY=your-local-dev-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# S3 Storage (optional for local dev)
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# API Configuration
LOG_LEVEL=debug
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Create initial user (optional)
python -c "
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash
import uuid

db = SessionLocal()
user = User(
    id=str(uuid.uuid4()),
    username='admin',
    email='admin@example.com',
    hashed_password=get_password_hash('admin123'),
    is_active=True
)
db.add(user)
db.commit()
print('Admin user created: admin / admin123')
"
```

### 4. Run the API Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with specific workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## Running with PostgreSQL (Recommended for Production-like Setup)

### 1. Install and Start PostgreSQL

**Windows:**
```bash
# Download from https://www.postgresql.org/download/windows/
# Or use chocolatey
choco install postgresql

# Start PostgreSQL service
net start postgresql-x64-15
```

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux:**
```bash
sudo apt-get install postgresql-15
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE inference;

# Create user (optional)
CREATE USER inference_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE inference TO inference_user;

# Exit
\q
```

### 3. Update .env

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/inference
```

### 4. Run Migrations

```bash
alembic upgrade head
```

## Running Background Workers (Optional)

The queue functionality requires Redis and Celery workers.

### 1. Install and Start Redis

**Windows:**
```bash
# Download from https://github.com/microsoftarchive/redis/releases
# Or use chocolatey
choco install redis-64

# Start Redis
redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Start Celery Worker

```bash
# In a separate terminal
cd backend/api
celery -A app.queue worker --loglevel=info
```

## Troubleshooting

### Missing Dependencies

If you get `ModuleNotFoundError`, install missing packages:

```bash
pip install celery redis fastapi uvicorn sqlalchemy alembic pydantic-settings
```

### Database Connection Issues

**SQLite (easiest for development):**
```bash
DATABASE_URL=sqlite:///./dev.db
```

**PostgreSQL not running:**
```bash
# Check if PostgreSQL is running
# Windows
net start postgresql-x64-15

# macOS
brew services list

# Linux
sudo systemctl status postgresql
```

### Port Already in Use

If port 8000 is already in use:
```bash
uvicorn app.main:app --reload --port 8001
```

## Development Workflow

1. **Start the backend:**
   ```bash
   cd backend/api
   uvicorn app.main:app --reload
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Running Tests

```bash
cd backend/api
python run_tests.py
```

Tests use SQLite in-memory database, so no setup required!

## Production Deployment

For production, use Docker:

```bash
docker-compose up -d
```

See [README.md](../../README.md) for full deployment instructions.
