"""Tests for OPA client service"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx


@pytest.mark.asyncio
async def test_opa_client_evaluate_policy_allow():
    """Test OPA client evaluates policy with allow decision"""
    from app.services.opa_client import OPAClient

    # Mock httpx.AsyncClient
    mock_response = AsyncMock()
    mock_response.json = lambda: {"result": True}
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.evaluate_policy({"device": {"authenticated": True}})

        assert result["allowed"] is True
        assert result["decision"] == "allow"


@pytest.mark.asyncio
async def test_opa_client_evaluate_policy_deny():
    """Test OPA client evaluates policy with deny decision"""
    from app.services.opa_client import OPAClient

    mock_response = AsyncMock()
    mock_response.json = lambda: {"result": False}
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.evaluate_policy({"device": {"authenticated": False}})

        assert result["allowed"] is False
        assert result["decision"] == "deny"


@pytest.mark.asyncio
async def test_opa_client_timeout_fails_closed():
    """Test OPA client fails closed on timeout"""
    from app.services.opa_client import OPAClient

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.evaluate_policy({"test": "data"})

        # Should fail closed for security
        assert result["allowed"] is False
        assert result["decision"] == "deny"
        assert "timeout" in result["error"].lower()


@pytest.mark.asyncio
async def test_opa_client_http_error_fails_closed():
    """Test OPA client fails closed on HTTP error"""
    from app.services.opa_client import OPAClient

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPError("Service unavailable")
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.evaluate_policy({"test": "data"})

        # Should fail closed for security
        assert result["allowed"] is False
        assert result["decision"] == "deny"
        assert "error" in result


@pytest.mark.asyncio
async def test_opa_client_check_device_compliance_true():
    """Test OPA client checks device compliance - compliant"""
    from app.services.opa_client import OPAClient

    mock_response = AsyncMock()
    mock_response.json = lambda: {"result": True}
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.check_device_compliance({
            "os_patches_current": True,
            "antivirus_enabled": True,
            "disk_encrypted": True
        })

        assert result is True


@pytest.mark.asyncio
async def test_opa_client_check_device_compliance_false():
    """Test OPA client checks device compliance - non-compliant"""
    from app.services.opa_client import OPAClient

    mock_response = AsyncMock()
    mock_response.json = lambda: {"result": False}
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.check_device_compliance({
            "os_patches_current": False  # Not compliant
        })

        assert result is False


@pytest.mark.asyncio
async def test_opa_client_compliance_error_returns_false():
    """Test OPA client returns False on compliance check error"""
    from app.services.opa_client import OPAClient

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = AsyncMock()
        mock_client.post.side_effect = httpx.HTTPError("Error")
        mock_client_class.return_value = mock_client

        client = OPAClient()
        result = await client.check_device_compliance({"test": "data"})

        # Should return False on error (fail safe)
        assert result is False
