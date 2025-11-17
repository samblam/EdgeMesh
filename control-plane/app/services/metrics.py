"""
Metrics service for Prometheus monitoring
"""
from prometheus_client import Counter, Gauge, Histogram


# Device metrics
devices_total = Gauge(
    "edgemesh_devices_total",
    "Total number of devices",
    ["status"]
)

device_enrollments_total = Counter(
    "edgemesh_device_enrollments_total",
    "Total device enrollments"
)

# Authorization metrics
authorization_decisions_total = Counter(
    "edgemesh_authorization_decisions_total",
    "Total authorization decisions",
    ["decision"]  # allow, deny
)

authorization_latency_seconds = Histogram(
    "edgemesh_authorization_latency_seconds",
    "Authorization decision latency"
)

# Connection metrics
connections_active = Gauge(
    "edgemesh_connections_active",
    "Currently active connections",
    ["service"]
)

connections_total = Counter(
    "edgemesh_connections_total",
    "Total connection requests",
    ["service", "status"]  # authorized, denied
)

# Health check metrics
health_checks_total = Counter(
    "edgemesh_health_checks_total",
    "Total health checks received"
)

unhealthy_devices = Gauge(
    "edgemesh_unhealthy_devices",
    "Number of unhealthy devices"
)


class MetricsService:
    """Service for updating Prometheus metrics"""

    @staticmethod
    def record_device_enrollment():
        """Record a device enrollment"""
        device_enrollments_total.inc()
        devices_total.labels(status="active").inc()

    @staticmethod
    def record_device_status_change(old_status: str, new_status: str):
        """Record a device status change"""
        devices_total.labels(status=old_status).dec()
        devices_total.labels(status=new_status).inc()

    @staticmethod
    def record_authorization_decision(allowed: bool, latency: float):
        """Record an authorization decision and its latency"""
        decision = "allow" if allowed else "deny"
        authorization_decisions_total.labels(decision=decision).inc()
        authorization_latency_seconds.observe(latency)

    @staticmethod
    def record_connection_request(service: str, authorized: bool):
        """Record a connection request"""
        status = "authorized" if authorized else "denied"
        connections_total.labels(service=service, status=status).inc()

        if authorized:
            connections_active.labels(service=service).inc()

    @staticmethod
    def record_connection_terminated(service: str):
        """Record a connection termination"""
        connections_active.labels(service=service).dec()

    @staticmethod
    def record_health_check():
        """Record a health check"""
        health_checks_total.inc()

    @staticmethod
    def update_device_counts(healthy: int, unhealthy: int):
        """Update device health counts"""
        devices_total.labels(status="active").set(healthy + unhealthy)
        unhealthy_devices.set(unhealthy)
