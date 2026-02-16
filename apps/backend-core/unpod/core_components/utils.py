import time

import jwt

from unpod.common.enum import RoleCodes, SpaceType
from unpod.common.storage_backends import imagekitBackend
from unpod.core_components.models import PilotLink, Provider
from django.conf import settings
import requests
import copy
from django.http import QueryDict
from .unpod_assistant.vapi_test import VapiAssistant
from unpod.core_components.models import Model, VoiceProfiles
import json


def remove_from_redis(key):
    from redis import StrictRedis

    try:
        REDIS: StrictRedis = StrictRedis.from_url(
            settings.CACHES["default"]["LOCATION"]
        )
        config = REDIS.get(key)
        if config:
            REDIS.delete(key)
            REDIS.close()
    except Exception as e:
        pass


def get_user_data(user_obj, fields=("id", "email", "full_name", "user_token")):
    user_data = {field: getattr(user_obj, field, "") or "" for field in fields}
    if "profile_color" in fields:
        if hasattr(user_obj, "userbasicdetail_user"):
            user_data["profile_color"] = user_obj.userbasicdetail_user.profile_color
        else:
            user_data.pop("profile_color", None)
    if "profile_picture" in fields:
        if hasattr(user_obj, "userbasicdetail_user"):
            if user_obj.userbasicdetail_user.profile_picture:
                user_data["profile_picture"] = imagekitBackend.generateURL(
                    user_obj.userbasicdetail_user.profile_picture.name
                )
        if user_data["profile_picture"] == "":
            user_data.pop("profile_picture", None)
    return user_data


def get_user_pilot_permission(pilot, user):
    if user.id == pilot.created_by:
        return RoleCodes.owner.name

    pilot_link = PilotLink.objects.filter(pilot=pilot, content_object=user).first()
    if not pilot_link:
        return None

    return pilot_link.role_code


def push_agent_vespa(data):
    url = f"{settings.API_SERVICE_URL}/store/agents/"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        return {"data": response.json()}
    except requests.exceptions.Timeout:
        return {"error": "Request timeout while pushing agent to Vespa"}
    except Exception as ex:
        return {"error": str(ex)}


def get_kb_list(obj):
    from unpod.space.models import Space

    kn_list = list(
        Space.objects.filter(
            pilots__pilot__id=obj.id, space_type=SpaceType.knowledge_base.name
        ).values("name", "slug", "token", "description")
    )
    for kb in kn_list:
        kb["datasource"] = kb.pop("description", "")
    return kn_list


def prepare_agent_data(pilot):
    agent_data = {
        "handle": pilot.handle,
        "persona_name": pilot.name,
        "about": pilot.description,
        "persona": pilot.ai_persona,
        "questions": pilot.questions,
        "llm_model": pilot.llm_model.slug if pilot.llm_model else None,
    }
    agent_data["organization_id"] = pilot.owner.id if pilot.owner else None
    agent_data["privacy_type"] = pilot.privacy_type
    tags = pilot.tags.values_list("name", flat=True)
    agent_data["tags"] = list(tags)
    agent_data["knowledge_bases"] = get_kb_list(pilot)
    return agent_data


def prepare_push_agent(pilot):
    agent_data = prepare_agent_data(pilot)
    return push_agent_vespa(agent_data)


def check_for_vapi(data, llm_slug=None, pilot=None):
    if hasattr(data, "dict"):
        data = data.dict()
    data = dict(data)
    data = copy.deepcopy(data)
    telephony = data.get("telephony_config")

    if not telephony and pilot is not None:
        telephony = pilot.telephony_config

    if data.get("chat_model"):
        chat_model_data = json.loads(data.get("chat_model"))
        # Try 'codename' first (new format), fallback to 'slug' (old format)
        model = chat_model_data.get("codename") or chat_model_data.get("slug")
    try:
        if not llm_slug:
            llm = Model.objects.filter(codename=model).first()
        else:
            llm = llm_slug
    except Exception:
        return {
            "error": "Invalid llm model please choose valid model",
            "success": False,
            "data": data,
        }

    # Add null check for llm
    if not llm:
        return {
            "error": f"LLM model '{model}' not found in database",
            "success": False,
            "data": data,
        }

    if isinstance(telephony, str):
        telephony = json.loads(telephony)
        data["telephony_config"] = telephony

    stt = Provider.objects.filter(id=telephony["transcriber"]["provider"]).first()
    tts = Provider.objects.filter(id=telephony["voice"]["provider"]).first()

    # Get tts_language from voice profile
    tts_language = "en"  # default
    voice_profile_id = telephony.get("voice_profile_id")
    if voice_profile_id:
        voice_profile = VoiceProfiles.objects.filter(pk=voice_profile_id).first()
        if voice_profile:
            lang_codes = list(voice_profile.tts_language.values_list("code", flat=True))
            if "en" in lang_codes and "hi" in lang_codes:
                tts_language = "en_hi"  # Multilingual
            elif "hi" in lang_codes:
                tts_language = "hi"  # Hindi only
            elif "en" in lang_codes:
                tts_language = "en"  # English only
            elif lang_codes:
                tts_language = lang_codes[0]  # First available language

    config_data = {
        "name": pilot.name or "default",
        "assistant_id": (pilot.config or {}).get("voice", {}).get("vapi_agent_id")
        or "",
        "llm_provider": llm.provider.name.lower() if llm and llm.provider else "openai",
        "llm_model": llm.name.lower() if llm else "gpt-4o-mini",
        "stt_provider": stt.name.lower() if stt else "openai",
        "stt_model": telephony["transcriber"]["model"].lower(),
        "stt_language": telephony["transcriber"]["language"].lower(),
        "tts_provider": tts.name.lower() if tts else "openai",
        "tts_model": telephony["voice"]["model"].lower(),
        "tts_voice": telephony["voice"]["voice"],
        "tts_language": tts_language,
        "first_message": data.get(
            "greeting_message", pilot.greeting_message if pilot else None
        ),
        "system_prompt": data.get(
            "system_prompt",
            pilot.system_prompt.encode().decode("unicode-escape") if pilot else None,
        ),
        "temperature": float(
            data.get("temperature", pilot.temperature if pilot else None)
        ),
        "number_of_words": int(data.get("number_of_words", 4)),
        "voice_seconds": float(data.get("voice_seconds", 0.2)),
        "back_off_seconds": int(data.get("back_off_seconds", 1)),
    }

    assistant = VapiAssistant()
    val = assistant.create_vapi_assistant(config_data)

    if not pilot:
        config = data.get("config", {})
        if isinstance(config, str):
            config = json.loads(config)
        else:
            config = dict(config)

        config.setdefault("voice", {})
        config["voice"]["vapi_agent_id"] = val
        data["config"] = config

    elif pilot:
        config = pilot.config
        config.setdefault("voice", {})
        config["voice"]["vapi_agent_id"] = val
        data["config"] = config

    numbers = telephony.get("telephony", [])

    for number in numbers:
        association = number.get("association", {})
        if association:
            number_id = association.get("phone_number_id", None)
            cred = number.get("association", {}).get("credentialId", None)
            if number_id:
                conf = data.get("config", {})
                conf["number_id"] = number_id
                data["config"] = conf

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.VAPI_API_KEY}",
                }
                payload = {"assistantId": val, "credentialId": cred}
                requests.patch(
                    f"{settings.VAPI_URL}/phone-number/{number_id}",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

    qd = QueryDict("", mutable=True)
    for key, value in data.items():
        qd[key] = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

    return {
        "message": "vapi created successfully",
        "success": True,
        "data": qd,
    }


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
