"""
Unit tests for configuration module.
"""
import pytest
from app.config import Settings

class TestSettings:
    """Test Settings configuration."""
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        assert settings.APP_NAME == "AI Inference API"
        assert settings.LOG_LEVEL == "info"
        assert settings.JWT_ALGORITHM == "HS256"
    
    def test_custom_settings(self):
        """Test that custom settings override defaults."""
        settings = Settings(
            APP_NAME="Custom API",
            LOG_LEVEL="debug",
            JWT_SECRET_KEY="custom-secret",
        )
        assert settings.APP_NAME == "Custom API"
        assert settings.LOG_LEVEL == "debug"
        assert settings.JWT_SECRET_KEY == "custom-secret"
    
    def test_jwt_expiration_is_integer(self):
        """Test that JWT expiration is an integer."""
        settings = Settings()
        assert isinstance(settings.JWT_EXPIRATION_MINUTES, int)
        assert settings.JWT_EXPIRATION_MINUTES > 0
