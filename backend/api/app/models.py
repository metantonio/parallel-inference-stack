from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum, Boolean
from datetime import datetime
import enum
from .database import Base

class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class InferenceRequest(Base):
    __tablename__ = "inference_requests"

    task_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    status = Column(String, default=TaskStatus.QUEUED)
    priority = Column(String, default="normal")
    model_version = Column(String, nullable=True)
    input_data = Column(JSON)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

