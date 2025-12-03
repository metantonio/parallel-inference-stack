from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum
from datetime import datetime
import enum
from .database import Base

class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

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

class InferenceResponse(Base):
    # This seems to be unused in main.py imports but was referenced. 
    # Keeping it simple or we can remove if not needed by SQLAlchemy.
    # Based on main.py, InferenceResponse is imported from .models but 
    # used as a return type annotation which usually implies a Pydantic model 
    # or it might be a mistake in main.py imports mixing Pydantic/ORM.
    # However, main.py defines InferenceResponsePayload (Pydantic).
    # Let's define a dummy class if needed or just skip.
    # Looking at main.py: `from .models import InferenceRequest, InferenceResponse, TaskStatus`
    # It uses InferenceResponsePayload for the endpoint response model.
    # It uses InferenceResponse nowhere in the code shown in main.py.
    # It might be a leftover. I will define it as a pass to avoid import error.
    pass
