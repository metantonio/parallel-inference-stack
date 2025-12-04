from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Inference API"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "*"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/inference"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    
    # Storage
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_MODELS: str = "models"
    S3_BUCKET_RESULTS: str = "results"
    
    # Ray Configuration
    RAY_ADDRESS: str = "ray-head:10001"
    
    # GPU Worker Configuration
    MODEL_PATH: str = "/models"
    BATCH_SIZE: int = 32
    MAX_BATCH_WAIT_MS: int = 100
    CUDA_VISIBLE_DEVICES: str = "0"
    
    # API Configuration
    WORKERS: int = 4
    
    # Authentication
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    GRAFANA_ADMIN_USER: str = "admin"
    GRAFANA_ADMIN_PASSWORD: str = "admin"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

settings = Settings()
