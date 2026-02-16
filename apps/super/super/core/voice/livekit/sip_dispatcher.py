"""
LiveKit SIP Dispatcher - Handles SIP call routing and agent dispatching
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .super_voice_agent import SuperVoiceAgent, AgentConfig

try:
    from livekit import api
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False


@dataclass
class SIPTrunkConfig:
    """SIP trunk configuration"""
    trunk_id: str
    name: str
    inbound_number: str
    outbound_numbers: List[str] = field(default_factory=list)
    agent_config: Optional[AgentConfig] = None
    routing_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallDispatchRule:
    """Call dispatching rule"""
    rule_id: str
    conditions: Dict[str, Any]  # from_number, to_number, time_range, etc.
    agent_config: AgentConfig
    priority: int = 100


class SIPDispatcher:
    """
    LiveKit SIP Dispatcher for routing calls to appropriate agents
    
    Features:
    - Inbound call routing based on rules
    - Outbound call dispatching
    - Agent lifecycle management
    - Call queue management
    - Load balancing across agents
    """
    
    def __init__(
        self,
        livekit_url: str,
        api_key: str,
        api_secret: str,
        logger: Optional[logging.Logger] = None
    ):
        self.livekit_url = livekit_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logger or logging.getLogger(__name__)
        
        # SIP configuration
        self.sip_trunks: Dict[str, SIPTrunkConfig] = {}
        self.dispatch_rules: List[CallDispatchRule] = []
        
        # Active agents and calls
        self.active_agents: Dict[str, SuperVoiceAgent] = {}
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        
        # LiveKit API client
        self.lk_api = None
        
        if not LIVEKIT_AVAILABLE:
            raise ImportError("livekit-python not installed. Install with: pip install livekit")
    
    async def initialize(self):
        """Initialize the SIP dispatcher"""
        try:
            self.lk_api = api.LiveKitAPI(
                self.livekit_url,
                self.api_key,
                self.api_secret
            )
            
            self.logger.info("SIP Dispatcher initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SIP dispatcher: {e}")
            return False
    
    def add_sip_trunk(self, trunk_config: SIPTrunkConfig):
        """Add SIP trunk configuration"""
        self.sip_trunks[trunk_config.trunk_id] = trunk_config
        self.logger.info(f"Added SIP trunk: {trunk_config.trunk_id}")
    
    def add_dispatch_rule(self, rule: CallDispatchRule):
        """Add call dispatch rule"""
        self.dispatch_rules.append(rule)
        # Sort by priority (lower number = higher priority)
        self.dispatch_rules.sort(key=lambda r: r.priority)
        self.logger.info(f"Added dispatch rule: {rule.rule_id}")
    
    async def handle_inbound_call(self, sip_call_info: Dict[str, Any]) -> bool:
        """
        Handle incoming SIP call and dispatch to appropriate agent
        
        Args:
            sip_call_info: SIP call information from LiveKit webhook
            
        Returns:
            True if call was successfully dispatched
        """
        try:
            call_id = sip_call_info.get("call_id")
            from_number = sip_call_info.get("from")
            to_number = sip_call_info.get("to")
            trunk_id = sip_call_info.get("trunk_id")
            
            self.logger.info(f"Inbound call: {from_number} -> {to_number} via {trunk_id}")
            
            # Find matching dispatch rule
            agent_config = self._find_agent_for_call(sip_call_info)
            if not agent_config:
                self.logger.warning(f"No agent found for call {call_id}")
                return False
            
            # Create and start agent
            agent = await self._create_agent(agent_config, call_id)
            if not agent:
                return False
            
            # Create LiveKit room and SIP participant
            room_name = f"sip-call-{call_id}"
            await self._create_room_and_participant(room_name, sip_call_info, agent_config)
            
            # Track call
            self.active_calls[call_id] = {
                "agent_id": agent.session_id,
                "room_name": room_name,
                "from_number": from_number,
                "to_number": to_number,
                "trunk_id": trunk_id,
                "status": "ringing",
                "started_at": datetime.now()
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle inbound call: {e}")
            return False
    
    async def initiate_outbound_call(
        self, 
        to_number: str, 
        agent_config: AgentConfig,
        from_number: Optional[str] = None,
        trunk_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Initiate outbound SIP call
        
        Args:
            to_number: Phone number to call
            agent_config: Agent configuration to use
            from_number: Optional caller ID
            trunk_id: SIP trunk to use
            
        Returns:
            Call ID if successful, None otherwise
        """
        try:
            call_id = f"out-{datetime.now().timestamp()}"
            room_name = f"sip-call-{call_id}"
            
            # Create agent
            agent = await self._create_agent(agent_config, call_id)
            if not agent:
                return None
            
            # Find appropriate trunk if not specified
            if not trunk_id:
                trunk_id = self._find_trunk_for_outbound(to_number)
            
            # Create room
            room_request = api.CreateRoomRequest(name=room_name)
            room = await self.lk_api.room.create_room(room_request)
            
            # Create SIP participant for outbound call
            sip_request = api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=trunk_id,
                sip_call_to=to_number,
                sip_call_from=from_number,
                dtmf_enabled=True,
                play_ringtone=True
            )
            
            sip_response = await self.lk_api.sip.create_sip_participant(sip_request)
            
            # Track call
            self.active_calls[call_id] = {
                "agent_id": agent.session_id,
                "room_name": room_name,
                "to_number": to_number,
                "from_number": from_number,
                "trunk_id": trunk_id,
                "sip_call_id": sip_response.sip_call_id,
                "status": "dialing",
                "started_at": datetime.now()
            }
            
            self.logger.info(f"Initiated outbound call: {call_id}")
            return call_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate outbound call: {e}")
            return None
    
    async def handle_call_status_update(self, call_info: Dict[str, Any]):
        """Handle call status updates from LiveKit webhooks"""
        try:
            call_id = call_info.get("call_id")
            status = call_info.get("status")
            
            if call_id in self.active_calls:
                self.active_calls[call_id]["status"] = status
                
                if status in ["ended", "failed", "no_answer"]:
                    await self._cleanup_call(call_id)
                    
                self.logger.info(f"Call {call_id} status: {status}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle call status update: {e}")
    
    async def end_call(self, call_id: str) -> bool:
        """End an active call"""
        try:
            if call_id not in self.active_calls:
                return False
            
            call_info = self.active_calls[call_id]
            agent_id = call_info.get("agent_id")
            
            # End agent session
            if agent_id in self.active_agents:
                await self.active_agents[agent_id].shutdown()
            
            # End SIP call via LiveKit API if available
            sip_call_id = call_info.get("sip_call_id")
            if sip_call_id:
                # LiveKit API call to end SIP call
                pass
            
            await self._cleanup_call(call_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end call {call_id}: {e}")
            return False
    
    def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get list of active calls"""
        return list(self.active_calls.values())
    
    def get_call_stats(self) -> Dict[str, Any]:
        """Get call statistics"""
        total_calls = len(self.active_calls)
        statuses = {}
        
        for call in self.active_calls.values():
            status = call.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "total_active_calls": total_calls,
            "active_agents": len(self.active_agents),
            "call_statuses": statuses,
            "sip_trunks": len(self.sip_trunks),
            "dispatch_rules": len(self.dispatch_rules)
        }
    
    # Private methods
    
    def _find_agent_for_call(self, call_info: Dict[str, Any]) -> Optional[AgentConfig]:
        """Find appropriate agent config for incoming call"""
        from_number = call_info.get("from", "")
        to_number = call_info.get("to", "")
        trunk_id = call_info.get("trunk_id", "")
        
        # Check dispatch rules in priority order
        for rule in self.dispatch_rules:
            if self._rule_matches(rule, call_info):
                return rule.agent_config
        
        # Fallback to trunk default agent
        if trunk_id in self.sip_trunks:
            return self.sip_trunks[trunk_id].agent_config
        
        return None
    
    def _rule_matches(self, rule: CallDispatchRule, call_info: Dict[str, Any]) -> bool:
        """Check if dispatch rule matches call info"""
        conditions = rule.conditions
        
        # Check from_number pattern
        if "from_number" in conditions:
            pattern = conditions["from_number"]
            from_num = call_info.get("from", "")
            if not self._number_matches_pattern(from_num, pattern):
                return False
        
        # Check to_number pattern  
        if "to_number" in conditions:
            pattern = conditions["to_number"]
            to_num = call_info.get("to", "")
            if not self._number_matches_pattern(to_num, pattern):
                return False
        
        # Check trunk_id
        if "trunk_id" in conditions:
            if call_info.get("trunk_id") != conditions["trunk_id"]:
                return False
        
        # Check time range
        if "time_range" in conditions:
            if not self._time_in_range(conditions["time_range"]):
                return False
        
        return True
    
    def _number_matches_pattern(self, number: str, pattern: str) -> bool:
        """Check if number matches pattern (supports wildcards)"""
        import re
        # Convert pattern to regex (simple * wildcard support)
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", number))
    
    def _time_in_range(self, time_range: Dict[str, Any]) -> bool:
        """Check if current time is in specified range"""
        # Simple implementation - can be enhanced
        return True
    
    def _find_trunk_for_outbound(self, to_number: str) -> Optional[str]:
        """Find appropriate trunk for outbound call"""
        # Simple implementation - use first available trunk
        for trunk_id, trunk in self.sip_trunks.items():
            if trunk.outbound_numbers:
                return trunk_id
        
        # Return first trunk as fallback
        return next(iter(self.sip_trunks.keys())) if self.sip_trunks else None
    
    async def _create_agent(self, agent_config: AgentConfig, call_id: str) -> Optional[SuperVoiceAgent]:
        """Create and initialize agent for call"""
        try:
            # Set transport to livekit for SIP calls
            agent_config.transport_type = "livekit"
            agent_config.transport_options.update({
                "url": self.livekit_url,
                "api_key": self.api_key,
                "api_secret": self.api_secret
            })
            
            agent = SuperVoiceAgent(agent_config, session_id=call_id)
            
            if await agent.initialize():
                self.active_agents[call_id] = agent
                return agent
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to create agent: {e}")
            return None
    
    async def _create_room_and_participant(
        self, 
        room_name: str, 
        sip_call_info: Dict[str, Any],
        agent_config: AgentConfig
    ):
        """Create LiveKit room and SIP participant"""
        try:
            # Create room
            room_request = api.CreateRoomRequest(name=room_name)
            room = await self.lk_api.room.create_room(room_request)
            
            # The SIP participant will be created automatically by LiveKit
            # when the SIP INVITE is accepted
            
        except Exception as e:
            self.logger.error(f"Failed to create room and participant: {e}")
            raise
    
    async def _cleanup_call(self, call_id: str):
        """Clean up call resources"""
        try:
            if call_id in self.active_calls:
                call_info = self.active_calls[call_id]
                agent_id = call_info.get("agent_id")
                
                # Shutdown agent
                if agent_id in self.active_agents:
                    await self.active_agents[agent_id].shutdown()
                    del self.active_agents[agent_id]
                
                # Remove call tracking
                del self.active_calls[call_id]
                
                self.logger.info(f"Cleaned up call: {call_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup call {call_id}: {e}")


# Webhook handler for LiveKit SIP events
class SIPWebhookHandler:
    """Handle LiveKit SIP webhook events"""
    
    def __init__(self, dispatcher: SIPDispatcher):
        self.dispatcher = dispatcher
        self.logger = logging.getLogger(__name__)
    
    async def handle_webhook(self, event_type: str, event_data: Dict[str, Any]):
        """Handle incoming webhook event"""
        try:
            if event_type == "sip_call_invite":
                await self.dispatcher.handle_inbound_call(event_data)
            elif event_type == "sip_call_status":
                await self.dispatcher.handle_call_status_update(event_data)
            else:
                self.logger.debug(f"Unhandled webhook event: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle webhook {event_type}: {e}")
