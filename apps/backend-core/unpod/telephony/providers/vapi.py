import requests
from rest_framework.response import Response
from rest_framework import status
from unpod.telephony.providers.base import BaseProvider


class VapiProvider(BaseProvider):
    """Abstract base class for providers."""

    def auth(self, creds: dict) -> str:
        """Authenticate with the provider using credentials."""
        pass

    @staticmethod
    def validate_config(config, keys):
        missing = [
            key for key in keys if key not in config or config.get(key) in [None, ""]
        ]
        if missing:
            return Response(
                {
                    "message": f"Missing required field(s): {', '.join(missing)}",
                    "error_type": "VALIDATION_ERROR",
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        return None

    def set_inbound(self, config: dict) -> Response:
        """
        Creates a Vapi inbound SIP trunk credential and registers a phone number.
        """
        required = ["api_key", "number"]
        validationError = self.validate_config(config, required)

        if validationError:
            return validationError

        headers = {
            "Authorization": f"Bearer {config.get('api_key')}",
            "Content-Type": "application/json",
        }

        # Step 1: Create inbound credential
        gateway_ip = config.get("gateway_ip", "sip-up-tt.unpod.tv")

        payload = {
            "provider": "byo-sip-trunk",
            "name": f"{config.get('name')} Inbound Trunk",
            "gateways": [{"ip": gateway_ip, "inboundEnabled": False}],
            "outboundLeadingPlusEnabled": True,
            "outboundAuthenticationPlan": {
                "authUsername": config.get("authUsername", "up-tt-user"),
                "authPassword": config.get("authPassword", "Pass-up-tt-user-word1"),
            },
        }

        res = requests.post(
            "https://api.vapi.ai/credential", headers=headers, json=payload, timeout=30
        )

        result = res.json()
        if res.status_code != 201:
            error = result.get("error")
            message = result.get("message")
            error_message = (
                f"{error} - {message}"
                if error and message
                else "Failed to create inbound credential"
            )

            return Response(
                {"success": False, "message": error_message, "error_type": error},
                status=res.status_code,
            )

        credentialId = result.get("id")

        # Step 2: Register the phone number to the credential
        phonePayload = {
            "provider": "byo-phone-number",
            # "name": "SIP Inbound Number",
            "name": config.get("name"),
            "number": config.get("number"),
            "numberE164CheckEnabled": False,
            "credentialId": credentialId,
        }

        print("Vapi Phone Payload:", phonePayload)
        print("==================================")

        phoneRes = requests.post(
            "https://api.vapi.ai/phone-number", headers=headers, json=phonePayload, timeout=30
        )

        result = phoneRes.json()
        if phoneRes.status_code != 201:
            error = result.get("error")
            message = result.get("message")
            error_message = (
                f"{error} - {message}"
                if error and message
                else "Failed to register phone number"
            )

            return Response(
                {"success": False, "message": error_message, "error_type": error},
                status=phoneRes.status_code,
            )

        return Response(
            {
                "success": True,
                "sip_refer": result.get("id"),
                "credentials_id": credentialId,
            },
            status=status.HTTP_200_OK,
        )

    def set_outbound(self, config: dict) -> Response:
        payload = {
            "provider": "byo-sip-trunk",
            "name": f"{config.get('provider')} Outbound Trunk",
            "gateways": [{"ip": config.get("gateway_ip")}],
            "outboundAuthenticationPlan": {
                "authUsername": config.get("authUsername"),
                "authPassword": config.get("authPassword"),
            },
        }

        headers = {
            "Authorization": f"Bearer {config.get('api_key')}",
            "Content-Type": "application/json",
        }

        res = requests.post(
            "https://api.vapi.ai/credential", headers=headers, json=payload, timeout=30
        )

        if res.status_code != 201:
            return Response(
                {"error": "Failed to create outbound trunk", "details": res.text},
                status=res.status_code,
            )

        return Response(
            {"success": True, "sip_refer": res.json().get("id")},
            status=status.HTTP_200_OK,
        )

    def update_trunk(self, config) -> Response:
        required = ["api_key", "number", "sip_refer"]
        validationError = self.validate_config(config, required)

        if validationError:
            return validationError

        headers = {
            "Authorization": f"Bearer {config.get('api_key')}",
            "Content-Type": "application/json",
        }

        payload = {
            "number": config.get("number")
            if "+" in config.get("number")
            else f"+91{config.get('number')}",
            "name": config.get("name"),
            "numberE164CheckEnabled": False,
        }

        res = requests.patch(
            f"https://api.vapi.ai/phone-number/{config.get('sip_refer')}",
            headers=headers,
            json=payload,
            timeout=30,
        )

        result = res.json()
        if res.status_code != 200:
            error = result.get("error")
            message = result.get("message")
            error_message = (
                f"{error} - {message}"
                if error and message
                else "Failed to update trunk"
            )

            return Response(
                {"message": error_message, "error_type": error}, status=res.status_code
            )

        return Response({"sip_refer": result.get("id")}, status=status.HTTP_200_OK)

    def delete_trunk(self, config):
        required = ["api_key", "sip_refer"]
        validationError = self.validate_config(config, required)

        if validationError:
            return validationError

        headers = {
            "Authorization": f"Bearer {config.get('api_key')}",
            "Content-Type": "application/json",
        }

        res = requests.delete(
            f"https://api.vapi.ai/phone-number/{config.get('sip_refer')}",
            headers=headers,
            timeout=30,
        )

        result = res.json()
        if res.status_code != 200:
            error = result.get("error")
            message = result.get("message")
            error_message = (
                f"{error} - {message}"
                if error and message
                else "Failed to delete trunk"
            )
            print(f"Error deleting trunk: {error_message}", str(result))

            return Response(
                {"message": error_message, "error_type": error}, status=res.status_code
            )

        return Response(
            {"message": "Trunk delete successfully."}, status=status.HTTP_200_OK
        )
