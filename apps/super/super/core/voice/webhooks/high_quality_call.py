import uvicorn
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()
import httpx


app = FastAPI()


async def process_context(customer_number: str, assistant_id: str, control_url: str):
    from super.core.voice.common.pilot import get_pilot_from_assistant_id
    from super.core.voice.workflows.pre_call import PreCallWorkFlow

    handle = get_pilot_from_assistant_id(assistant_id)

    if not handle:
        return {"success": False}

    executor = PreCallWorkFlow(agent_id=handle)

    res = executor.execute_inbound(customer_number)

    if not res.get("chat_context"):
        return {"success": False}

    try:
        headers = {
            "Content-Type": "application/json",
        }

        chat_context = res.get("chat_context")

        payload = {
            "type": "add-message",
            "message": {
                "role": "system",
                "content": f"[Past Conversation With The User] \n\n {chat_context}",
            },
            "triggerResponseEnabled": True,
        }

        print(f" adding call context for call ")

        if control_url:
            async with httpx.AsyncClient() as client:
                for i in range(3):
                    response = await client.post(
                        control_url, json=payload, headers=headers
                    )

                    if response.status_code == 200:
                        print("Successfully added control message and chat context")
                        return {"success": True}

                    print(
                        f"Failed to add control message retrying {i+1}/3 : \n {response.text}"
                    )
            print(f"Failed to add control message and chat context ")
            return {"success": False}

        print("no control url available")
    except Exception as e:
        print(str(e))
        return {"success": False}


async def _process_event(event_json: dict):
    event_type = event_json.get("message", {}).get("type")
    call_type = event_json.get("message", {}).get("call", {}).get("type")

    if event_type == "assistant.started" and call_type == "inboundPhoneCall":
        call_data = event_json.get("message", {}).get("call", {})
        customer_numer = call_data.get("customer", {}).get("name")
        control_url = call_data.get("monitor", {}).get("controlUrl", "")
        assistant_id = call_data.get("assistantId")

        await process_context(
            customer_number=customer_numer,
            assistant_id=assistant_id,
            control_url=control_url,
        )

        print(f"{'='*50} {'='*50}")


@app.post("/api/v1/high-quality-calls/")
async def receive_webhook(request: Request):
    try:
        event_json = await request.json()
        await _process_event(event_json)
        return {"status": "success"}

    except Exception as e:
        print("Error processing webhook:", e)
        return {"error": "Invalid Authorization header"}, 401


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
