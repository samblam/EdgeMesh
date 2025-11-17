# EdgeMesh Device Simulator

A Python CLI tool that simulates multiple edge devices enrolling, reporting health metrics, and requesting connections to the EdgeMesh control plane.

## Features

- **Multi-device simulation**: Simulates multiple edge devices concurrently
- **Device enrollment**: Automatically enrolls devices with the control plane
- **Health reporting**: Continuously reports realistic health metrics
- **Connection requests**: Simulates random connection requests to services
- **Realistic load patterns**: Generates realistic traffic patterns for testing
- **Graceful shutdown**: Handles SIGINT/SIGTERM signals properly

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Run with defaults (20 devices against localhost:8000)
python simulator.py

# Custom API endpoint
python simulator.py --api http://192.168.1.100:8000

# Custom number of devices
python simulator.py --devices 50

# Both custom API and device count
python simulator.py --api https://control-plane.example.com --devices 100
```

### Command-line Arguments

- `--api`: Control plane API URL (default: `http://localhost:8000`)
- `--devices`: Number of devices to simulate (default: `20`)

## How It Works

The simulator performs the following workflow:

1. **Initialization**: Creates fake device configurations with random types (laptop/server/iot) and OS info
2. **Enrollment**: Enrolls all devices with the control plane API
3. **Health Reporting Loop**: Every 60 seconds, all enrolled devices report health metrics including:
   - CPU usage (20-85%)
   - Memory usage (30-80%)
   - Disk usage (40-75%)
   - OS patches status (85% compliant)
   - Antivirus status (90% compliant)
   - Disk encryption status (95% compliant)

4. **Connection Request Loop**: Every 5 seconds, 1-3 random devices request connections to random services:
   - database
   - api
   - storage
   - analytics

## Example Output

```
2025-11-17 19:15:00 - INFO - Initialized 20 devices
2025-11-17 19:15:00 - INFO - Enrolling devices...
2025-11-17 19:15:01 - INFO -   ✓ device-000 enrolled
2025-11-17 19:15:01 - INFO -   ✓ device-001 enrolled
...
2025-11-17 19:15:20 - INFO - Starting health reporting loop (every 60s)...
2025-11-17 19:15:20 - INFO - Starting connection simulation loop (every 5s)...
2025-11-17 19:15:21 - INFO - ✓ device-003 → api (authorized)
2025-11-17 19:15:21 - WARNING - ✗ device-007 → database (denied: 403)
...
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_simulator.py::test_simulator_initialization -v

# Run with coverage
python -m pytest tests/ --cov=simulator --cov-report=html
```

### Project Structure

```
simulator/
├── simulator.py          # Main simulator implementation
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── tests/
    └── test_simulator.py # Unit tests
```

## Testing Against Live API

To test against a running EdgeMesh control plane:

```bash
# Start the control plane (in another terminal)
cd ../control-plane
docker-compose up

# Run simulator
python simulator.py --api http://localhost:8000 --devices 10
```

Press `Ctrl+C` to stop the simulator gracefully.

## Requirements

- Python 3.11+
- httpx 0.28.1+
- faker 33.1.0+
- pytest 9.0.1+ (for testing)

## License

Part of the EdgeMesh Zero-Trust Access Control System.
