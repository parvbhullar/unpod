
from typing import Any,Optional ,List,Dict
from livekit.agents import JobContext
from super.core.voice.schema import  UserState
from livekit.agents.voice import Agent
from livekit.agents.llm import function_tool


class VanillaAgent(Agent):
    def __init__( self,
        handler: "VanillaAgenHandler",
        user_state: "UserState",
        instructions: str,
        tools: Optional[List[Any]] = None,
        ctx: "JobContext" = None,
        config: Optional[Dict[str, Any]] = None,
        ):
        super().__init__(instructions=instructions, tools=tools)
        self.config = config or {}
        self.user_state = user_state
        self.ctx = ctx
        self.handler = handler

    @function_tool(
        name="voicemail_detector",
        description="Call this tool if you have detected a voicemail system, AFTER hearing the voicemail greeting. Use when you detect an automated answering machine or voicemail greeting.",
    )
    async def detected_answering_machine(self):
        """Call this tool if you have detected a voicemail system, AFTER hearing the voicemail greeting"""
        pass

    async def on_enter(self) -> None:
        await super().on_enter()
        print(f"\n\n VanillaAgent enter Entered the chat \n\n ")
        first_msg = self.config.get("first_message", "Hello! How can I assist you today?")
        await self.session.say(first_msg)
