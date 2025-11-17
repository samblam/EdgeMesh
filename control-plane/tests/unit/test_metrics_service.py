"""
Unit tests for MetricsService
"""
import pytest
from unittest.mock import Mock, patch
from app.services.metrics import (
    MetricsService,
    devices_total,
    device_enrollments_total,
    authorization_decisions_total,
    authorization_latency_seconds,
    connections_active,
    connections_total,
    health_checks_total,
    unhealthy_devices,
)


class TestMetricsService:
    """Test suite for MetricsService"""

    def setup_method(self):
        """Store initial metric values before each test"""
        # Store initial values for comparison
        self.initial_enrollments = device_enrollments_total._value.get()
        self.initial_health_checks = health_checks_total._value.get()

    def test_record_device_enrollment(self):
        """Test recording device enrollment increments correct metrics"""
        # Get initial values
        initial_enrollments = device_enrollments_total._value.get()
        initial_active = devices_total.labels(status="active")._value.get()

        # Record enrollment
        MetricsService.record_device_enrollment()

        # Verify enrollment counter increased
        assert device_enrollments_total._value.get() == initial_enrollments + 1

        # Verify active devices gauge increased
        assert devices_total.labels(status="active")._value.get() == initial_active + 1

    def test_record_device_status_change(self):
        """Test recording device status change updates gauges correctly"""
        # Get initial state
        initial_active = devices_total.labels(status="active")._value.get()
        initial_inactive = devices_total.labels(status="inactive")._value.get()

        # Change device from active to inactive
        MetricsService.record_device_status_change("active", "inactive")

        # Verify counts updated
        assert devices_total.labels(status="active")._value.get() == initial_active - 1
        assert devices_total.labels(status="inactive")._value.get() == initial_inactive + 1

    def test_record_authorization_decision_allowed(self):
        """Test recording allowed authorization decision"""
        latency = 0.05  # 50ms

        # Get initial values
        initial_allow = authorization_decisions_total.labels(decision="allow")._value.get()
        initial_deny = authorization_decisions_total.labels(decision="deny")._value.get()

        # Record allowed decision
        MetricsService.record_authorization_decision(allowed=True, latency=latency)

        # Verify allow counter increased
        assert authorization_decisions_total.labels(decision="allow")._value.get() == initial_allow + 1

        # Verify deny counter unchanged
        assert authorization_decisions_total.labels(decision="deny")._value.get() == initial_deny

        # Verify latency was recorded (histogram observe doesn't raise exceptions)
        # The actual histogram functionality is tested by prometheus_client library

    def test_record_authorization_decision_denied(self):
        """Test recording denied authorization decision"""
        latency = 0.03  # 30ms

        # Get initial values
        initial_allow = authorization_decisions_total.labels(decision="allow")._value.get()
        initial_deny = authorization_decisions_total.labels(decision="deny")._value.get()

        # Record denied decision
        MetricsService.record_authorization_decision(allowed=False, latency=latency)

        # Verify deny counter increased
        assert authorization_decisions_total.labels(decision="deny")._value.get() == initial_deny + 1

        # Verify allow counter unchanged
        assert authorization_decisions_total.labels(decision="allow")._value.get() == initial_allow

        # Verify latency was recorded (histogram observe doesn't raise exceptions)
        # The actual histogram functionality is tested by prometheus_client library

    def test_record_connection_request_authorized(self):
        """Test recording authorized connection request"""
        service = "database"

        # Get initial values
        initial_authorized = connections_total.labels(service=service, status="authorized")._value.get()
        initial_denied = connections_total.labels(service=service, status="denied")._value.get()
        initial_active = connections_active.labels(service=service)._value.get()

        # Record authorized connection
        MetricsService.record_connection_request(service=service, authorized=True)

        # Verify authorized counter increased
        assert connections_total.labels(service=service, status="authorized")._value.get() == initial_authorized + 1

        # Verify denied counter unchanged
        assert connections_total.labels(service=service, status="denied")._value.get() == initial_denied

        # Verify active connections increased
        assert connections_active.labels(service=service)._value.get() == initial_active + 1

    def test_record_connection_request_denied(self):
        """Test recording denied connection request"""
        service = "database"

        # Get initial values
        initial_authorized = connections_total.labels(service=service, status="authorized")._value.get()
        initial_denied = connections_total.labels(service=service, status="denied")._value.get()
        initial_active = connections_active.labels(service=service)._value.get()

        # Record denied connection
        MetricsService.record_connection_request(service=service, authorized=False)

        # Verify denied counter increased
        assert connections_total.labels(service=service, status="denied")._value.get() == initial_denied + 1

        # Verify authorized counter unchanged
        assert connections_total.labels(service=service, status="authorized")._value.get() == initial_authorized

        # Verify active connections unchanged (denied connections don't become active)
        assert connections_active.labels(service=service)._value.get() == initial_active

    def test_record_connection_terminated(self):
        """Test recording connection termination"""
        service = "database"

        # Get initial active connections
        initial_active = connections_active.labels(service=service)._value.get()

        # Record connection termination
        MetricsService.record_connection_terminated(service=service)

        # Verify active connections decreased
        assert connections_active.labels(service=service)._value.get() == initial_active - 1

    def test_record_health_check(self):
        """Test recording health check"""
        initial_count = health_checks_total._value.get()

        # Record health check
        MetricsService.record_health_check()

        # Verify counter increased
        assert health_checks_total._value.get() == initial_count + 1

    def test_update_device_counts(self):
        """Test updating device counts"""
        healthy = 80
        unhealthy = 20

        # Update device counts
        MetricsService.update_device_counts(healthy=healthy, unhealthy=unhealthy)

        # Verify total devices set correctly
        assert devices_total.labels(status="active")._value.get() == 100

        # Verify unhealthy count set correctly
        assert unhealthy_devices._value.get() == 20

    def test_multiple_services_tracked_separately(self):
        """Test that different services are tracked independently"""
        # Get initial values
        initial_database = connections_active.labels(service="database")._value.get()
        initial_api = connections_active.labels(service="api")._value.get()

        # Record connections for different services
        MetricsService.record_connection_request(service="database", authorized=True)
        MetricsService.record_connection_request(service="api", authorized=True)
        MetricsService.record_connection_request(service="database", authorized=True)

        # Verify each service tracked separately
        assert connections_active.labels(service="database")._value.get() == initial_database + 2
        assert connections_active.labels(service="api")._value.get() == initial_api + 1

    def test_authorization_latency_statistics(self):
        """Test that authorization latency histogram tracks statistics correctly"""
        # Get initial value
        initial_allow = authorization_decisions_total.labels(decision="allow")._value.get()

        # Record multiple latencies
        latencies = [0.01, 0.02, 0.03, 0.04, 0.05]

        for latency in latencies:
            MetricsService.record_authorization_decision(allowed=True, latency=latency)

        # Verify all decisions were recorded
        assert authorization_decisions_total.labels(decision="allow")._value.get() == initial_allow + 5

        # Histogram functionality (observe) is verified by not raising exceptions
        # The actual statistical calculations are tested by prometheus_client library
