#!/usr/bin/env python3
"""EdgeMesh Device Simulator

Simulates multiple edge devices enrolling, reporting health, and requesting connections.
"""
import asyncio
import httpx
import random
import signal
from faker import Faker
from typing import List, Dict
from datetime import datetime
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

fake = Faker()


class DeviceSimulator:
    """Simulate multiple EdgeMesh devices"""

    def __init__(self, api_base: str, num_devices: int = 20, verify_ssl: bool = False):
        self.api_base = api_base
        self.devices: List[Dict] = []
        self.num_devices = num_devices
        self.running = True
        self.verify_ssl = verify_ssl
        self._client: httpx.AsyncClient = None

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("\n\nReceived shutdown signal, stopping gracefully...")
        self.running = False

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create reusable HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(verify=self.verify_ssl)
        return self._client

    async def _close_client(self):
        """Close HTTP client if it exists"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def initialize_devices(self):
        """Create fake device configurations"""

        device_types = ["laptop", "server", "iot"]
        os_options = {
            "laptop": [("Ubuntu", "22.04"), ("macOS", "14.1"), ("Windows", "11")],
            "server": [("Ubuntu", "22.04"), ("Ubuntu", "24.04")],
            "iot": [("Ubuntu", "22.04")]
        }

        for i in range(self.num_devices):
            device_type = random.choice(device_types)
            os, os_version = random.choice(os_options[device_type])

            device = {
                "device_id": f"device-{i:03d}",
                "device_type": device_type,
                "os": os,
                "os_version": os_version,
                "user_email": fake.email(),
                "user_id": f"user-{i:03d}",
                "enrolled": False
            }

            self.devices.append(device)

        logger.info(f"Initialized {self.num_devices} devices")

    async def enroll_all_devices(self):
        """Enroll all devices with control plane"""

        logger.info("Enrolling devices...")

        client = await self._get_client()
        for device in self.devices:
            try:
                response = await client.post(
                    f"{self.api_base}/api/v1/enroll",
                    json={
                        "device_id": device["device_id"],
                        "device_type": device["device_type"],
                        "enrollment_token": "demo-secret-token-change-in-production",
                        "os": device["os"],
                        "os_version": device["os_version"]
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    result = response.json()
                    device["enrolled"] = True
                    device["device_cert"] = result["certificate"]
                    logger.info(f"  ✓ {device['device_id']} enrolled")
                else:
                    logger.warning(f"  ✗ {device['device_id']} failed: {response.status_code}")

            except Exception as e:
                logger.error(f"  ✗ {device['device_id']} error: {e}")

    async def report_health(self, device: Dict):
        """Report health for single device"""

        # Generate realistic health metrics
        health = {
            "device_id": device["device_id"],
            "status": "healthy",
            "metrics": {
                "cpu_usage": random.uniform(20, 85),
                "memory_usage": random.uniform(30, 80),
                "disk_usage": random.uniform(40, 75),
                "os_patches_current": random.random() > 0.15,  # 85% compliant
                "antivirus_enabled": random.random() > 0.10,   # 90% compliant
                "disk_encrypted": random.random() > 0.05,      # 95% compliant
            }
        }

        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.api_base}/api/v1/health",
                json=health,
                timeout=5.0
            )

            if response.status_code == 200:
                result = response.json()
                status_icon = "✓" if result.get("status") == "healthy" else "✗"
                logger.debug(f"{status_icon} {device['device_id']}: {result.get('status')}")

        except Exception as e:
            logger.error(f"✗ {device['device_id']} health report failed: {e}")

    async def health_reporting_loop(self):
        """Continuously report health for all devices"""

        logger.info("Starting health reporting loop (every 60s)...")

        while self.running:
            try:
                if enrolled_devices := [d for d in self.devices if d["enrolled"]]:
                    await asyncio.gather(
                        *[self.report_health(device) for device in enrolled_devices]
                    )

                # Use smaller sleep chunks to check self.running more frequently
                for _ in range(12):  # 12 * 5 = 60 seconds
                    if not self.running:
                        break
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Health reporting error: {e}")
                if not self.running:
                    break

        logger.info("Health reporting loop stopped")

    async def request_connection(self, device: Dict):
        """Request connection to random service"""

        services = ["database", "api", "storage", "analytics"]
        service = random.choice(services)

        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.api_base}/api/v1/connections/request",
                json={
                    "device_id": device["device_id"],
                    "user_id": device["user_id"],
                    "service_name": service
                },
                timeout=5.0
            )

            if response.status_code == 200:
                logger.info(f"✓ {device['device_id']} → {service} (authorized)")
            else:
                logger.warning(f"✗ {device['device_id']} → {service} (denied: {response.status_code})")

        except Exception as e:
            logger.error(f"✗ {device['device_id']} connection error: {e}")

    async def connection_simulation_loop(self):
        """Continuously request random connections"""

        logger.info("Starting connection simulation loop (every 5s)...")

        while self.running:
            try:
                # Pick 1-3 random devices to request connections
                if enrolled_devices := [d for d in self.devices if d["enrolled"]]:
                    requesting_devices = random.sample(
                        enrolled_devices,
                        k=min(3, len(enrolled_devices))
                    )

                    await asyncio.gather(
                        *[self.request_connection(device) for device in requesting_devices]
                    )

                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Connection simulation error: {e}")
                if not self.running:
                    break

        logger.info("Connection simulation loop stopped")

    async def run(self):
        """Run full simulation"""

        # Setup signal handlers
        self._setup_signal_handlers()

        try:
            await self.initialize_devices()
            await self.enroll_all_devices()

            # Run health reporting and connection simulation concurrently
            await asyncio.gather(
                self.health_reporting_loop(),
                self.connection_simulation_loop()
            )
        finally:
            # Cleanup HTTP client
            await self._close_client()
            logger.info("Simulator stopped")


async def main():
    parser = argparse.ArgumentParser(description="EdgeMesh Device Simulator")
    parser.add_argument("--api", default="http://localhost:8000", help="Control plane API URL")
    parser.add_argument("--devices", type=int, default=20, help="Number of devices to simulate")
    parser.add_argument("--verify-ssl", action="store_true", help="Enable SSL certificate verification")

    args = parser.parse_args()

    simulator = DeviceSimulator(args.api, args.devices, args.verify_ssl)
    await simulator.run()


if __name__ == "__main__":
    asyncio.run(main())
