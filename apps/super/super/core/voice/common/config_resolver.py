"""
Agent Config Resolver - Standalone configuration resolution for voice/chat agents.

This module provides configuration resolution utilities that can be used by any
agent handler (VoiceAgentHandler, SuperkikAgentHandler, etc.).

Config resolution handles three scenarios:
1. SDK/web calls: agent_handle or space_token in metadata
2. Inbound SIP calls: phone number from participant attributes
3. Outbound calls: model_config in metadata or agent_id lookup
"""

from __future__ import annotations

import asyncio
import os
import logging
from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from livekit.agents import JobContext

logger = logging.getLogger("voice.config_resolver")


@dataclass
class AgentConfigResult:
    """Result from agent config resolution."""

    model_config: Dict[str, Any]
    user_data: Dict[str, Any]
    pilot_data: Optional[Dict[str, Any]] = None
    participant: Optional[Any] = None
    call_type: str = "inbound"


async def get_config_with_cache(
    agent_handle: Optional[str] = None,
    space_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get agent configuration with caching.

    Uses ModelConfig from super_services to fetch configuration
    by agent handle or space token.

    Args:
        agent_handle: Agent identifier/slug
        space_token: Space token for SDK calls

    Returns:
        Model configuration dict or None
    """
    from super_services.voice.models.config import ModelConfig

    config_loader = ModelConfig()
    config = None

    if agent_handle:
        logger.debug(f"Fetching config for agent_handle: {agent_handle}")
        config = config_loader.get_config(agent_handle)

    if not config and space_token:
        logger.debug(f"Fetching config for space_token")
        config = config_loader.get_config_by_token(space_token)

    return config


async def get_agent_number_from_ctx(ctx: "JobContext") -> Optional[str]:
    """
    Get the agent's phone number from SIP participant attributes.

    Args:
        ctx: LiveKit job context

    Returns:
        Phone number string or None
    """
    result = await get_agent_info_from_ctx(ctx)
    return result.get("phone_number") if result else None


async def get_agent_info_from_ctx(ctx: "JobContext") -> Optional[Dict[str, Any]]:
    """
    Get agent identification info from participant attributes.

    For SIP calls: looks for sip.trunkPhoneNumber or sip.calledNumber
    For web calls: looks for agent.name or lk.agent_name attributes

    Args:
        ctx: LiveKit job context

    Returns:
        Dict with 'phone_number' and/or 'agent_handle', or None
    """
    from livekit import api

    try:
        async def _get_participants():
            async with api.LiveKitAPI() as lkapi:
                from livekit.api import ListParticipantsRequest

                return await lkapi.room.list_participants(
                    ListParticipantsRequest(room=ctx.room.name)
                )

        participants = await asyncio.wait_for(_get_participants(), timeout=5.0)
    except asyncio.TimeoutError:
        logger.error("Timeout getting agent info from LiveKit API (5s)")
        return None
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        return None

    result = {}

    for participant in participants.participants:
        attrs = dict(participant.attributes) if participant.attributes else {}

        # Check for SIP phone number
        phone = (
            attrs.get("sip.trunkPhoneNumber")
            or attrs.get("sip.calledNumber")
            or attrs.get("sip.phoneNumber")
        )
        if phone:
            result["phone_number"] = phone

        # Check for agent handle
        agent_name = (
            attrs.get("agent.name")
            or attrs.get("lk.agent_name")
            or attrs.get("agent_handle")
        )
        if agent_name:
            result["agent_handle"] = agent_name

        if result:
            break

    return result if result else None


async def resolve_sdk_call_config(
    ctx: "JobContext",
    metadata: Dict[str, Any],
) -> Optional[Tuple[Dict, Dict, Dict]]:
    """
    Resolve configuration for SDK/web calls.

    Args:
        ctx: LiveKit job context
        metadata: Job metadata with agent_handle or space_token

    Returns:
        Tuple of (model_config, user_data, pilot_data) or None
    """
    agent_handle = metadata.get("agent_handle")
    space_token = metadata.get("space_token")

    logger.info(
        f"[SDK] Resolving config: agent_handle={agent_handle}, "
        f"space_token={'set' if space_token else 'none'}"
    )

    _start = perf_counter()

    # Get config from handle or token
    config = await get_config_with_cache(
        agent_handle=agent_handle,
        space_token=space_token,
    )

    logger.info(
        f"[SDK] Config fetch: {(perf_counter() - _start) * 1000:.0f}ms"
    )

    if not config:
        logger.error(f"[SDK] No config found for handle={agent_handle}")
        return None

    # Build user_data from metadata
    user_data = metadata.get("data", {})

    # Get pilot data for space info
    pilot_data = {}
    if space_token:
        from super.core.voice.common.pilot import get_space_id

        pilot_data = {
            "space_token": space_token,
            "space_id": get_space_id(space_token),
        }

    return config, user_data, pilot_data


async def resolve_inbound_sip_config(
    ctx: "JobContext",
) -> Tuple[Optional[Dict], Optional[Dict], Optional[Any]]:
    """
    Resolve config for inbound SIP calls by phone number lookup.

    Args:
        ctx: LiveKit job context

    Returns:
        Tuple of (model_config, pilot_data, participant)
    """
    _start = perf_counter()
    logger.info("[INBOUND] Starting SIP config resolution...")

    async def resolve_config_by_number():
        agent_number = await get_agent_number_from_ctx(ctx)
        logger.info(f"[INBOUND] Agent number: {agent_number}")

        if not agent_number:
            logger.warning("[INBOUND] Could not get agent number")
            return None, None

        from super.core.voice.common.pilot import get_pilot_and_space_for_number

        pilot_data = await get_pilot_and_space_for_number(agent_number)
        if not pilot_data:
            logger.warning(f"[INBOUND] No pilot for number: {agent_number}")
            return None, None

        slug = pilot_data.get("pilot")
        config = await get_config_with_cache(agent_handle=slug)

        if not config:
            logger.warning(f"[INBOUND] No config for pilot: {slug}")
            return None, pilot_data

        return config, pilot_data

    # Run participant wait and config resolution in parallel
    try:
        participant, (model_config, pilot_data) = await asyncio.gather(
            asyncio.wait_for(ctx.wait_for_participant(), timeout=30.0),
            resolve_config_by_number(),
            return_exceptions=False,
        )
    except asyncio.TimeoutError:
        logger.error("[INBOUND] Timeout waiting for participant")
        return None, None, None
    except Exception as e:
        logger.error(f"[INBOUND] Resolution error: {e}")
        return None, None, None

    logger.info(f"[INBOUND] Resolution: {(perf_counter() - _start) * 1000:.0f}ms")

    if not participant:
        return None, None, None

    # Fallback to default agent if needed
    if not model_config:
        default_agent = os.getenv("DEFAULT_VOICE_AGENT")
        if default_agent:
            logger.info(f"[INBOUND] Using default agent: {default_agent}")
            model_config = await get_config_with_cache(agent_handle=default_agent)
            pilot_data = {"pilot": default_agent}

    return model_config, pilot_data, participant


async def resolve_agent_config(
    ctx: "JobContext",
    metadata: Dict[str, Any],
) -> Optional[AgentConfigResult]:
    """
    Main config resolver - handles SDK, inbound SIP, and outbound calls.

    Args:
        ctx: LiveKit JobContext
        metadata: Parsed job metadata

    Returns:
        AgentConfigResult or None if resolution failed
    """
    user_data = metadata.get("data", {})
    model_config = metadata.get("model_config", {})
    pilot_data = None
    participant = None
    call_type = "outbound" if metadata.get("call_type") == "outbound" else "inbound"

    # Case 1: SDK/web calls with agent_handle or space_token
    if not model_config and (
        metadata.get("agent_handle") or metadata.get("space_token")
    ):
        result = await resolve_sdk_call_config(ctx, metadata)
        if not result:
            return None
        model_config, user_data, pilot_data = result

        # Wait for participant for SDK calls
        try:
            participant = await asyncio.wait_for(
                ctx.wait_for_participant(), timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error("[SDK] Timeout waiting for participant")
            return None

    # Case 2: Inbound SIP calls - lookup by phone number
    elif call_type == "inbound" and not model_config:
        model_config, pilot_data, participant = await resolve_inbound_sip_config(ctx)
        if not model_config:
            return None

    # Case 3: Outbound calls with model_config already in metadata
    elif call_type == "outbound" and not model_config:
        agent_id = user_data.get("agent_id")
        if agent_id:
            model_config = await get_config_with_cache(agent_handle=agent_id)

        if not model_config:
            fallback = os.getenv("AGENT_NAME")
            if fallback:
                model_config = await get_config_with_cache(agent_handle=fallback)

        if not model_config:
            logger.error(f"[OUTBOUND] No config for agent_id={agent_id}")
            return None

    # Update user_data with space info for SDK calls
    is_sdk_call = metadata.get("agent_handle") or metadata.get("space_token")
    if is_sdk_call and metadata.get("space_token"):
        from super.core.voice.common.pilot import get_space_id

        if not user_data:
            user_data = {}
        user_data.update({
            "space_token": metadata.get("space_token"),
            "space_id": user_data.get("space_id") or get_space_id(
                metadata.get("space_token")
            ),
        })

    if not user_data and pilot_data:
        user_data = {
            "token": pilot_data.get("token", ""),
            "space_name": pilot_data.get("space_name"),
        }

    logger.info(f"Resolved config for agent: {model_config.get('agent_id', 'unknown')}")

    return AgentConfigResult(
        model_config=model_config,
        user_data=user_data,
        pilot_data=pilot_data,
        participant=participant,
        call_type=call_type,
    )
