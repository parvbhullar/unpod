"""
SuperVoice Mini-App - Main application entry point
"""

import asyncio
import logging
import os
import yaml
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

from super.core.configuration.base_config import BaseModelConfig
from .super_voice_agent import SuperVoiceAgent, AgentConfig
from .sip_dispatcher import SIPDispatcher, SIPTrunkConfig, CallDispatchRule
from .transport_factory import SuperTransportFactory


class VoiceModelConfig(BaseModelConfig):
    """Voice model configuration implementation"""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
    
    def get_config(self, token: str, **kwargs) -> Dict[str, Any]:
        """Get configuration for given token/space"""
        space_configs = self.config_data.get("space_configs", {})
        default_config = self.config_data.get("default_config", {})
        
        # Return space-specific config or default
        return space_configs.get(token, default_config)


class SuperVoiceApp:
    """
    SuperVoice Mini-App - Complete voice calling application
    
    Features:
    - Multiple transport support (LiveKit, WebRTC, WebSocket)
    - SIP call dispatching and routing
    - Agent lifecycle management
    - REST API for call control
    - WebSocket for real-time events
    - Configuration management
    """
    
    def __init__(self, config_path: str = "config/voice_config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # Core components
        self.sip_dispatcher: Optional[SIPDispatcher] = None
        self.active_agents: Dict[str, SuperVoiceAgent] = {}
        self.model_config: Optional[VoiceModelConfig] = None
        
        # FastAPI app
        self.app = FastAPI(title="SuperVoice API", version="1.0.0")
        self._setup_routes()
    
    async def initialize(self):
        """Initialize the voice application"""
        try:
            # Setup model config
            self.model_config = VoiceModelConfig(self.config.get("model_config", {}))
            
            # Initialize SIP dispatcher if LiveKit is configured
            if self._is_livekit_configured():
                await self._setup_sip_dispatcher()
            
            self.logger.info("SuperVoice App initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SuperVoice App: {e}")
            return False
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the FastAPI server"""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _is_livekit_configured(self) -> bool:
        """Check if LiveKit is properly configured"""
        livekit_config = self.config.get("livekit", {})
        required_fields = ["url", "api_key", "api_secret"]
        return all(livekit_config.get(field) for field in required_fields)
    
    async def _setup_sip_dispatcher(self):
        """Setup SIP dispatcher with configuration"""
        livekit_config = self.config["livekit"]
        
        self.sip_dispatcher = SIPDispatcher(
            livekit_url=livekit_config["url"],
            api_key=livekit_config["api_key"],
            api_secret=livekit_config["api_secret"],
            logger=self.logger
        )
        
        if not await self.sip_dispatcher.initialize():
            raise Exception("Failed to initialize SIP dispatcher")
        
        # Load SIP trunks and dispatch rules from config
        await self._load_sip_configuration()
    
    async def _load_sip_configuration(self):
        """Load SIP trunks and dispatch rules"""
        sip_config = self.config.get("sip", {})
        
        # Load SIP trunks
        for trunk_data in sip_config.get("trunks", []):
            agent_config = self._create_agent_config(trunk_data.get("agent_config", {}))
            
            trunk_config = SIPTrunkConfig(
                trunk_id=trunk_data["trunk_id"],
                name=trunk_data["name"],
                inbound_number=trunk_data["inbound_number"],
                outbound_numbers=trunk_data.get("outbound_numbers", []),
                agent_config=agent_config
            )
            self.sip_dispatcher.add_sip_trunk(trunk_config)
        
        # Load dispatch rules
        for rule_data in sip_config.get("dispatch_rules", []):
            agent_config = self._create_agent_config(rule_data["agent_config"])
            
            rule = CallDispatchRule(
                rule_id=rule_data["rule_id"],
                conditions=rule_data["conditions"],
                agent_config=agent_config,
                priority=rule_data.get("priority", 100)
            )
            self.sip_dispatcher.add_dispatch_rule(rule)
    
    def _create_agent_config(self, config_data: Dict[str, Any]) -> AgentConfig:
        """Create agent config from configuration data"""
        return AgentConfig(
            agent_name=config_data.get("agent_name", "SuperVoiceAgent"),
            model_config=self.model_config,
            transport_type=config_data.get("transport_type", "livekit"),
            transport_options=config_data.get("transport_options", {}),
            auto_answer=config_data.get("auto_answer", True),
            session_timeout=config_data.get("session_timeout", 300),
            enable_sip=config_data.get("enable_sip", True),
            sip_trunk_id=config_data.get("sip_trunk_id"),
            knowledge_bases=config_data.get("knowledge_bases", [])
        )
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "SuperVoice API", "version": "1.0.0"}
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "active_agents": len(self.active_agents),
                "sip_dispatcher": self.sip_dispatcher is not None,
                "transports": list(SuperTransportFactory.list_available_transports().keys())
            }
        
        @self.app.post("/calls/outbound")
        async def initiate_outbound_call(request: Dict[str, Any]):
            """Initiate outbound call"""
            try:
                if not self.sip_dispatcher:
                    raise HTTPException(status_code=400, detail="SIP dispatcher not available")
                
                to_number = request["to_number"]
                agent_config_data = request.get("agent_config", {})
                from_number = request.get("from_number")
                trunk_id = request.get("trunk_id")
                
                agent_config = self._create_agent_config(agent_config_data)
                
                call_id = await self.sip_dispatcher.initiate_outbound_call(
                    to_number=to_number,
                    agent_config=agent_config,
                    from_number=from_number,
                    trunk_id=trunk_id
                )
                
                if call_id:
                    return {"success": True, "call_id": call_id}
                else:
                    raise HTTPException(status_code=500, detail="Failed to initiate call")
                    
            except KeyError as e:
                raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/calls/{call_id}/end")
        async def end_call(call_id: str):
            """End active call"""
            try:
                if self.sip_dispatcher:
                    success = await self.sip_dispatcher.end_call(call_id)
                    return {"success": success}
                else:
                    # Handle direct agent calls
                    if call_id in self.active_agents:
                        await self.active_agents[call_id].shutdown()
                        del self.active_agents[call_id]
                        return {"success": True}
                    else:
                        raise HTTPException(status_code=404, detail="Call not found")
                        
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/calls")
        async def list_active_calls():
            """List active calls"""
            try:
                if self.sip_dispatcher:
                    return self.sip_dispatcher.get_active_calls()
                else:
                    return [{"agent_id": agent_id, "status": "active"} 
                           for agent_id in self.active_agents.keys()]
                           
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/stats")
        async def get_stats():
            """Get application statistics"""
            try:
                if self.sip_dispatcher:
                    return self.sip_dispatcher.get_call_stats()
                else:
                    return {
                        "active_agents": len(self.active_agents),
                        "transports": SuperTransportFactory.list_available_transports()
                    }
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/agents/create")
        async def create_agent(request: Dict[str, Any]):
            """Create new voice agent"""
            try:
                agent_config = self._create_agent_config(request)
                agent = SuperVoiceAgent(agent_config)
                
                if await agent.initialize():
                    self.active_agents[agent.session_id] = agent
                    return {
                        "success": True, 
                        "agent_id": agent.session_id,
                        "transport": agent_config.transport_type
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to initialize agent")
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time events"""
            await websocket.accept()
            try:
                while True:
                    # Handle WebSocket messages
                    data = await websocket.receive_text()
                    # Echo for now - can be enhanced for real-time control
                    await websocket.send_text(f"Echo: {data}")
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
            finally:
                await websocket.close()
        
        @self.app.post("/webhooks/livekit")
        async def livekit_webhook(request: Request):
            """Handle LiveKit webhook events"""
            try:
                if not self.sip_dispatcher:
                    return JSONResponse({"status": "ignored"})
                
                body = await request.json()
                event_type = body.get("event")
                event_data = body.get("data", {})
                
                from .sip_dispatcher import SIPWebhookHandler
                webhook_handler = SIPWebhookHandler(self.sip_dispatcher)
                await webhook_handler.handle_webhook(event_type, event_data)
                
                return JSONResponse({"status": "processed"})
                
            except Exception as e:
                self.logger.error(f"Webhook error: {e}")
                return JSONResponse({"status": "error", "message": str(e)})
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "model_config": {
                "default_config": {
                    "system_prompt": "You are a helpful voice assistant.",
                    "first_message": "Hello! How can I help you today?",
                    "knowledge_base": []
                },
                "space_configs": {
                    "SPACE123": {
                        "system_prompt": "You are an English-speaking customer service agent.",
                        "first_message": "Hello! Welcome to our service. How may I assist you?",
                        "knowledge_base": ["customer_service"]
                    }
                }
            },
            "livekit": {
                "url": os.getenv("LIVEKIT_URL", "wss://your-livekit-url"),
                "api_key": os.getenv("LIVEKIT_API_KEY", ""),
                "api_secret": os.getenv("LIVEKIT_API_SECRET", "")
            },
            "sip": {
                "trunks": [],
                "dispatch_rules": []
            }
        }


async def main():
    """Main entry point"""
    app = SuperVoiceApp()
    
    if await app.initialize():
        await app.start_server()
    else:
        print("Failed to initialize SuperVoice App")


if __name__ == "__main__":
    asyncio.run(main())
