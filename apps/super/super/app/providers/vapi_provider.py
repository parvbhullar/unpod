import os

import httpx
import requests
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from super.app.call_utils import fetch_with_manual_retry
from super.core.logging.logging import print_log
from super.core.voice.providers.base import CallProvider, CallResult
from dateutil import parser
from super.core.callback.base import BaseCallback
from super.core.configuration import BaseModelConfig


class VapiProvider(CallProvider):
    """VAPI call provider implementation"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.BULK_UPDATE_API = "https://api.asksupplyai.com/bulk_update/"

    def get_provider_name(self) -> str:
        return "vapi"

    def supports_async(self) -> bool:
        return True  # We'll wrap sync operations in async

    def validate_data(self, data: Dict[str, Any]) -> bool:
        return "contact_number" in data

    def _is_retryable_error(self, error_message: str) -> bool:
        """
        Check if an error is retryable.

        Args:
            error_message: The error message to check

        Returns:
            True if the error is retryable, False otherwise
        """
        retryable_errors = [
            "sip-480-temporarily-unavailable",  # SIP 480 error
            "call.in-progress.error-sip-outbound-call-failed-to-connect",  # SIP 480 error
            "rate-limit",  # Rate limit errors
            "ratelimit",  # Alternative rate limit format
            "too-many-requests",  # HTTP 429
            "temporarily-unavailable",  # General temporary unavailability
            "providerfault",  # Provider fault errors
        ]

        error_lower = error_message.lower() if error_message else ""
        return any(
            retryable_error in error_lower for retryable_error in retryable_errors
        )

    async def check_current_calls(self):
        current_time = datetime.utcnow() - timedelta(minutes=5)
        start_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_time = (current_time + timedelta(minutes=5)).strftime(
            "%Y-%m-%dT%H:%M:%S.000Z"
        )
        analytics_query = {
            "queries": [
                {
                    "table": "subscription",
                    "name": "active_calls_concurrency",
                    "operations": [{"operation": "history", "column": "concurrency"}],
                    "timeRange": {
                        "step": "second",
                        "start": start_time,
                        "end": end_time,
                    },
                }
            ]
        }
        auth_token = os.getenv("VAPI_API_KEY")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        url = "https://api.vapi.ai/analytics"
        client = httpx.Client()
        response = fetch_with_manual_retry(
            client,
            "POST",
            url,
            headers=headers,
            json=analytics_query,
            timeout=10,
            max_retries=5,
            backoff_factor=2,
        )
        if response.status_code == 201:
            data = response.json()
            print_log("active_calls_concurrency", data)
            result = data[0].get("result", [])
            if result:
                return result[-1].get("historyConcurrency", 0)
            else:
                return 0
        else:
            print_log(
                f"Failed to fetch active calls concurrency: {response.status_code} - {response.text}"
            )
            return False

    async def execute_call(
        self,
        agent_id: str,
        task_id: str,
        data: Dict[str, Any],
        instructions: Optional[str] = None,
        model_config: BaseModelConfig = None,
        callback: BaseCallback = None,
        call_type: str = "outbound",
    ) -> CallResult:
        """
        Execute a VAPI call with retry logic for specific errors.

        Retries the call after 15 seconds if encountering:
        - SIP 480 errors (temporarily unavailable)
        - Rate limit errors
        - Provider fault errors
        """

        # Set objective
        if instructions:
            data["objective"] = instructions
        else:
            data["objective"] = "Say Hi This your voice assistant from Unpod"

        if not self.validate_data(data):
            return CallResult(
                status="failed", error="No Contact Number Found", transcript=[]
            )

        contact_number = data["contact_number"]
        contact_name = data.get("contact_name") or data.get("name") or "User"

        # Get retry configuration from environment
        max_call_retries = int(
            os.getenv("VAPI_CALL_MAX_RETRIES", 1)
        )  # Default: 1 retry
        retry_delay = int(os.getenv("VAPI_CALL_RETRY_DELAY", 15))  # Default: 15 seconds

        print_log(f"Starting call execution for {agent_id} - Task: {task_id}")

        # Check and wait for available channel slots (max 15 concurrent calls)
        max_concurrent_calls = int(os.getenv("VAPI_MAX_CONCURRENT_CALLS", 10))
        channel_wait_interval = int(os.getenv("VAPI_CHANNEL_WAIT_INTERVAL", 10))

        while True:
            try:
                current_calls = await self.check_current_calls()
            except Exception as ex:
                print_log(f"Error checking current calls: {ex}")
                current_calls = False
            if current_calls is False:
                print_log(f"Failed to fetch current calls, retrying for task {task_id}")
                await asyncio.sleep(2)
                continue  # Retry fetching current calls
            if current_calls < max_concurrent_calls:
                print_log(
                    f"Channel available ({current_calls}/{max_concurrent_calls}), starting call for task {task_id}"
                )
                break
            print_log(
                f"Waiting for channel slot ({current_calls}/{max_concurrent_calls}) for task {task_id}"
            )
            await asyncio.sleep(channel_wait_interval)

        last_result = None
        for attempt in range(max_call_retries + 1):  # +1 for initial attempt
            try:
                if attempt > 0:
                    print_log(
                        f"Retrying call for task {task_id} (attempt {attempt + 1}/{max_call_retries + 1}) "
                        f"after {retry_delay}s delay due to: {last_result.error if last_result else 'unknown error'}",
                        "vapi_call_retry",
                    )
                    await asyncio.sleep(retry_delay)

                # Start the call
                call_response = await self._start_vapi_call(agent_id, data)

                if isinstance(call_response, str):
                    return CallResult(
                        status="failed",
                        error=call_response,
                        transcript=[],
                        data={
                            "call_type": "outbound",
                            "cost": 0,
                            "type": "outboundPhoneCall",
                            "error": call_response,
                        },
                    )

                call_id = call_response["response"]["id"]
                headers = call_response["headers"]

                # Wait for call to end before returning (frees up channel tracking)
                # print_log(f"Call started with call_id {call_id}, waiting for call to end for task {task_id}")
                # await self._check_call_ended(call_id, headers)
                # print_log(f"Call ended for call_id {call_id}, task {task_id}")
                # if call_id:
                #     await self.add_call_context(data=data, call_response=call_response)

                return CallResult(
                    status="in_progress",
                    call_id=call_id,
                    customer=contact_name,
                    contact_number=contact_number,
                    data={
                        "call_type": "outbound",
                        "cost": 0,
                        "type": "outboundPhoneCall",
                    },
                )

            except Exception as e:
                print_log("Exception Occured during call execution ", str(e))

                if attempt == max_call_retries - 1:
                    return CallResult(
                        status="failed",
                        error=str(e),
                        transcript=[],
                        data={
                            "call_type": "outbound",
                            "cost": 0,
                            "type": "outboundPhoneCall",
                            "error": str(e),
                        },
                    )

    async def add_call_context(self, data, call_response):
        if not data.get("pre_call_result", {}) and data.get("pre_call_result", {}).get(
            "chat_context"
        ):
            print_log(f"no chat context for call")
            return

        try:
            headers = call_response["headers"]

            chat_context = data.get("pre_call_result", {}).get("chat_context", "")
            control_url = call_response["response"].get("artifactPlan", {}).get(
                "monitor", {}
            ).get("controlUrl") or call_response["response"].get("monitor", {}).get(
                "controlUrl"
            )

            payload = {
                "type": "add-message",
                "message": {
                    "role": "system",
                    "content": f"[Past Conversation With The User] \n\n {chat_context}",
                },
                "triggerResponseEnabled": True,
            }

            print_log(f" adding call context for call ")
            if control_url:
                for i in range(3):
                    asyncio.sleep(2)
                    try:
                        res = requests.post(control_url, json=payload, headers=headers,timeout=10)
                    except requests.Timeout:
                        print(f"timeout waiting for response retrying : {i+1}/3")
                        continue
                    if res.status_code == 200:
                        print_log("Successfully added control message and chat context")
                        return
                    print_log(
                        f"Failed to add control message retrying {i+1}/3 : \n {res.text}"
                    )
                print_log(f"Failed to add control message and chat context ")
                return

            print_log("no control url available", call_response)
        except Exception as e:
            print_log(str(e))
            return

    async def _start_vapi_call(self, agent_id: str, data: Dict[str, Any]):
        """Start a VAPI call (wrapped in async)"""
        # Import the existing start_vapi_call function
        from ..call_execution import start_vapi_call

        # Run in thread pool to make it async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, start_vapi_call, agent_id, data)

    async def _fetch_call_status_with_retry(
        self, call_id: str, headers: dict, max_retries: int = 3, retry_delay: int = 2
    ) -> tuple[Optional[dict], Optional[str]]:
        """
        Fetch call status from VAPI API with retry mechanism.

        Args:
            call_id: The call ID to fetch status for
            headers: HTTP headers for authentication
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Delay in seconds between retries (default: 2)

        Returns:
            Tuple of (call_data dict, phone_number string) or (None, None) if failed
        """
        loop = asyncio.get_event_loop()

        for attempt in range(max_retries):
            try:
                # Fetch call status
                status_response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(
                        f"https://api.vapi.ai/call/{call_id}", headers=headers
                    ),
                )

                if status_response.status_code == 200:
                    call_data = status_response.json()
                    # Fetch phone number
                    phone_number_id = call_data.get("phoneNumberId")
                    if phone_number_id:
                        try:
                            number_response = await loop.run_in_executor(
                                None,
                                lambda: requests.get(
                                    f"https://api.vapi.ai/phone-number/{phone_number_id}",
                                    headers=headers,
                                ),
                            )

                            if number_response.status_code == 200:
                                number = number_response.json().get("number", "")
                                return call_data, number
                        except Exception as e:
                            print_log(
                                f"Error fetching phone number (attempt {attempt + 1}/{max_retries}): {str(e)}"
                            )

                    # Return call data even if phone number fetch failed
                    return call_data, ""

                elif status_response.status_code >= 500:
                    # Server error - retry
                    print(
                        f"Server error {status_response.status_code} (attempt {attempt + 1}/{max_retries})"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                else:
                    # Client error - don't retry
                    print(f"Client error {status_response.status_code}, not retrying")
                    return None, None

            except Exception as e:
                print(
                    f"Exception fetching call status (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue

        return None, None

    def _parse_timestamps(
        self, start: Optional[str], end: Optional[str]
    ) -> tuple[str, str]:
        """
        Parse ISO timestamps to SQL format.

        Args:
            start: ISO format start timestamp
            end: ISO format end timestamp

        Returns:
            Tuple of (start_time_sql, end_time_sql)
        """
        start_time_sql = "NULL"
        end_time_sql = "NULL"

        try:
            if start:
                start_time_sql = (
                    f"{parser.isoparse(start).strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except Exception as e:
            print(f"Error parsing start time: {str(e)}")

        try:
            if end:
                end_time_sql = f"{parser.isoparse(end).strftime('%Y-%m-%d %H:%M:%S')}"
        except Exception as e:
            print(f"Error parsing end time: {str(e)}")

        return start_time_sql, end_time_sql

    def _calculate_duration(self, start: Optional[str], end: Optional[str]) -> any:
        """
        Calculate call duration from start and end timestamps.

        Args:
            start: ISO format start timestamp
            end: ISO format end timestamp

        Returns:
            Duration in seconds or 'NULL' if calculation fails
        """
        try:
            if start and end:
                return (parser.parse(end) - parser.parse(start)).total_seconds()
        except Exception as e:
            print(f"Error calculating duration: {str(e)}")

        return "NULL"

    def _build_call_result(
        self,
        status: str,
        call_id: str,
        call_data: dict,
        contact_name: str,
        contact_number: str,
        phone_number: str,
        start_time_sql: str,
        end_time_sql: str,
        error: Optional[str] = None,
    ) -> CallResult:
        """
        Build a CallResult object from call data.

        Args:
            status: Call status ("completed" or "failed")
            call_id: The call ID
            call_data: Raw call data from VAPI API
            contact_name: Customer name
            contact_number: Customer phone number
            phone_number: Assistant phone number
            start_time_sql: Formatted start time
            end_time_sql: Formatted end time
            error: Optional error message

        Returns:
            CallResult object
        """
        start = call_data.get("startedAt")
        end = call_data.get("endedAt")

        data_with_flat_fields = {
            **call_data,
            "call_type": "outbound",
            "cost": call_data.get("cost", 0) if status == "completed" else 0,
            "type": "outboundPhoneCall",
        }

        if error:
            data_with_flat_fields["error"] = error

        # print_log("creating call result data for call ",call_data)

        # print_log(call_data.get("artifact", {}).get('recording',{}).get("mono",{}).get("assistantUrl",""))
        return CallResult(
            status=status,
            call_id=call_id,
            customer=contact_name,
            contact_number=contact_number,
            call_end_reason=call_data.get("endedReason"),
            recording_url=call_data.get("recordingUrl", ""),
            transcript=call_data.get("transcript", []),
            call_start=start_time_sql,
            call_end=end_time_sql,
            assistant_number=phone_number,
            duration=self._calculate_duration(start, end),
            call_summary=call_data.get("summary", ""),
            error=error,
            data=data_with_flat_fields,
        )

    async def _poll_call_status(
        self, call_id: str, headers: dict, contact_name: str, contact_number: str
    ) -> CallResult:
        """Poll call status until completion with retry mechanism for final status"""
        call_log = []
        poll_interval = int(
            os.getenv("CALL_STATUS_POLL_INTERVAL", 20)
        )  # Default: 5 seconds

        while True:
            try:
                # Fetch call status with retry mechanism
                call_data, phone_number = await self._fetch_call_status_with_retry(
                    call_id, headers, max_retries=3, retry_delay=2
                )

                if call_data is None:
                    # Failed to fetch status after retries
                    return CallResult(
                        status="failed",
                        call_id=call_id,
                        customer=contact_name,
                        contact_number=contact_number,
                        error="Failed to fetch call status after multiple retries",
                        transcript=[],
                        data={
                            "call_type": "outbound",
                            "cost": 0,
                            "type": "outboundPhoneCall",
                            "error": "Failed to fetch call status",
                        },
                    )

                call_status = call_data.get("status")
                call_log.append(call_status)

                # Parse timestamps
                start = call_data.get("startedAt")
                end = call_data.get("endedAt")
                start_time_sql, end_time_sql = self._parse_timestamps(start, end)

                # Handle completed call (ended after in-progress)

                if (
                    call_status == "ended"
                    and len(call_log) > 1
                    and call_log[call_log.index("ended") - 1] == "in-progress"
                    and call_data.get("endedReason")
                    != "call.in-progress.sip-completed-call"
                ):
                    # print(call_data)
                    return self._build_call_result(
                        status="completed",
                        call_id=call_id,
                        call_data=call_data,
                        contact_name=contact_name,
                        contact_number=contact_number,
                        phone_number=phone_number,
                        start_time_sql=start_time_sql,
                        end_time_sql=end_time_sql,
                    )

                # Handle failed call (ended during ringing)
                elif (
                    call_status == "ended"
                    and len(call_log) > 1
                    and call_log[call_log.index("ended") - 1] == "ringing"
                    and call_data.get("endedReason")
                    != "call.in-progress.sip-completed-call"
                ):
                    return self._build_call_result(
                        status="failed",
                        call_id=call_id,
                        call_data=call_data,
                        contact_name=contact_name,
                        contact_number=contact_number,
                        phone_number=phone_number,
                        start_time_sql=start_time_sql,
                        end_time_sql=end_time_sql,
                        error=call_data.get(
                            "endedReason", "Call failed during ringing"
                        ),
                    )

                # Continue polling for in-progress or queued calls
                elif call_status in ["in-progress", "queued", "ringing"]:
                    await asyncio.sleep(poll_interval)
                    continue

                # Handle unexpected end
                elif (
                    call_status == "ended"
                    and call_data.get("endedReason")
                    != "call.in-progress.sip-completed-call"
                ):
                    return self._build_call_result(
                        status="failed",
                        call_id=call_id,
                        call_data=call_data,
                        contact_name=contact_name,
                        contact_number=contact_number,
                        phone_number=phone_number,
                        start_time_sql=start_time_sql,
                        end_time_sql=end_time_sql,
                        error="Call Ended Unexpectedly",
                    )

                # Unknown status - continue polling
                else:
                    await asyncio.sleep(poll_interval)
                    continue

            except Exception as e:
                print(f"Error in poll loop: {str(e)}")
                await asyncio.sleep(10)

    async def _check_call_ended(self, call_id: str, headers: dict) -> CallResult:
        """Poll call status until completion with retry mechanism for final status"""
        poll_interval = int(os.getenv("CALL_STATUS_POLL_INTERVAL", 5))

        while True:
            try:
                # Fetch call status with retry mechanism
                call_data, phone_number = await self._fetch_call_status_with_retry(
                    call_id, headers, max_retries=3, retry_delay=2
                )
                call_status = call_data.get("status")
                print_log("call_id --> ", call_id, "call_status --> ", call_status)
                if call_status == "ended":
                    return True
                else:
                    await asyncio.sleep(poll_interval)
                    continue
            except Exception as ex:
                print(f"Error in poll loop: {str(ex)}")
                await asyncio.sleep(10)

    async def _process_special_agents(
        self, agent_id: str, result: CallResult, data: Dict[str, Any]
    ) -> CallResult:
        """Process special agent types with custom logic"""

        # Ninja Cart Agent
        if "ninja-cart-agent" in agent_id and result.transcript:
            try:
                from ..invoice import SupplyOrderExtractor

                extractor = SupplyOrderExtractor()
                extraction_result = extractor(
                    name=result.customer, transcript=result.transcript
                )
                result.notes = {
                    "customer_name": extraction_result.customer_name,
                    "order_details": str(extraction_result.order_details),
                }
            except Exception:
                result.notes = {
                    "customer_name": result.customer,
                    "order_details": result.call_end_reason,
                }

        # Ninja Cart Collection Agent
        if (
            "ninjacart-collection-agent" in agent_id
            and result.transcript
            and result.data
        ):
            try:
                result.call_summary = result.data.get("summary")
                result.call_status = json.loads(
                    result.data.get("analysis", {}).get("successEvaluation", "{}")
                )

                token = data.get("token", "O33EUEE3UVQ2KJQFN30Z7U6U")
                url = f"{self.BULK_UPDATE_API}{token}"
                label = str(result.call_status.get("Rcode", "")).strip()

                payload = [
                    {
                        "document_id": data["document_id"],
                        "action": "edit",
                        "data": {"labels": [label], "summary": result.call_summary},
                    }
                ]

                # Make API request in thread pool
                loop = asyncio.get_event_loop()
                urlresponse = await loop.run_in_executor(
                    None, lambda: requests.post(url, json=payload)
                )

                if urlresponse.status_code == 200:
                    result.status_update = "Call Status Updated"
                else:
                    result.status_update = "Call Status Not Updated"

            except Exception as e:
                result.status_update = f"Call Status Not Updated because {str(e)}"

        return result

    async def update_call_data(self, task):
        auth_token = os.getenv("VAPI_API_KEY")
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        call_id, contact_name, contact_number = (
            task.output.get("call_id", None),
            task.input.get("name", ""),
            task.input.get("contact_number", None),
        )
        result = await self._poll_call_status(
            call_id, headers, contact_name, contact_number
        )

        new_output = {}
        try:
            cost = (
                float(result.data.get("cost", 0.0))
                + (float(result.data.get("cost", 0.0)) * 5) / 100
            )
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
                "metadata": {
                    "cost": cost,
                    "type": result.data.get("type", "outboundPhoneCall"),
                    "usage": result.data.get("usage", {}),
                },
            }

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
            # raise Exception(f"Error executing call response: {str(e)}")
            response = task.output or {}
            response["status"] = "failed"
            response["data"] = {
                "call_id": result.call_id,
                "customer": result.customer,
                "error": f"Failed to format response: {str(e)}",
            }
            return response

        return new_output
