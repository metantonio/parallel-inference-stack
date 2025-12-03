import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.config import Settings

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
    return Settings(
        DATABASE_URL=TEST_DATABASE_URL,
        REDIS_URL="redis://localhost:6379/15",  # Use different DB for tests
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
