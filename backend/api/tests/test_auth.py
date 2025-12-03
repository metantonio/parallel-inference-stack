"""
Unit tests for authentication module.
"""
import pytest
from datetime import timedelta
from jose import jwt
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)
from app.models import User

class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_hash_password(self):
        """Test that password hashing works."""
        password = "my_secure_password"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "my_secure_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "my_secure_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_contains_correct_data(self):
        """Test that token contains the correct data."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_token_with_custom_expiration(self):
        """Test creating token with custom expiration."""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data, expires_delta=expires_delta)
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
    
    def test_expired_token_fails_validation(self):
        """Test that expired token fails validation."""
        data = {"sub": "testuser"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta=expires_delta)
        
        # Should raise exception when decoding expired token
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

class TestUserAuthentication:
    """Test user authentication flow."""
    
    def test_get_user(self, test_db):
        """Test retrieving user from database."""
        from app.auth import get_user
        
        # Create test user
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        test_db.add(user)
        test_db.commit()
        
        # Retrieve user
        retrieved = get_user(test_db, "testuser")
        assert retrieved is not None
        assert retrieved.username == "testuser"
    
    def test_get_nonexistent_user(self, test_db):
        """Test retrieving non-existent user returns None."""
        from app.auth import get_user
        
        retrieved = get_user(test_db, "nonexistent")
        assert retrieved is None
