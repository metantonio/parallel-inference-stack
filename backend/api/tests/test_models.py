"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from app.models import User, InferenceRequest, TaskStatus

class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, test_db):
        """Test creating a user."""
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here",
            is_active=True,
        )
        test_db.add(user)
        test_db.commit()
        
        # Retrieve user
        retrieved_user = test_db.query(User).filter(User.username == "testuser").first()
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.is_active is True
    
    def test_user_unique_username(self, test_db):
        """Test that username must be unique."""
        user1 = User(
            id="user-1",
            username="testuser",
            email="test1@example.com",
            hashed_password="hash1",
        )
        user2 = User(
            id="user-2",
            username="testuser",  # Duplicate username
            email="test2@example.com",
            hashed_password="hash2",
        )
        
        test_db.add(user1)
        test_db.commit()
        
        test_db.add(user2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            test_db.commit()

class TestInferenceRequestModel:
    """Test InferenceRequest model."""
    
    def test_create_inference_request(self, test_db):
        """Test creating an inference request."""
        request = InferenceRequest(
            task_id="task-123",
            user_id="user-123",
            status=TaskStatus.QUEUED,
            priority="normal",
            input_data={"text": "Hello"},
            created_at=datetime.utcnow(),
        )
        test_db.add(request)
        test_db.commit()
        
        # Retrieve request
        retrieved = test_db.query(InferenceRequest).filter(
            InferenceRequest.task_id == "task-123"
        ).first()
        assert retrieved is not None
        assert retrieved.status == TaskStatus.QUEUED
        assert retrieved.priority == "normal"
        assert retrieved.input_data == {"text": "Hello"}
    
    def test_task_status_enum(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.QUEUED == "queued"
        assert TaskStatus.PROCESSING == "processing"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
