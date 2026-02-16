import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from livekit.api import WebhookReceiver, TokenVerifier
from super_services.voice.models.config import ModelConfig , MessageCallBack
from super_services.libs.core.db import executeQuery
from super.core.voice.schema import UserState
load_dotenv()
from cachetools import TTLCache
from super.app.call_execution import execute_call
import threading
import asyncio

def run_in_background(coro):
    def runner():
        asyncio.run(coro)
    threading.Thread(target=runner, daemon=True).start()

class LiveKitWebhookHandler:
    def __init__(self):
        self.app = Flask(__name__)
        self.LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
        self.LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
        self.token = TokenVerifier(self.LIVEKIT_API_KEY, self.LIVEKIT_API_SECRET)
        self.webhook_receiver = WebhookReceiver(self.token)

        self.cache = TTLCache(maxsize=100, ttl=20)

        self.room_name = None
        self.user_number= None
        self.pilot =None
        self.agent_number=None
        # Register routes
        self.app.add_url_rule("/livekit/", view_func=self.receive_webhook, methods=["POST"])


    def get_pilot_slug(self, number: str) -> str | None:
        query = """
        SELECT *
        FROM core_components_pilot
        WHERE EXISTS (
            SELECT 1 FROM jsonb_array_elements(telephony_config->'telephony') elem
            WHERE elem->>'number' = %(number)s
        )
        LIMIT 1;
        """
        res = executeQuery(query, many=True, params={"number": number})
        if res:
            return res[0].get("handle")
        return None

    async def _handle_participant_joined(self, participant: dict):
        self.agent_number = participant.get("attributes", {}).get("sip.trunkPhoneNumber", "")
        self.user_number = participant.get("attributes", {}).get("sip.phoneNumber", "")

        if self.user_number and not self.pilot:
            self.pilot = self.get_pilot_slug(self.agent_number)

            data= {
                "assistant_number":self.agent_number,
                "contact_number":self.user_number,
                "agent_id":self.pilot,
                "room_name" :self.room_name,
                "call_type":'inbound'

            }
            # loop = asyncio.get_running_loop()
            # loop.create_task(execute_call(self.pilot,"",data,"",ModelConfig(),MessageCallBack()))

            run_in_background(execute_call(self.pilot, "", data, "", ModelConfig(), MessageCallBack()))

    def set_initial_state(self):
        self.room_name = None
        self.user_number = None
        self.pilot = None

    async def _handle_participant_left(self):
        print(f"Stopping agent for room {self.room_name}")
        self.set_initial_state()


    async def _process_event(self, event_json: dict):
        event_type = event_json.get("event")
        if event_type == "room_started":
            room = event_json.get("room")
            self.room_name = room.get("name")
            print(f"Room started: {self.room_name}")
            if "pipecat_call" in self.room_name:
               self.agent_number = ''


        elif event_type == "participant_joined"  and "pipecat_call" in self.room_name:
            participant = event_json.get("participant")
            await self._handle_participant_joined(participant)


        elif event_type == "participant_left" and self.room_name:
            room = event_json.get("room")
            self.room_name = room.get("name")
            if "pipecat_call" in self.room_name:
                if self.room_name in self.cache:
                    print(f"Skipping room {self.room_name}, already processed")
                    return

                self.cache[self.room_name] = True
                await self._handle_participant_left()

    async def receive_webhook(self):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return "Authorization header is required", 401

        try:
            raw_body = request.data.decode("utf-8")
            event_json = json.loads(raw_body)
            self.webhook_receiver.receive(raw_body, auth_token)
            await self._process_event(event_json)
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print("Error processing webhook:", e)
            return "Invalid Authorization header", 401

    def run(self, host="0.0.0.0", port=5000):
        self.app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    handler = LiveKitWebhookHandler()
    handler.run()
