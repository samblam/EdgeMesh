"""Tests for configuration management"""
import pytest
import os


def test_settings_module_exists():
    """Test that settings module can be imported"""
    from app.config import settings
    assert settings is not None


def test_settings_has_required_fields():
    """Test settings object has all required configuration fields"""
    from app.config import settings

    # Database settings
    assert hasattr(settings, 'DATABASE_URL')
    assert hasattr(settings, 'DATABASE_POOL_SIZE')
    assert hasattr(settings, 'DATABASE_MAX_OVERFLOW')

    # OPA settings
    assert hasattr(settings, 'OPA_URL')
    assert hasattr(settings, 'OPA_TIMEOUT')

    # Security settings
    assert hasattr(settings, 'ENROLLMENT_TOKEN_SECRET')
    assert hasattr(settings, 'CERT_VALIDITY_DAYS')
    assert hasattr(settings, 'CA_CERT_VALIDITY_DAYS')

    # Rate limiting
    assert hasattr(settings, 'RATE_LIMIT_ENROLLMENTS')
    assert hasattr(settings, 'RATE_LIMIT_CONNECTIONS')
    assert hasattr(settings, 'RATE_LIMIT_HEALTH')

    # Health check
    assert hasattr(settings, 'HEALTH_CHECK_MAX_AGE_MINUTES')


def test_settings_defaults():
    """Test settings have sensible defaults"""
    from app.config import settings

    assert settings.CERT_VALIDITY_DAYS == 90
    assert settings.CA_CERT_VALIDITY_DAYS == 3650
    assert settings.OPA_TIMEOUT == 5
    assert settings.HEALTH_CHECK_MAX_AGE_MINUTES == 5
    assert settings.DATABASE_POOL_SIZE == 20
    assert settings.DATABASE_MAX_OVERFLOW == 10


def test_settings_database_url_default():
    """Test database URL has a default for development"""
    from app.config import settings

    # Should have a default (sqlite for testing)
    assert settings.DATABASE_URL is not None
    assert len(settings.DATABASE_URL) > 0
