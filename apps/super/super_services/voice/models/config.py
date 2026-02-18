import ast
import codecs
import json
import os
from typing import Any, Dict, Optional

from super.core.callback.base import BaseCallback
from super.core.configuration.base_config import BaseModelConfig
from super.core.context.schema import Event, Message
from super_services.db.services.repository.conversation_block import (
    _extract_user_from_message,
    save_message_block,
)
from super_services.libs.core.block_processor import send_block_to_channel
from super_services.libs.core.db import executeQuery
from super_services.libs.core.redis import REDIS
from super_services.libs.logger import logger

_CONFIG_CACHE_TTL = 86400
_CONFIG_CACHE_PREFIX = "model_config:"
_USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"


def _get_cached_config(key: str) -> Optional[Dict[str, Any]]:
    """Get config from Redis cache."""
    if not _USE_REDIS:
        return None
    try:
        cache_key = f"{_CONFIG_CACHE_PREFIX}{key}"
        data = REDIS.get(cache_key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def _set_cached_config(key: str, config: Dict[str, Any]) -> None:
    if not _USE_REDIS:
        return
    try:
        cache_key = f"{_CONFIG_CACHE_PREFIX}{key}"
        REDIS.setex(cache_key, _CONFIG_CACHE_TTL, json.dumps(config))
    except Exception:
        pass


class ModelConfig(BaseModelConfig):
    def get_config(self, agent_id, **kwargs):
        try:
            config = _get_cached_config(agent_id)
            #
            if config:
                print(
                    f"\n\n found cached config for : {_CONFIG_CACHE_PREFIX}{agent_id} \n\n"
                )
                return config

            # Use a single parameterized query with JOINs to get all the data in one call
            query = f"""
            SELECT
                cp.id AS pilot_id,
                cp.space_id,
                cp.handle,
                cp.llm_model_id,
                cp.telephony_config::text AS telephony_config,
                cp.greeting_message,
                cp.system_prompt,
                cp.ai_persona,
                cp.followup_prompt as followup_prompt,
                cp.handover_prompt as handover_prompt,
                cp.back_off_seconds AS backoff_seconds,
                cp.voice_seconds AS voice_seconds,
                cp.enable_callback AS callback_enabled,
                cp.enable_followup AS follow_up_enabled,
                cp.enable_handover AS handover_enabled,
                cp.number_of_words AS number_of_words,
                cp.calling_days::text AS calling_days,
                cp.calling_time_ranges::text AS calling_time_ranges,
                cp.enable_memory As enable_memory,
                cp.voice_temperature as voice_temperature,
                cp.voice_speed as voice_speed,
                cp.voice_prompt as voice_prompt,
                prov.name AS llm_provider,
                cp.handover_number AS handover_number,
                cp.instant_handover AS instant_handover,
                llm.codename AS llm_model,
                llm.config::text AS llm_config,
                llm.inference as llm_inference,
                cp.notify_via_sms as sms_enabled,
                llm.realtime_sts as llm_realtime,
                ss.name AS space_name,
                ss.id AS space_id,
                ss.token AS space_token,
                ss.space_type AS space_type,
                MAX(CASE WHEN f.slug = 'structured-data' THEN df.values::text END)::json AS structured_data,
                MAX(CASE WHEN f.slug = 'success-evaluation' THEN df.values::text END)::json AS success_evaluation,
                MAX(CASE WHEN f.slug = 'summary' THEN df.values::text END)::json AS summary,
                STRING_AGG(kb.name, ',' ORDER BY kb.name) AS kb_names,
                STRING_AGG(kb.token, ',' ORDER BY kb.name) AS kb_tokens
                FROM core_components_pilot AS cp
                LEFT JOIN space_space AS ss ON cp.space_id = ss.id
                LEFT JOIN core_components_model AS llm ON cp.llm_model_id = llm.id
                LEFT JOIN core_components_provider AS prov ON llm.provider_id = prov.id
                LEFT JOIN core_components_pilotlink AS pl ON pl.pilot_id = cp.id
                    AND pl.content_type_id = (
                        SELECT id FROM django_content_type WHERE model = 'space' LIMIT 1
                    )
                LEFT JOIN space_space AS kb ON pl.object_id = kb.id
                    AND kb.space_type = 'knowledge_base'
                LEFT JOIN dynamic_form_values AS df ON df.parent_id = cp.handle
                LEFT JOIN dynamic_forms AS f ON df.form_id = f.id AND f.slug IN ('structured-data', 'success-evaluation', 'summary')
                WHERE cp.handle = %s
                GROUP BY cp.id, cp.space_id, cp.handle, cp.llm_model_id,
                         cp.telephony_config::text, cp.greeting_message, cp.system_prompt,
                         cp.ai_persona, cp.followup_prompt, cp.handover_prompt,
                         cp.back_off_seconds, cp.voice_seconds, cp.enable_callback,
                         cp.enable_followup, cp.enable_handover, cp.number_of_words,
                         cp.voice_temperature, cp.voice_speed, cp.voice_prompt, llm.codename, cp.instant_handover ,
                         cp.calling_days::text, cp.calling_time_ranges::text, cp.enable_memory,
                         cp.handover_number, prov.name, llm.name, llm.config::text,
                         llm.inference, llm.realtime_sts, ss.id, ss.name, ss.token,
                         ss.space_type;
            """

            # Use parameterized query for safety
            results = executeQuery(query, params=(agent_id,), many=True)
            if not results:
                return {}

            # Process the main result
            main_result = results[0]

            # print(main_result)
            # Parse telephony config once
            tele_config_raw = main_result["telephony_config"]
            tele_dict = {}
            if tele_config_raw:
                try:
                    if isinstance(tele_config_raw, str):
                        tele_dict = json.loads(tele_config_raw)
                    else:
                        tele_dict = tele_config_raw

                    # Try to evaluate if it's a string representation
                    if isinstance(tele_dict, str):
                        tele_dict = ast.literal_eval(tele_dict)
                except (ValueError, SyntaxError, json.JSONDecodeError):
                    tele_dict = {}

            # Extract knowledge base spaces from concatenated results
            knowledge_base_spaces = []
            kb_names = main_result.get("kb_names")
            kb_tokens = main_result.get("kb_tokens")

            if kb_names and kb_tokens:
                names = kb_names.split(",")
                tokens = kb_tokens.split(",")

                # Combine names and tokens
                for name, token in zip(names, tokens):
                    if name and token:
                        knowledge_base_spaces.append(
                            {"name": name.strip(), "token": token.strip()}
                        )

            # Build the model config
            handover_numbers = main_result.get("handover_number",[])
            if handover_numbers and isinstance(handover_numbers,str):
                try:
                    if ',' in  handover_numbers:
                        handover_numbers = handover_numbers.split(',')
                    else:
                        handover_numbers=handover_numbers
                except Exception as e:
                    print(e)
                    handover_numbers = []

            if tele_dict:
                query = """
                    select tp.name, model.inference, model.realtime_sts
                    from core_components_model as model
                    inner join core_components_provider as tp on tp.id = model.provider_id
                    where model.name=%(model_name)s
                """

                params = {
                    "model_name": tele_dict.get("transcriber", {}).get("model"),
                }

                stt_provider = executeQuery(query, params=params) or {}
                params = {
                    "model_name": tele_dict.get("voice", {}).get("model"),
                }
                tts_provider = executeQuery(query, params=params) or {}

                query = "select inference,realtime_sts as realtime from core_components_voice where code=%(voice)s"

                voice_dict = executeQuery(
                    query, params={"voice": tele_dict.get("voice", {}).get("voice")}
                ) or {}

            else:
                stt_provider = {}
                tts_provider = {}
                voice_dict = {
                    "inferece": 0,
                    "realtime_sts": 0,
                }
                tele_dict = {
                    "voice": {
                        "model": "tts-1",
                        "voice": "alloy",
                    },
                    "quality": "good",
                    "transcriber": {
                        "model": "whisper-1",
                        "language": "en",
                    },
                }

            # Safe lowercase helper for nullable fields
            def safe_lower(value: str | None, default: str = "") -> str:
                return value.lower() if value else default

            # Check for voice-specific inference flag from telephony config
            # This takes precedence over model-level inference flag
            voice_config = tele_dict.get("voice", {})
            voice_inference_flag = voice_config.get("voice_inference")

            # If voice has explicit inference flag, use it; otherwise fallback to model
            if voice_inference_flag is not None:
                tts_inference_enabled = bool(voice_inference_flag)
            else:
                tts_inference_enabled = bool(tts_provider.get("inference"))

            model_config = {

                "agent_id": agent_id,
                "llm_provider": main_result["llm_provider"] or "openai",
                "llm_model": safe_lower(main_result["llm_model"], "gpt-4o-mini"),
                "llm_config": main_result["llm_config"],
                "llm_inference": bool(main_result["llm_inference"]),
                "llm_realtime": bool(main_result["llm_realtime"]),
                "stt_provider": safe_lower(stt_provider.get("name"), "openai"),
                "stt_model": tele_dict.get("transcriber", {}).get("model"),
                "stt_realtime": bool(stt_provider.get("realtime")),
                "stt_inference": bool(stt_provider.get("inference")),
                "language": tele_dict.get("transcriber", {}).get("language"),
                "telephony": tele_dict.get("telephony"),
                "tts_provider": safe_lower(tts_provider.get("name"), "openai"),
                "tts_model": voice_config.get("model"),
                "tts_voice": voice_config.get("voice"),
                "tts_inference": tts_inference_enabled,
                "tts_realtime": bool(tts_provider.get("realtime")),
                "first_message": main_result["greeting_message"],
                "sms_enabled":bool(main_result["sms_enabled"]),
                "system_prompt": main_result["system_prompt"]
                .encode()
                .decode("unicode-escape"),
                "voice_inference": bool(voice_dict.get("inference")),
                "voice_temperature": main_result["voice_temperature"],
                "voice_speed":main_result["voice_speed"],
                "voice_instructions": main_result.get("voice_prompt"),
                "voice_realtime": bool(voice_dict.get("realtime")),
                "enable_memory": bool(main_result["enable_memory"]),
                "persona": main_result["ai_persona"],
                "space_name": main_result["space_name"],
                "space_id": main_result["space_id"],
                "space_token": main_result["space_token"],
                "knowledge_base": knowledge_base_spaces,
                "quality": tele_dict.get("quality", "good"),
                "instant_handover":main_result["instant_handover"],
                "speaking_plan": {
                    "min_silence_duration": main_result["backoff_seconds"],
                    "min_interruption_duration": main_result["voice_seconds"],
                    "min_interruption_words": main_result["number_of_words"],
                },
                "handover_number": handover_numbers,
                "handover_enabled": bool(main_result["handover_enabled"]),
                "callback_enabled": bool(main_result["callback_enabled"]),
                "follow_up_enabled": bool(main_result["follow_up_enabled"]),
                "calling_days": main_result["calling_days"],
                "calling_time_ranges": main_result["calling_time_ranges"],
                "conversation_playbook": [],  # Conversation playbook can be added here
                "pre_call_playbook": [],  # Pre call playbook can be added here
                "followup_prompt": main_result["followup_prompt"],
                "handover_prompt": main_result["handover_prompt"],
                "post_call_playbook": [
                    {"success_evaluation": main_result["success_evaluation"]},
                    {"structured_data": main_result["structured_data"]},
                    {"summary": main_result["summary"]},
                ],  # Post call playbook can be added here
            }

            # logger.info(f"Model-Config-{agent_id}: {model_config}")
            _set_cached_config(agent_id, model_config)

            return model_config

        except Exception as e:
            logger.error(f"Error in get_config: {str(e)}")
            print(f"Error: {str(e)}")
            return {}

    def send_config(self, token, **kwargs):
        pass


class MessageCallBack(BaseCallback):
    def __init__(self, *args, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def send(self, message: Message, thread_id: str):
        # Skip saving if thread_id is empty or None
        if not thread_id:
            logger.warning(
                "[MessageCallBack] Skipping block save - no thread_id available"
            )
            return

        if not isinstance(message, Message):
            message = Message.add_assistant_message(message)

        # Skip empty messages
        content = message.message
        data = message.data
        if not content and (not data or not isinstance(data, dict)):
            return

        # Debug: Log block save attempt
        logger.info(
            f"[MessageCallBack] Saving block for thread_id={thread_id}, "
            f"role={message.sender.role}, content_len={len(content or '')}"
        )

        # Save block using Message-based function
        block = save_message_block(message, thread_id)
        if not block:
            logger.warning(
                f"[MessageCallBack] save_message_block returned empty for thread_id={thread_id}"
            )
            return

        # Debug: Log successful save
        logger.info(
            f"[MessageCallBack] Block saved: block_id={block.get('block_id')}, "
            f"thread_id={thread_id}"
        )

        # Extract user for channel broadcast
        sender_user, _ = _extract_user_from_message(message)

        # Determine event type for channel
        event = (
            "block"
            if message.event not in [Event.TASK_END, Event.TASK_START]
            else message.event
        )
        send_block_to_channel(thread_id, block, sender_user, event=event)

    def receive(self, message: Message):
        print("Receive", message)


if __name__ == "__main__":
    configs = ModelConfig().get_config("gamestop-iu3kqyk3rf4x")
    print(configs)
