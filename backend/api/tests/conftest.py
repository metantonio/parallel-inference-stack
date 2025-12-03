import pytest
import os
import sys

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock settings BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_settings():
    """Provide test settings."""
    from app.config import Settings
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL="redis://localhost:6379/15",
        JWT_SECRET_KEY="test-secret-key-for-testing-only",
        JWT_ALGORITHM="HS256",
        JWT_EXPIRATION_MINUTES=30,
    )

@pytest.fixture
def mock_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True,
    }

@pytest.fixture
def mock_inference_request():
    """Sample inference request data."""
    return {
        "data": {"text": "Hello, world!"},
        "priority": "normal",
        "timeout": 60,
    }
