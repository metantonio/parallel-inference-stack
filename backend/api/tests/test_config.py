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

    def test_cors_origins_list_with_wildcard(self):
        """Should return ['*'] when CORS_ORIGINS='*'."""
        settings = Settings(CORS_ORIGINS="*")
        assert settings.cors_origins_list == ["*"]


    def test_cors_origins_list_multiple(self):
        """Should split comma-separated origins."""
        settings = Settings(CORS_ORIGINS="http://localhost:3000, http://127.0.0.1:3000")
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]


    def test_cors_origins_list_single(self):
        """Should return list with one origin."""
        settings = Settings(CORS_ORIGINS="http://localhost:3000")
        assert settings.cors_origins_list == ["http://localhost:3000"]