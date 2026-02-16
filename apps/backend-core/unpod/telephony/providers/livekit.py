from .base import BaseProvider
import requests
import time
import jwt
from rest_framework.response import Response
from rest_framework import status
from unpod.telephony.models import VoiceBridgeNumber


class LivekitProvider(BaseProvider):
    """Abstract base class for providers."""

    def __init__(self):
        self.token = None
        self.headers = None
        self._token_expiry = 0

    """Authenticate with the provider using credentials."""

    def auth(self, creds: dict) -> str:
        now = int(time.time())

        if time.time() < self._token_expiry:
            return self.token

        self._token_expiry = now + 3500
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")

        payload = {
            "iss": api_key,
            "exp": now + 3600,
            "iat": now,
            "video": {"ingressAdmin": True},
            "sip": {"call": True, "admin": True},
        }
        token = jwt.encode(payload, api_secret, algorithm="HS256")
        self.token = token if isinstance(token, str) else token.decode("utf-8")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        return self.token

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

    """Creates a LiveKit inbound SIP trunk credential and registers a phone number."""

    def set_inbound(self, config: dict) -> Response:
        """Set up inbound configuration for the provider."""
        required = ["api_key", "api_secret", "base_url", "name", "numbers"]

        validationError = self.validate_config(config, required)
        if validationError:
            return validationError

        self.auth(config)

        payload = {
            "trunk": {
                "name": config.get("name"),
                "numbers": config.get("numbers")
                if isinstance(config.get("numbers"), list)
                else [config.get("numbers")],
            }
        }

        try:
            base_url = config.get("base_url").replace("wss://", "")
            res = requests.post(
                f"https://{base_url}/twirp/livekit.SIP/CreateSIPInboundTrunk",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if res.status_code == 401:
                return Response(
                    {"message": res.text, "error_type": "UNAUTHORIZED"},
                    status=res.status_code,
                )

            result = res.json()
            if res.status_code != 200:
                print("Result from LiveKit:", result)
                error = result.get("code")
                message = result.get("msg")
                error_message = (
                    f"{error} - {message}"
                    if error and message
                    else "Failed to create inbound credential"
                )

                return Response(
                    {"success": False, "message": error_message, "error_type": error},
                    status=res.status_code,
                )

            sipRefer = result.get("sip_trunk_id")

            return Response(
                {"success": True, "sip_refer": sipRefer}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"success": False, "message": f"Exception Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    """Creates a LiveKit outbound SIP trunk credential and registers a phone number."""

    def set_outbound(self, config: dict) -> Response:
        required = ["api_key", "api_secret", "base_url", "address", "numbers", "name"]

        validationError = self.validate_config(config, required)
        if validationError:
            return validationError

        self.auth(config)

        trunk_payload = {
            "trunk": {
                "name": config.get("name", "My outbound trunk"),
                "address": config["address"],
                "numbers": config["numbers"],
                "auth_username": config.get("auth_username", "up-tt-user"),
                "auth_password": config.get("auth_password", "Pass-up-tt-user-word1"),
            }
        }

        try:
            base_url = config.get("base_url").replace("wss://", "")
            res = requests.post(
                f"https://{base_url}/twirp/livekit.SIP/CreateSIPOutboundTrunk",
                headers=self.headers,
                json=trunk_payload,
                timeout=30,
            )

            if res.status_code == 401:
                return Response(
                    {
                        "success": False,
                        "message": res.text,
                        "error_type": "UNAUTHORIZED",
                    },
                    status=res.status_code,
                )

            result = res.json()
            if res.status_code != 200:
                error = result.get("error")
                message = result.get("message")
                error_message = (
                    f"{error} - {message}"
                    if error and message
                    else "Failed to create outbound trunk"
                )

                return Response(
                    {"success": False, "message": error_message, "error_type": error},
                    status=res.status_code,
                )

            sipRefer = result.get("sip_trunk_id")

            return Response(
                {"success": True, "sip_refer": sipRefer}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    """Creates a LiveKit dispatch rule for SIP trunks."""

    def set_dispatch_rule(self, config):
        required = ["api_key", "api_secret", "base_url", "name", "sip_id"]

        validationError = self.validate_config(config, required)
        if validationError:
            return validationError

        self.auth(config)

        numbers = config.get("numbers")
        vbn = VoiceBridgeNumber.objects.filter(number__number__in=numbers)

        agent = [{"agent_name": str(num.agent_id)} for num in vbn]
        payload = {
            "rule": {"dispatchRuleIndividual": {"roomPrefix": config.get("name")}},
            "name": config.get("name"),
            "trunk_ids": [config.get("sip_id")],
        }
        if agent:
            payload["room_config"] = {"agents": agent}
        try:
            base_url = config.get("base_url").replace("wss://", "")
            res = requests.post(
                f"https://{base_url}/twirp/livekit.SIP/CreateSIPDispatchRule",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if res.status_code == 401:
                return Response(
                    {
                        "success": False,
                        "message": res.text,
                        "error_type": "UNAUTHORIZED",
                    },
                    status=res.status_code,
                )

            result = res.json()
            if res.status_code != 200:
                error = result.get("error")
                message = result.get("message")
                error_message = (
                    f"{error} - {message}"
                    if error and message
                    else "Failed to create dispatch Rule"
                )

                return Response(
                    {"success": False, "message": error_message, "error_type": error},
                    status=res.status_code,
                )

            print("set_dispatch_rule: Result from LiveKit:", result)

            return Response(
                {"success": True, "sip_refer": result.get("sip_dispatch_rule_id")},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    """Updates a LiveKit SIP trunk configuration."""

    def update_trunk(self, config) -> Response:
        direction = config.get("direction")
        required = ["api_key", "api_secret", "base_url", "name", "number", "sip_refer"]

        if direction == "outbound":
            required.extend(["address"])

        validationError = self.validate_config(config, required)
        if validationError:
            return validationError

        self.auth(config)

        payload = {
            "sip_trunk_id": config.get("sip_refer"),
            "replace": {
                "name": config.get("name"),
                "numbers": config.get("number"),
                "address": config.get("address", "sip-up-tt.unpod.tv"),
                "media_encryption": config.get("media_encryption"),
                "auth_username": config.get("username", "up-tt-user"),
                "auth_password": config.get("password", "Pass-up-tt-user-word1"),
            },
        }

        print("==================================")
        print("payload:", payload)
        print("==================================")

        base_url = config.get("base_url").replace("wss://", "")
        trunkType = (
            "UpdateSIPInboundTrunk"
            if direction == "inbound"
            else "UpdateSIPOutboundTrunk"
        )
        url = f"https://{base_url}/twirp/livekit.SIP/{trunkType}"

        try:
            res = requests.post(url, json=payload, headers=self.headers, timeout=30)

            if res.status_code == 401:
                return Response(
                    {"message": res.text, "error_type": "UNAUTHORIZED"},
                    status=res.status_code,
                )

            result = res.json()
            if res.status_code != 200:
                error = result.get("code")
                message = result.get("msg")
                error_message = (
                    f"{error} - {message}"
                    if error and message
                    else "Failed to update trunk"
                )

                return Response(
                    {"message": error_message, "error_type": error},
                    status=res.status_code,
                )

            sipRefer = result.get("sip_trunk_id")

            return Response({"sip_refer": sipRefer}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    """Deletes a LiveKit SIP trunk configuration."""

    def delete_trunk(self, config):
        required = ["api_key", "api_secret", "base_url", "sip_refer"]

        validationError = self.validate_config(config, required)
        if validationError:
            return validationError

        self.auth(config)

        print("Deleting trunk with config:", config, required)

        serviceType = config.get("service_type", "")
        payload = {"sip_trunk_id": config.get("sip_refer")}

        if serviceType == "rule":
            payload["sip_dispatch_rule_id"] = config.get("sip_refer")

        base_url = config.get("base_url").replace("wss://", "")
        trunkType = (
            "DeleteSIPDispatchRule" if serviceType == "rule" else "DeleteSIPTrunk"
        )
        url = f"https://{base_url}/twirp/livekit.SIP/{trunkType}"

        res = requests.post(url, json=payload, headers=self.headers, timeout=30)

        if res.status_code == 401:
            return Response(
                {"message": res.text, "error_type": "UNAUTHORIZED"},
                status=res.status_code,
            )

        result = res.json()
        print("Deleting trunk with res:", res, res.status_code, res.text)
        if res.status_code != 200:
            error = result.get("code")
            message = result.get("msg")
            error_message = (
                f"{error} - {message}"
                if error and message
                else "Failed to delete trunk"
            )

            print(f"Error deleting trunk: {error_message}")

            return Response(
                {"message": error_message, "error_type": error}, status=res.status_code
            )

        return Response(
            {"message": "Trunk delete successfully."}, status=status.HTTP_200_OK
        )
