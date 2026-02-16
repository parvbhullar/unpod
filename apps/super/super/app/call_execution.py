import random
import time
import requests
import os
import traceback


from super.core.config.constants import AGENTS_SEARCH_API
from super.app.call_agents import agent_ids_list, agent_ids
from super.app.call_profile import update_profile_by_task_id
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig
from super.core.logging import logging
from super.core.logging.logging import print_log
from super.core.voice.workflows.post_call import PostCallWorkflow
from super.core.voice.workflows.dspy_config import get_dspy_lm
from super_services.libs.core.timezone_utils import normalize_phone_number
from super_services.voice.common.threads import (
    # create_thread_post,
    get_user_id,
)
from super.core.voice.schema import UserState
from super.core.voice.workflows.pre_call import PreCallWorkFlow

API_SERVICE_URL = os.environ.get("API_SERVICE_URL", "http://0.0.0.0:9116/api/v1").rstrip("/")
BULK_UPDATE_API = API_SERVICE_URL + "/store/collection-doc-bulk-update/"

# Setup logger
logger = logging.get_logger(__name__)


def fetch_script(agent, data):
    objective = data.get("objective")

    api_url = AGENTS_SEARCH_API
    data = {"query": "Agent", "handle": [agent]}
    response = requests.post(api_url, json=data)
    response.raise_for_status()
    agent_docs = response.json().get("data", [])
    if not agent_docs:
        return "Agent not found"
    persona = agent_docs[0]["metadata"]["persona"]

    prompt = f"""
            [Role]
            You are an AI assistant named {persona} who communicates in English. Your primary task is to execute the call with given objective: {objective}.

            [Context]
            You are engaged with a customer to deliver the message : {objective}.Once message is delivered, end the call by using 'endcallFunction'.

            [Response Guidelines]
            *   Keep responses brief.
            *   Just deliver the message.
            *   Maintain a calm, empathetic, and professional tone.
            *   Answer only the question posed by the user.
            *   Begin responses with direct answers, without introducing additional data.
            *   Never say the word 'function' nor 'tools' nor the name of the Available functions.
            *   Never say ending the call or 'triggering the end of the call'.
            """
    return prompt



def format_number(phone_number: str) -> str | None:
    return normalize_phone_number(phone_number)


def create_general_call(agent, data):
    print("create_general_call", agent)
    try:
        if not all([agent, data]):
            return "Please provide all required information."
        auth_token = os.getenv("VAPI_API_KEY")
        vapi_phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
        if not auth_token or not vapi_phone_number_id:
            return "Missing VAPI credentials in environment variables."
        number = data["contact_number"]
        name = data.get("contact_name") or data.get("name") or "User"
        try:
            formatted_number = format_number(number)
        except ValueError as e:
            return f"Invalid phone number format."
        scripts = fetch_script(agent, data)
        json_data = {
            "phoneNumberId": vapi_phone_number_id,
            "customer": {"name": name, "number": formatted_number},
            "assistant": {
                "transcriber": {
                    "provider": "deepgram",
                    "language": "en",  # "hi" if 'hindi' in agent else "en",
                    "model": "nova-2",
                },
                "model": {
                    "provider": "openai",
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": f"{scripts}"},
                    ],
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "wlmwDR77ptH6bKHZui0l",
                    "model": "eleven_turbo_v2",
                },
                "firstMessageMode": "assistant-speaks-first",
                "firstMessage": f"Hi I have a message for You from {name}",
                "endCallMessage": "Thank You",
                "recordingEnabled": True,
                "endCallFunctionEnabled": True,
                "startSpeakingPlan": {"smartEndpointingEnabled": True},
            },
        }

        print(f"Making call to {formatted_number}")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.vapi.ai/call/phone",
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json",
            },
            json=json_data,
        )

        if response.status_code in [200, 201]:
            call_data = response.json()
            response = {"response": call_data, "headers": headers}
            return response
        else:
            return f"Failed to start call: {response.text}"

    except Exception as e:
        return f"Error starting call: {str(e)}"


def get_agent_id(agent_name):
    return agent_ids.get(agent_name, None)


def start_vapi_call(agent, data):
    """Start a VAPI call with the given contact information dynamically, record transcript and extract summary."""
    try:
        # Previous validation checks remain the same
        if not all([agent, data]):
            return "Please provide all required information."

        from super_services.voice.models.config import ModelConfig

        pilot_data = ModelConfig().get_config(agent)

        agent_id = data.get("vapi_agent_id", get_agent_id(agent))

        if not agent_id:
            call_response = create_general_call(agent, data=data)
            return call_response

        print_log("start_vapi_call with agent_id", agent_id)

        auth_token = os.getenv("VAPI_API_KEY")
        # vapi_phone_number_id = data.get("number_id", os.getenv("VAPI_PHONE_NUMBER_ID"))

        telephony_list = pilot_data.get("telephony", [])
        print_log(
            "telephony_numbers - ", [n.get("number", "NA") for n in telephony_list]
        )
        if not telephony_list:
            return "No telephony numbers configured."
        tel_number = random.choice(telephony_list)
        vapi_phone_number_id = tel_number.get("association", {}).get(
            "phone_number_id", os.getenv("VAPI_PHONE_NUMBER_ID")
        )
        print_log(
            "picked phone number - ",
            tel_number.get("number", "NA"),
            vapi_phone_number_id,
        )
        # vapi_phone_number_id = "1c2223c6-d861-439e-a0b9-f7faf19a285b"

        name = data.get("contact_name") or data.get("name") or "User"
        number = data.get("contact_number")
        if not auth_token or not vapi_phone_number_id:
            return "Missing VAPI credentials in environment variables."

        try:
            formatted_number = format_number(number)
        except ValueError as e:
            return f"Invalid phone number format."

        mailing_address = data.get("address", "New Delhi")
        source_name = data.get("source", "Website")
        # location = mailing_address.split(',')[1].strip() if ',' in mailing_address else 'New Delhi'
        company_name = data.get("company_name", "Unpod AI")
        alternate_slots = data.get(
            "alternate_slots", ["Tuesday at 10 AM", "Thursday at 2 PM"]
        )

        # Keys that are used internally and should not be passed to variableValues
        internal_keys = {
            "contact_number",
            "contact_name",
            "number_id",
            "vapi_agent_id",
            "token",
            "document_id",
            "thread_id",
            "user_id",
            "call_type",
            "pre_call_result",
        }

        # Build variable values with defaults
        variable_values = {
            "name": name,
            "customer_name": name,
            "mailing_address": mailing_address,
            "location": (
                mailing_address.split(",")[1].strip()
                if "," in mailing_address
                else "New Delhi"
            ),
            "agent_name": agent,
            "source": source_name,
            "context": (
                data.get("context") if "context" in data else data["objective"]
            ),
            "company_name": company_name,
            "alternate_slots": alternate_slots,
        }

        # Iterate through all input data keys and add to variable_values
        # (input data takes precedence, skip internal keys)
        for key, value in data.items():
            if key not in internal_keys:
                variable_values[key] = value

        json_data = {
            "assistantId": agent_id,
            "phoneNumberId": vapi_phone_number_id,
            "customer": {"name": name, "number": formatted_number},
            "assistantOverrides": {
                "artifactPlan": {
                    "recordingEnabled": True,
                    "recordingFormat": "wav;l16",
                    "recordingUseCustomStorageEnabled": True,
                },
                "variableValues": variable_values,
            },
        }
        print(f"Making call to {formatted_number}")
        print(f"Using agent ID: {agent_id}")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        response = None

        for i in range(2):
            response = requests.post(
                "https://api.vapi.ai/call/phone",
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Content-Type": "application/json",
                },
                json=json_data,
            )
            if response.status_code in [200, 201]:
                call_data = response.json()
                response = {"response": call_data, "headers": headers}
                return response
            else:
                print(f"Failed to start call Retrying ({i+1}/2)")
                # print(response.text)
                json_data["phoneNumberId"] = os.getenv("VAPI_PHONE_NUMBER_ID")

        return f"Failed to start call {response.text}"

    except Exception as e:
        traceback.print_exc()
        return f"Error starting call: {str(e)}"


def get_matching_agent(agent_id):
    matching_agents = [agent for agent in agent_ids_list if agent_id.startswith(agent)]
    if matching_agents:
        return max(matching_agents, key=len)  # Return the longest matching agent
    return "general"


def normalize_transcript(transcript) -> list:
    """
    Normalize transcript to list format.

    VAPI returns transcript as a string, but we need it in list format with role/content structure.
    This function converts string format to list format.

    Args:
        transcript: Either a string (VAPI format) or list (already normalized)

    Returns:
        list: Normalized transcript in list format
    """
    if isinstance(transcript, list):
        # Already in correct format
        return transcript

    if isinstance(transcript, str):
        # Parse string format: "AI: text\nUser: text\n..."
        normalized = []
        lines = transcript.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line starts with role indicator
            if line.startswith("AI:") or line.startswith("Assistant:"):
                content = line.split(":", 1)[1].strip() if ":" in line else line
                normalized.append(
                    {
                        "role": "assistant",
                        "content": content,
                        "user_id": None,
                        "timestamp": "",
                    }
                )
            elif line.startswith("User:"):
                content = line.split(":", 1)[1].strip() if ":" in line else line
                normalized.append(
                    {
                        "role": "user",
                        "content": content,
                        "user_id": "unknown",
                        "timestamp": "",
                    }
                )

        return normalized

    # If neither string nor list, return empty list
    return []


async def execute_call(
    agent_id: str,
    task_id: str,
    data: dict,
    instructions: str = None,
    model_config: BaseModelConfig = None,
    callback: BaseCallback = None,
):
    """
    Execute a call using the appropriate provider (VAPI or LiveKit) based on input data.

    Args:
        agent_id: Agent identifier
        task_id: Task identifier
        data: Call data containing contact information or room details
        instructions: Optional instructions for the call
        model_config: Configuration for the model
        callback: Callback handler for streaming updates

    Returns:
        dict: Standardized response format compatible with existing API
    """
    from .providers import CallProviderFactory, CallResult

    try:
        print_log(f"Starting call execution - Task: {task_id}, Agent: {agent_id}")
        data = await execute_pre_call_workflow(task_id, data, agent_id)
        # Create the appropriate provider based on input data
        provider = CallProviderFactory.create_provider(data)
        provider_name = provider.get_provider_name()

        logger.info(f"Provider selected: {provider_name} for task {task_id}")

        # Execute the call using the selected provider
        logger.info(f"Executing call with {provider_name} provider for task {task_id}")
        try:
            data["thread_id"] = task_id
            data["user_id"] = (
                get_user_id(task_id) if not data.get("user_id") else data.get("user_id")
            )

            result: CallResult = await provider.execute_call(
                agent_id,
                task_id,
                data,
                instructions,
                model_config,
                callback,
                data.get("call_type", "outbound"),
            )

            # Normalize transcript format (VAPI returns string, we need list)
            if result.transcript:
                result.transcript = normalize_transcript(result.transcript)
                logger.info(
                    f"Normalized transcript for task {task_id}: {len(result.transcript)} entries"
                )

        except TypeError as te:
            # Catch TypeError from logging issues in pipecat/livekit libraries
            logger.error(
                f"Logging error in provider execution for task {task_id}: {str(te)}"
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            if "Logger.log()" in str(te) and "missing" in str(te):
                raise Exception(
                    f"Logging configuration error in {provider_name} provider: {str(te)}"
                )
            else:
                raise te

        # TODO - Process Post Call workflow to run tools after the process.
        task = {
            "task_id": task_id,
            "instructions": instructions,
            "input": data,
        }
        post_call_result = {}
        try:
            if result.status == "completed":
                t1 = time.time()
                post_call_result = await execute_post_call_workflow(
                    agent_id, model_config, result, task
                )
                t2 = time.time()
                print_log(
                    f"Call execution completed - Task: {task_id}, Status: {result.status}, Time taken {round(t2-t1, 4)}"
                )
        except Exception as ex:
            logger.error(f"Error in post call workflow for task {task_id}: {str(ex)}")
            post_call_result = {}
        try:
            if result.status == "completed":
                logger.info(f"Updating profile after call for task {task_id}")
                await update_profile_by_task_id(task_id)
                logger.info(f"Profile updated successfully for task {task_id}")
        except Exception as profile_error:
            logger.error(
                f"Failed to update profile for task {task_id}: {str(profile_error)}"
            )
        # Convert CallResult to the expected response format
        response = {"status": result.status}

        # Build the output data
        output = {
            "transcript": result.transcript or [],
            "data": result.data or {},
            "recording": result.recording_url or "",
        }

        # Add error if present
        if result.error:
            output["error"] = result.error

        # Add notes if present
        if result.notes:
            output["notes"] = result.notes

        # Add call summary and status if present (for collection agents)
        if result.call_summary:
            output["call_summary"] = result.call_summary
        if result.call_status:
            output["call_status"] = result.call_status
        if result.status_update:
            output["status_update"] = result.status_update

        # Build new_output for backward compatibility
        logger.debug(f"Building response data for task {task_id}")
        new_output = {}
        try:
            cost = (
                float(result.data.get("cost", 0.0))
                + (float(result.data.get("cost", 0.0)) * 5) / 100
            )
            logger.debug(f"Calculated cost: {cost} for task {task_id}")

            new_output = {
                "call_id": result.call_id,
                "customer": result.customer,
                "contact_number": result.contact_number,
                "call_end_reason": result.call_end_reason,
                "recording_url": result.recording_url,
                "transcript": result.transcript,
                "start_time": result.call_start,
                "end_time": result.call_end,
                "assistant_number": result.assistant_number,
                "call_summary": result.call_summary,
                "duration": result.duration,
                "cost": cost,
                "post_call_data": post_call_result,
                "call_type": result.data.get("type", ""),
                "metadata": {
                    "cost": cost,
                    "type": result.data.get("type", "outboundPhoneCall"),
                    "usage": result.data.get("usage", {}),
                    # "messages":result.data.get('messages',None),
                },
            }

            logger.debug(f"Response data built successfully for task {task_id}")
            if result.status == "failed":
                new_output = {}

            if result.error:
                new_output["error"] = result.error
            if result.notes:
                new_output["notes"] = result.notes
            if result.call_summary:
                new_output["call_summary"] = result.call_summary
            if result.call_status:
                new_output["call_status"] = result.call_status
            if result.status_update:
                new_output["status_update"] = result.status_update

        except Exception as e:
            raise Exception(f"Error executing call response: {str(e)}")
            # Fallback for backward compatibility
            logger.error(f"Error formatting response for task {task_id}: {str(e)}")
            response["status"] = "failed"
            response["data"] = {
                "call_id": result.call_id,
                "customer": result.customer,
                "error": f"Failed to format response: {str(e)}",
            }
            return response

        response["data"] = new_output
        logger.info(
            f"Final response prepared for task {task_id} with status: {response['status']} \n\n response : {response}"
        )

        return response

    except ValueError as e:
        raise Exception(f"Error executing call ValueError: {str(e)}")
        # Provider selection failed
        logger.error(f"Provider selection failed for task {task_id}: {str(e)}")
        return {
            "status": "failed",
            "data": {"transcript": [], "error": str(e), "data": {}},
        }
    except Exception as e:
        raise Exception(f"Error executing call Outer Exception: {str(e)}")
        # Unexpected error
        logger.error(f"Unexpected error for task {task_id}: {str(e)}")
        return {
            "status": "failed",
            "data": {
                "transcript": [],
                "error": f"Unexpected error during call execution: {str(e)}",
                "data": {},
            },
        }


async def execute_post_call_workflow(
    agent_id,
    model_config,
    result,
    task,
    update_data=False,
    user_state: UserState = None,
):
    from super_services.db.services.models.task import TaskModel

    # Create process-local LM instance early to avoid threading issues
    lm = get_dspy_lm()

    post_call_result = {}
    task_id = task.get("task_id")

    call_end_time = (
        result.call_end
        if not isinstance(result, dict)
        else result.get("call_end") or None
    )
    transcript = (
        result.transcript
        if not isinstance(result, dict)
        else result.get("transcript", []) or []
    )
    recording_url = (
        result.recording_url
        if not isinstance(result, dict)
        else result.get("recording_url") or None
    )

    # Extract thread_id from recording_url filename if available
    thread_id = None
    # if recording_url:
    #     import os
    #     filename = os.path.basename(recording_url)
    #     # Extract thread_id from filename format: {thread_id}_{timestamp}.wav
    #     thread_id = filename.split('_')[0] if '_' in filename else None

    try:
        logger.info(f"Post call workflow started {task_id}")
        config = model_config.get_config(agent_id)

        data = task.get("input", {})

        # Extract turn_metrics from result.data if available (set by observer in pipecat_handler)
        turn_metrics = None
        if hasattr(result, "data") and isinstance(result.data, dict):
            turn_metrics = result.data.get("turn_metrics", None)
            if turn_metrics:
                logger.info(
                    f"Found turn_metrics in result.data: {len(turn_metrics)} turns"
                )

        post_call_input_data = {
            "task_id": task_id,
            "instructions": task.get("instructions", ""),
            "input_data": data,
            "output": result,
            "call_end_time": call_end_time,
            "thread_id": thread_id,
            "recording_url": recording_url,
            "turn_metrics": turn_metrics,  # Per-turn cost and latency metrics from observer
        }
        workflow_handler = PostCallWorkflow(
            user_state=user_state,
            model_config=config,
            transcript=transcript,
            token=data.get("token", None),
            document_id=data.get("document_id", None),
            data=post_call_input_data,
            lm=lm,
        )
        post_call_result = await workflow_handler.execute()
        logger.info(
            f"Post call workflow processed for task {task_id}, result: {post_call_result}"
        )

    except Exception as e:
        print_log(f"Exception occured while creating post call data {e}")
        post_call_result = {}
        raise e

    if update_data and post_call_result:
        print_log(f"Updating profile after post call for task {task_id}")
        TaskModel._get_collection().update_one(
            {"task_id": task_id},
            {"$set": {"output.post_call_data": post_call_result}},
        )
    await update_profile_by_task_id(task_id)
    return post_call_result


async def execute_pre_call_workflow(task_id, data, agent_id):
    executor = PreCallWorkFlow(
        task_id=task_id,
        data=data,
        agent_id=agent_id,
    )

    pre_call_result = executor.execute()

    if pre_call_result:
        data["pre_call_result"] = pre_call_result

    return data
