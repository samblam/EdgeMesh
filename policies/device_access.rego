package edgemesh.authz

import future.keywords.if
import future.keywords.in

# Default deny
default allow := false

# Main authorization logic
allow if {
    input.device.authenticated
    device_is_healthy(input.device)
    service_access_allowed(input.user, input.service)
    time_restrictions_met(input.user, input.time)
}

# Device health evaluation
device_is_healthy(device) if {
    device.status == "active"
    device.os_patches_current == true
    device.antivirus_enabled == true
    device.disk_encrypted == true
    device.cpu_usage < 90
    device.memory_usage < 90
}

# Service access control based on roles
service_access_allowed(user, service) if {
    role := user.role
    service_permissions[service][role] == true
}

# Service to role mapping
service_permissions := {
    "database": {
        "admin": true,
        "developer": true,
        "analyst": false
    },
    "api": {
        "admin": true,
        "developer": true,
        "analyst": true
    },
    "storage": {
        "admin": true,
        "developer": true,
        "analyst": true
    },
    "analytics": {
        "admin": true,
        "developer": false,
        "analyst": true
    }
}

# Time-based access restrictions
time_restrictions_met(user, time) if {
    user.role == "admin"  # Admins always allowed
}

time_restrictions_met(user, time) if {
    user.role != "admin"
    is_business_hours(time)
}

is_business_hours(time) if {
    time.hour >= 9
    time.hour < 17
    time.day_of_week >= 1  # Monday
    time.day_of_week <= 5  # Friday
}
