"""OPA (Open Policy Agent) Client Service"""
import httpx
from typing import Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class OPAClient:
    """
    Client for Open Policy Agent

    Handles policy evaluation requests to OPA server.
    Implements fail-closed semantics: on any error, deny access.
    """

    def __init__(self):
        self.opa_url = settings.OPA_URL
        self.policy_path = "edgemesh/authz/allow"

    async def evaluate_policy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate authorization policy with given input

        Args:
            input_data: Context for policy evaluation (device, user, service, etc.)

        Returns:
            Policy decision with allowed flag and decision string

        Example:
            >>> result = await client.evaluate_policy({
            ...     "device": {"authenticated": True, "status": "active"},
            ...     "user": {"role": "developer"},
            ...     "service": "database"
            ... })
            >>> result["allowed"]  # True or False
            >>> result["decision"]  # "allow" or "deny"
        """

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.opa_url}/v1/data/{self.policy_path}",
                    json={"input": input_data},
                    timeout=settings.OPA_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()

                allowed = result.get("result", False)

                return {
                    "allowed": allowed,
                    "decision": "allow" if allowed else "deny"
                }

            except httpx.TimeoutException as e:
                logger.error(f"OPA timeout: {e}")
                # Fail closed for security
                return {
                    "allowed": False,
                    "decision": "deny",
                    "error": "Policy service timeout - access denied for safety"
                }
            except httpx.HTTPError as e:
                logger.error(f"OPA HTTP error: {e}")
                # Fail closed for security
                return {
                    "allowed": False,
                    "decision": "deny",
                    "error": f"Policy service unavailable: {str(e)}"
                }
            except Exception as e:
                logger.error(f"OPA unexpected error: {e}", exc_info=True)
                return {
                    "allowed": False,
                    "decision": "deny",
                    "error": "Policy evaluation failed"
                }

    async def check_device_compliance(self, device_data: Dict[str, Any]) -> bool:
        """
        Check if device meets compliance requirements

        Args:
            device_data: Device information for compliance check

        Returns:
            True if device is compliant, False otherwise

        Example:
            >>> compliant = await client.check_device_compliance({
            ...     "os_patches_current": True,
            ...     "antivirus_enabled": True,
            ...     "disk_encrypted": True,
            ...     "os": "Ubuntu",
            ...     "os_version": "22.04"
            ... })
        """

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.opa_url}/v1/data/edgemesh/compliance/device_compliant",
                    json={"input": device_data},
                    timeout=5.0
                )
                response.raise_for_status()
                result = response.json()

                return result.get("result", False)

            except httpx.HTTPError:
                # Fail safe - return False on error
                return False
