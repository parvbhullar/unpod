import logging

from rest_framework import status
from rest_framework.response import Response

from .constants import ENCRYPTION_TYPES
# from .models import BridgeProviderConfig
import time
import jwt

logger = logging.getLogger(__name__)
from .models import BridgeProviderConfig
from .providers.livekit import LivekitProvider
from .providers.vapi import VapiProvider
from ..common.datetime import get_datetime_now
from ..common.enum import TrunkType
from ..core_components.models import Pilot, Provider
from django.conf import settings
from django.utils.functional import SimpleLazyObject
import requests
from unpod.common.utils import get_global_configs
from .sbc_trunking.sbc import SBC
from rest_framework.exceptions import ValidationError
from django.db.models import Sum
from .models import VoiceBridgeNumber

sip_config = SimpleLazyObject(lambda: get_global_configs("unpod_sip_config"))

sbc = SimpleLazyObject(lambda: SBC())


def update_trunk_error(trunk, result):
    if result.status_code != 200:
        message = result.data.get("message")
        error_type = result.data.get("error_type")

        trunk.error_type = error_type
        trunk.error = message
        trunk.save()


def save_bridge_config(result, bridge, credential, payload, direction):
    if result.status_code == 200:
        # if result.status_code == status.HTTP_206_PARTIAL_CONTENT:
        #     raise serializers.ValidationError(result.data.get("message"))
        # raise ValueError(
        #     result.data.get(
        #         "message", f"trunk update failed for provider {credential.name}"
        #     )
        # )

        print(
            "save_bridge_config data:",
            direction,
            payload,
            payload.get("numbers"),
            payload.get("vbn_ids"),
        )
        print("==================================")
        print(payload)
        obj, created = BridgeProviderConfig.objects.update_or_create(
            bridge=bridge,
            provider_credential=credential,
            direction=direction,
            sip_refer=result.data.get("sip_refer"),
            defaults={
                "name": payload.get("name", ""),
                "numbers": payload.get("numbers"),
                "vbn_ids": payload.get("vbn_ids"),
                "address": payload.get("address", sip_config.get("up_sip_url")),
                "sip_credentials_id": result.data.get("credentials_id", ""),
                "username": sip_config.get("id"),
                "password": sip_config.get("secret"),
                "sip_refer": result.data.get("sip_refer"),
                "direction": direction,
                "service_type": "service" if direction != "" else "rule",
                "trunk_type": TrunkType.voice_infra.value,
                "config": {
                    "source": "auto-created on bridge",
                    "created_at": get_datetime_now(),
                    "updated": False,
                },
            },
        )

        print("BridgeProviderConfig created:", created, "obj:", obj)
        print("==================================")

        if not created:
            obj.config["source"] = "auto-created on bridge"
            obj.config["created_at"] = get_datetime_now()
            obj.config["updated"] = True
            obj.save()

        return obj, created

    return None, False


def create_livekit_trunks(bridge, credential, payload):
    numbers = payload.get("numbers")
    conf = {
        "name": payload.get("name"),
        "numbers": numbers,
        "api_key": credential.api_key,
        "api_secret": credential.api_secret,
        "base_url": credential.base_url or "",
        "address": sip_config.get("up_sip_url"),
        "auth_username": sip_config.get("id"),
        "auth_password": sip_config.get("secret"),
    }

    livekit = LivekitProvider()

    result = livekit.set_inbound(conf)
    save_bridge_config(result, bridge, credential, payload, "inbound")

    conf["sip_id"] = result.data.get("sip_refer")
    result = livekit.set_dispatch_rule(conf)
    save_bridge_config(result, bridge, credential, payload, "")

    result = livekit.set_outbound(conf)
    if result.get("success"):
        VoiceBridgeNumber.objects.filter(number__number__in=numbers).update(
            has_trunks=True
        )
    else:
        VoiceBridgeNumber.objects.filter(number__number__in=numbers).update(
            has_trunks=False
        )

    payload["address"] = conf.get("address", sip_config.get("up_sip_url", ""))
    save_bridge_config(result, bridge, credential, payload, "outbound")


def update_livekit_trunks(trunks, bridge, credential, payload):
    for trunk in trunks:
        payload["name"] = trunk.name or payload.get("name") or bridge.name
        print(f"---------direction----------{trunk.direction}----------------------")

        if trunk.direction != "":
            conf = {
                "name": payload.get("name"),
                "numbers": payload.get("numbers"),
                "api_key": credential.api_key,
                "api_secret": credential.api_secret,
                "base_url": credential.base_url or "",
                "sip_refer": trunk.sip_refer,
                "direction": trunk.direction,
                "address": trunk.address or sip_config.get("up_sip_url", ""),
            }
            result = update_trunk(trunk, conf)
            if result.status_code == 200:
                print("-----------------------------------------")
                print("update_livekit_trunks data:", trunk, conf, result.data)
                print("-----------------------------------------")
                payload["address"] = trunk.address or sip_config.get("up_sip_url")
                save_bridge_config(result, bridge, credential, payload, trunk.direction)

            else:
                update_trunk_error(trunk, result)
        else:
            result = Response(
                {"message": "", "sip_refer": trunk.sip_refer}, status=status.HTTP_200_OK
            )
            save_bridge_config(result, bridge, credential, payload, trunk.direction)


def update_trunk(trunk, data):
    credential = trunk.provider_credential
    numbers = list(data.get("numbers", []))
    result = None

    print("update_trunk data:", trunk, data)

    if credential.provider.name.lower() == "livekit":
        conf = {
            "api_key": credential.api_key,
            "api_secret": credential.api_secret,
            "base_url": credential.base_url or "",
            "sip_refer": trunk.sip_refer,
            "direction": trunk.direction,
            "name": data.get("name"),
            "number": numbers,
            "address": data.get("address", sip_config.get("up_sip_url")),
            "media_encryption": ENCRYPTION_TYPES.get(data.get("media_encryption"), 0),
            "username": data.get("username", sip_config.get("id")),
            "password": data.get("password", sip_config.get("secret")),
        }
        livekit = LivekitProvider()
        result = livekit.update_trunk(conf)
        res = sbc.create_configs(conf, trunk.bridge, trunk.provider_credential)
        VoiceBridgeNumber.objects.filter(number__number__in=numbers).update(
            sbc_config=res
        )

    if credential.provider.name.lower() == "vapi":
        conf = {
            "name": data.get("name"),
            "number": numbers[0],
            "api_key": credential.api_key,
            "api_secret": credential.api_secret,
            "base_url": credential.base_url or "",
            "sip_refer": trunk.sip_refer,
        }
        vapi = VapiProvider()
        result = vapi.update_trunk(conf)
        res = sbc.create_configs(conf, trunk.bridge, trunk.provider_credential)
        VoiceBridgeNumber.objects.filter(number__number__in=numbers[0]).update(
            sbc_config=res
        )

    if result is None:
        return Response(
            {"message": "Trunk update failed"}, status=status.HTTP_400_BAD_REQUEST
        )

    return result


def update_trunks_numbers(trunks, vbn):
    """
    Updates multiple trunks based on the provided list of trunks and removes the specified number from each trunk.
    """
    if trunks.exists():
        for trunk in trunks:
            remainingNumbers = [
                num for num in trunk.numbers if num != vbn.number.number
            ]
            print("remainingNumbers:", remainingNumbers)
            print("==================================")
            if not remainingNumbers:
                # If no numbers remain, we should delete the trunk
                result = delete_trunk(trunk)

                if result.status_code == 200:
                    trunk.delete()
                # elif result.status_code == status.HTTP_206_PARTIAL_CONTENT:
                #     raise serializers.ValidationError(result.data.get("message"))
                # else:
                #     raise ValueError(result.data.get("message"))
                else:
                    update_trunk_error(trunk, result)
            else:
                # If there are remaining numbers, update the trunk
                remainingIds = [num for num in trunk.vbn_ids if num != vbn.id]

                if trunk.direction == "":
                    config = trunk.config or {}
                    config["source"] = "auto-created on bridge"
                    config["updated"] = True
                    config["updated_at"] = get_datetime_now()

                    trunk.numbers = remainingNumbers
                    trunk.vbn_ids = remainingIds
                    trunk.config = config
                    trunk.save()

                else:
                    data = {
                        "name": trunk.name,
                        "numbers": remainingNumbers,
                        "address": trunk.address,
                        "media_encryption": trunk.media_encryption,
                        "username": trunk.username,
                        "password": trunk.password,
                    }

                    result = update_trunk(trunk, data)
                    if result.status_code == 200:
                        config = trunk.config or {}
                        config["source"] = "auto-created on bridge"
                        config["updated"] = True
                        config["updated_at"] = get_datetime_now()

                        trunk.numbers = remainingNumbers
                        trunk.vbn_ids = remainingIds
                        trunk.config = config
                        trunk.save()
                    # elif result.status_code == status.HTTP_206_PARTIAL_CONTENT:
                    #     raise serializers.ValidationError(result.data.get("message"))
                    # else:
                    #     raise ValueError(result.data.get("message"))
                    else:
                        update_trunk_error(trunk, result)


def delete_trunk(trunk):
    result = None
    credential = trunk.provider_credential

    for i in trunk.numbers:
        sbc.delete_configs(i, trunk.bridge, trunk.provider_credential)

    if credential.provider.name.lower() == "livekit":
        conf = {
            "api_key": credential.api_key,
            "api_secret": credential.api_secret,
            "base_url": credential.base_url or "",
            "sip_refer": trunk.sip_refer,
            "service_type": trunk.service_type,
        }

        livekit = LivekitProvider()
        result = livekit.delete_trunk(conf)

    elif credential.provider.name.lower() == "vapi":
        conf = {
            "api_key": credential.api_key,
            "sip_refer": trunk.sip_refer,
        }

        vapi = VapiProvider()
        result = vapi.delete_trunk(conf)

    if result is None:
        return Response(
            {"message": "Trunk update failed"}, status=status.HTTP_400_BAD_REQUEST
        )

    return result


def delete_trunks(trunks):
    """
    Deletes multiple trunks based on the provided list of trunks.
    """
    if trunks.exists():
        for trunk in trunks:
            result = delete_trunk(trunk)
            if result.status_code == 200:
                trunk.delete()
            # elif result.status_code == status.HTTP_206_PARTIAL_CONTENT:
            #     raise serializers.ValidationError(result.data.get("message"))
            # else:
            #     raise ValueError(result.data.get("message"))
            else:
                update_trunk_error(trunk, result)


def update_pilot_number(agent, instance):
    config = agent.telephony_config
    number = instance.number
    number = {
        "number": number.number,
        "country": number.country,
        "provider": number.provider.name,
    }

    if "telephony" not in config or not isinstance(config["telephony"], list):
        config["telephony"] = []

    handle = instance.agent_id if instance.agent_id else None

    if agent.handle == handle:
        if number not in config["telephony"]:
            config.get("telephony").append(number)

        agent.telephony_config = config
        agent.save()

    else:
        if instance.agent_id is not None:
            try:
                old = Pilot.objects.get(handle=instance.agent_id)
            except Pilot.DoesNotExist:
                old = None

            if old:
                old_config = old.telephony_config or {}
                telephony_list = old_config.setdefault("telephony", [])
                if number not in telephony_list:
                    telephony_list.append(number)
                old.telephony_config = old_config
                old.save()

        telephony_list = config.setdefault("telephony", [])
        if number not in telephony_list:
            telephony_list.append(number)
        agent.telephony_config = config
        agent.save()

        return Response(
            {"data": " ", "message": "Voice Bridge Number updated successfully."},
            status=status.HTTP_400_BAD_REQUEST,
        )


def create_number(data):
    response = requests.get(
        f"{settings.VAPI_URL}/phone-number",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + settings.VAPI_API_KEY,
        },
    )
    res = response.json()

    if response.status_code == 200:
        for num in res:
            if num.get("number") == data["number"]:
                data["association"] = {
                    "phone_number_id": num.get("id", ""),
                    "provider": num.get("providerResourceId", ""),
                    "orgId": num.get("orgId", ""),
                    "credentialId": num.get("credentialId", ""),
                }
                data["agent_number"] = True
    return data


def get_organization_channel_limit(organization):
    """
    Get the maximum allowed channels for an organization based on their subscription modules
    """
    try:
        from unpod.subscription.models import ActiveSubscription

        # Get the active subscription for the organization
        active_sub = ActiveSubscription.objects.filter(
            organization=organization, is_active=True
        ).first()

        if not active_sub or not hasattr(active_sub, "subscription"):
            return 1000  # Default safe value

        # Get the channels module from subscription
        channel_module = (
            active_sub.subscription.subscriptionmodules_subscription.filter(
                module__name="channels"
            ).first()
        )

        if channel_module:
            return int(channel_module.quantity)

        return 1000  # Default if no channel module found

    except Exception as e:
        logger.error(f"Error getting channel limit for org {organization.id}: {str(e)}")
        return 1000  # Safe default


def validate_channel_allocation(organization, requested_channels, current_usage=0):
    """
    Validate if the requested channels can be allocated within the organization's limit
    based on the number's channel count.

    Args:
        organization: The organization instance
        requested_channels: Number of channels being requested for the number
        current_usage: Current channel usage that will be replaced (for updates)

    Returns:
        None if valid, raises ValidationError if invalid
    """
    try:
        # Get organization's channel limit
        max_allowed = get_organization_channel_limit(organization)

        # Get current total usage across all numbers
        current_total = (
            VoiceBridgeNumber.objects.filter(bridge__hub=organization).aggregate(
                total=Sum("channels_count")
            )["total"]
            or 0
        )

        # Calculate a new total if this request is approved
        new_total = current_total - current_usage + requested_channels

        if new_total > max_allowed:
            raise ValidationError(
                f"Channel allocation would exceed organization limit. "
                f"Current usage: {current_total}, Requested: {requested_channels}, "
                f"After update: {new_total}, Allowed: {max_allowed}"
            )
    except Exception as e:
        logger.error(f"Error validating channel allocation: {str(e)}", exc_info=True)
        raise ValidationError("Error validating channel allocation") from e


def is_valid_credentials(data):
    provider = Provider.objects.filter(id=data.get("provider")).first()

    try:
        if provider.name.lower() == "livekit":
            api_key = data.get("api_key", "")
            api_secret = data.get("api_secret", "")
            now = int(time.time())
            payload = {
                "iss": api_key,
                "exp": now + 3600,
                "iat": now,
                "video": {"ingressAdmin": True},
                "sip": {"call": True, "admin": True},
            }
            token = jwt.encode(payload, api_secret, algorithm="HS256")
            token = token if isinstance(token, str) else token.decode("utf-8")
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            base_url = data.get("base_url", "").replace("wss://", "")
            res = requests.post(
                f"https://{base_url}/twirp/livekit.SIP/ListSIPInboundTrunk",
                headers=headers,
                json={},
            )

            if res.status_code == 200:
                return True
            else:
                return False

        elif provider.name.lower() == "vapi":
            res = requests.get(
                "https://api.vapi.ai/assistant",
                headers={"Authorization": f"Bearer {data.get('api_key')}"},
            )
            if res.status_code == 200:
                return True
            else:
                return False

        return False
    except Exception as e:
        return False


def get_livekit_trunks():
    url = f"https://{settings.LIVEKIT_BASE}/twirp/livekit.SIP/ListSIPInboundTrunk"

    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET
    now = int(time.time())
    _token_expiry = now + 3500

    payload = {
        "iss": api_key,
        "exp": now + 3600,
        "iat": now,
        "video": {"ingressAdmin": True},
        "sip": {"call": True, "admin": True},
    }
    token = jwt.encode(payload, api_secret, algorithm="HS256")
    token = token if isinstance(token, str) else token.decode("utf-8")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        data = requests.post(f"{url}", headers=headers, json={})
        res = data.json().get("items")
        return res
    except Exception as e:
        print("exception occured while fetching numbers", str(e))
        return []
