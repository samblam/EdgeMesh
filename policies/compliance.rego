package edgemesh.compliance

import future.keywords.if

# Check if device meets compliance requirements
device_compliant(device) if {
    device.os_patches_current == true
    device.antivirus_enabled == true
    device.disk_encrypted == true
    supported_os_version(device.os, device.os_version)
}

# Supported OS versions (example)
supported_os_version(os, version) if {
    os == "Ubuntu"
    version in ["22.04", "24.04"]
}

supported_os_version(os, version) if {
    os == "macOS"
    version_parts := split(version, ".")
    major := to_number(version_parts[0])
    major >= 13  # Ventura or later
}

supported_os_version(os, version) if {
    os == "Windows"
    version in ["10", "11"]
}
