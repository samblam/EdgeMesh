"""Tests for EdgeMesh Device Simulator"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch


def test_simulator_initialization():
    """Test DeviceSimulator can be initialized"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=5)

    assert sim.api_base == "http://localhost:8000"
    assert sim.num_devices == 5
    assert sim.devices == []
    assert sim.running is True


@pytest.mark.asyncio
async def test_initialize_devices():
    """Test device initialization creates correct number of devices"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=3)
    await sim.initialize_devices()

    assert len(sim.devices) == 3

    # Verify device structure
    for device in sim.devices:
        assert "device_id" in device
        assert "device_type" in device
        assert "os" in device
        assert "os_version" in device
        assert "user_email" in device
        assert "user_id" in device
        assert "enrolled" in device
        assert device["enrolled"] is False


@pytest.mark.asyncio
async def test_initialize_devices_creates_valid_types():
    """Test devices have valid types and OS"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=10)
    await sim.initialize_devices()

    valid_types = ["laptop", "server", "iot"]

    for device in sim.devices:
        assert device["device_type"] in valid_types
        assert len(device["os"]) > 0
        assert len(device["os_version"]) > 0


@pytest.mark.asyncio
async def test_enroll_all_devices_success():
    """Test enrolling all devices with API"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=2)
    await sim.initialize_devices()

    # Mock httpx.AsyncClient
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "device_id": "device-000",
        "certificate": "MOCK_CERT",
        "private_key": "MOCK_KEY",
        "ca_certificate": "MOCK_CA"
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        await sim.enroll_all_devices()

    # Verify all devices are enrolled
    for device in sim.devices:
        assert device["enrolled"] is True
        assert "device_cert" in device


@pytest.mark.asyncio
async def test_report_health():
    """Test health reporting for single device"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=1)
    await sim.initialize_devices()

    device = sim.devices[0]
    device["enrolled"] = True

    # Mock httpx.AsyncClient
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "healthy"}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        await sim.report_health(device)

    # Verify post was called with correct endpoint
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v1/health" in call_args[0][0]


@pytest.mark.asyncio
async def test_request_connection():
    """Test connection request for single device"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=1)
    await sim.initialize_devices()

    device = sim.devices[0]
    device["enrolled"] = True

    # Mock httpx.AsyncClient
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "connection_id": "conn-123",
        "status": "authorized"
    }

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post.return_value = mock_response

    with patch('httpx.AsyncClient', return_value=mock_client):
        await sim.request_connection(device)

    # Verify post was called with correct endpoint
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "/api/v1/connections/request" in call_args[0][0]


@pytest.mark.asyncio
async def test_health_metrics_are_realistic():
    """Test that generated health metrics are realistic"""
    from simulator import DeviceSimulator

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=1)
    await sim.initialize_devices()

    device = sim.devices[0]

    # Capture the health data sent
    captured_health = None

    async def capture_post(*args, **kwargs):
        nonlocal captured_health
        captured_health = kwargs.get('json')
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "healthy"}
        return mock_resp

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = capture_post

    with patch('httpx.AsyncClient', return_value=mock_client):
        await sim.report_health(device)

    # Verify metrics are realistic
    assert captured_health is not None
    assert "metrics" in captured_health
    metrics = captured_health["metrics"]
    assert 20 <= metrics["cpu_usage"] <= 85
    assert 30 <= metrics["memory_usage"] <= 80
    assert 40 <= metrics["disk_usage"] <= 75
    assert isinstance(metrics["os_patches_current"], bool)
    assert isinstance(metrics["antivirus_enabled"], bool)
    assert isinstance(metrics["disk_encrypted"], bool)


def test_signal_handler():
    """Test that signal handler stops the simulator"""
    from simulator import DeviceSimulator
    import signal

    sim = DeviceSimulator(api_base="http://localhost:8000", num_devices=1)

    assert sim.running is True
    sim._signal_handler(signal.SIGTERM, None)
    assert sim.running is False
