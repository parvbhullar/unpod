"""
Calls Sync Cron Job - Syncs inbound and outbound calls from VAPI.

This cron job runs every 5 minutes and:
1. Fetches recent calls (inbound + outbound) from VAPI API
2. Matches calls to existing tasks or creates new tasks for inbound calls
3. Updates recording URLs from S3 or provider API
4. Executes post-call workflows
5. Triggers webhooks if configured
6. Recovers failed/pending runs
"""

import asyncio
import json
import os
import time
import traceback
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

from super_services.db.services.models.task import (
    RunModel,
    TaskExecutionLogModel,
    TaskModel,
)
from super_services.db.services.schemas.task import TaskStatusEnum
from super_services.voice.models.config import ModelConfig
from super_services.libs.core.db import executeQuery


class CallsSyncService:
    """
    Service class for syncing calls from VAPI provider.

    Handles:
    - Fetching recent calls (inbound + outbound)
    - Task matching and creation
    - Recording URL retrieval from S3 or provider
    - Post-call workflow execution
    - Webhook execution
    - Failed run recovery
    """

    def __init__(self) -> None:
        """Initialize the CallsSyncService with environment configuration."""
        self.auth_token = os.getenv("VAPI_AUTH_TOKEN")
        self.base_url = os.getenv("VAPI_BASE", "https://api.vapi.ai")
        self.state_file = os.getenv(
            "INBOUND_CALLS_EXECUTION_PATH", "/tmp/calls_sync_state.json"
        )
        self.aws_bucket = os.getenv("AWS_STORAGE_BUCKET_NAME", "cdr-storage-recs")
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
        self.vapi_s3_prefix = os.getenv("VAPI_S3_FILE_PATH", "")
        self.sbc_s3_prefix = os.getenv("S3_FILE_PATH", "")
        self._s3_client: Optional[boto3.client] = None
        self._phone_number_cache: dict[str, str] = {}  # Cache for phone numbers
        self._failed_phone_ids: set[str] = set()  # Track failed phone number IDs

    @property
    def s3_client(self) -> boto3.client:
        """Lazy-load S3 client."""
        if self._s3_client is None:
            self._s3_client = boto3.client("s3")
        return self._s3_client

    def get_auth_headers(self) -> dict:
        """Get authentication headers for VAPI API."""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def convert_iso_to_mysql(dt_str: str) -> Optional[str]:
        """Convert ISO 8601 timestamp to MySQL datetime format."""
        if not dt_str:
            return None
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def get_last_execution_time(self) -> Optional[str]:
        """Get last execution time from state file."""
        if not self.state_file:
            return None

        if not os.path.exists(self.state_file):
            with open(self.state_file, "w") as f:
                json.dump({"last_run": None}, f)
            return None

        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                return data.get("last_run")
        except (json.JSONDecodeError, KeyError, ValueError):
            with open(self.state_file, "w") as f:
                json.dump({"last_run": None}, f)
            return None

    def update_last_execution_time(self) -> str:
        """Update last execution time in state file."""
        print(f"{self.state_file} updating cron run time")
        utc_now = datetime.now(timezone.utc)
        iso_z_format = utc_now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

        if self.state_file:
            with open(self.state_file, "w") as f:
                json.dump({"last_run": iso_z_format}, f)

        return iso_z_format

    def get_space_token(self, space_id: str) -> Optional[dict]:
        """Get space token from database."""
        query = """
        SELECT token FROM space_space where id=%(space_id)s;
        """
        params = {"space_id": space_id}
        token = executeQuery(query, params)
        return token

    def get_space_for_user(self, user_id: str) -> Optional[str]:
        """Get a space_id for a user from their organization."""
        if not user_id:
            return None

        query = """
        SELECT ss.id as space_id
        FROM space_space ss
        JOIN space_spaceorganization so ON ss.space_organization_id = so.id
        JOIN space_organizationmemberroles som ON so.id = som.organization_id
        WHERE som.user_id = %(user_id)s
        LIMIT 1;
        """
        params = {"user_id": user_id}
        try:
            result = executeQuery(query, params)
            space_id = result.get("space_id") if result else None
            # Convert to string if needed (MySQL may return int)
            return str(space_id) if space_id is not None else None
        except Exception as e:
            print(f"Error getting space for user {user_id}: {e}")
            return None

    def get_agent_number(self, phone_number_id: str) -> str:
        """Get agent phone number from VAPI API with caching."""
        if not phone_number_id:
            return ""

        # Check cache first
        if phone_number_id in self._phone_number_cache:
            return self._phone_number_cache[phone_number_id]

        # Skip if we already know this ID fails
        if phone_number_id in self._failed_phone_ids:
            return ""

        url = f"{self.base_url}/phone-number/{phone_number_id}"
        try:
            data = requests.get(url, headers=self.get_auth_headers(), timeout=30)
            data.raise_for_status()
            number = data.json().get("number", "")
            self._phone_number_cache[phone_number_id] = number
            return number
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                # Phone number not found - cache the failure to avoid repeated calls
                self._failed_phone_ids.add(phone_number_id)
                print(f"Phone number {phone_number_id} not found in VAPI (404)")
            else:
                print(f"Error fetching agent number: {e}")
            return ""
        except Exception as e:
            print(f"Error fetching agent number: {e}")
            return ""

    def get_pilot_data(self, assistant_ids: list) -> dict:
        """Get pilot data for given assistant IDs."""
        data = {}

        query = """
        SELECT
        handle,
        space_id,
        created_by,
        config
        FROM core_components_pilot
        WHERE config->'voice'->>'vapi_agent_id' = %(assistant_id)s Limit 1;
        """

        print(f"fetching pilot data for {len(assistant_ids)} agents")

        for assistant_id in assistant_ids:
            if not assistant_id:
                continue

            params = {"assistant_id": assistant_id}
            res = executeQuery(query, params)
            response = res if res else {}
            handle = res.get("handle") if res else None

            if handle:
                df_params = {"agent_id": handle}
                query2 = """
                    SELECT dfv.values
                    FROM dynamic_form_values dfv
                    JOIN dynamic_forms df
                    ON dfv.form_id = df.id
                    WHERE dfv.parent_id = %(agent_id)s
                    AND df.slug = 'webhook-integration';
                """
                ws = executeQuery(query2, df_params)
                if ws:
                    response["webhook"] = ws.get("values", {})

            data[assistant_id] = response

        return data

    def fetch_data_with_retry(
        self, url: str, params: dict = None, max_retries: int = 3
    ) -> Optional[dict]:
        """Fetch data from URL with retry logic."""

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = requests.get(
                    url,
                    headers=self.get_auth_headers(),
                    params=params,
                    timeout=60,
                )
                response.raise_for_status()

                data = response.json()
                time_taken = round(time.time() - start_time, 2)

                print(f"API call took {time_taken}s, attempt {attempt + 1}")

                if time_taken > 10:
                    print(f"⚠️ Slow API call ({time_taken}s): {response.request.url}")

                # Retry only if response is empty AND slow
                if not data and time_taken > 20 and attempt < max_retries:
                    print(f"Empty response after {time_taken}s, retrying...")
                    time.sleep(2**attempt)
                    continue

                return data

            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")

                if attempt == max_retries - 1:
                    print(f"❌ Max retries exceeded for {url}")
                    return None

                time.sleep(2**attempt)  # Exponential backoff

            except ValueError as e:
                # JSON decoding failed
                print(f"Invalid JSON response from {url}: {e}")
                return None

        return None

    def fetch_all_recent_calls(
        self,
        last_run_time: Optional[str] = None,
        call_type: Optional[str] = None,
        max_pages: int = 100,
        assistant_id: Optional[str] = None,
    ) -> list:
        """
        Fetch all calls from VAPI API updated after last_run_time with pagination.

        Uses timestamp-based pagination to fetch all records, handling up to 10K+ calls.

        Args:
            last_run_time: ISO 8601 timestamp (e.g., "2025-01-01T10:00:00Z")
            call_type: Optional filter - "inboundPhoneCall" or "outboundPhoneCall"
            max_pages: Maximum number of pages to fetch (safety limit, default 100)
            assistant_id: Optional filter by VAPI assistant ID

        Returns:
            List of all call objects from VAPI API
        """
        url = f"{self.base_url}/call"
        all_calls: list = []
        page_size = 100
        page_count = 0

        # Track the oldest updatedAt to paginate backwards
        current_upper_bound: Optional[str] = None

        while page_count < max_pages:
            params: dict = {"limit": page_size}

            # Filter by assistant_id if provided
            if assistant_id:
                params["assistantId"] = assistant_id

            # Filter by last_run_time (lower bound)
            if last_run_time:
                params["updatedAtGt"] = last_run_time

            # For pagination, use updatedAtLt to get older records
            if current_upper_bound:
                params["updatedAtLt"] = current_upper_bound

            try:
                print(f"Fetching calls page {page_count + 1} with params: {params}")
                calls = self.fetch_data_with_retry(url, params)
                if not calls:
                    # No more records
                    break

                all_calls.extend(calls)
                page_count += 1

                # If we got fewer than page_size, we've reached the end
                if len(calls) < page_size:
                    break

                # Get the oldest updatedAt for next pagination
                oldest_updated_at = min(
                    call.get("updatedAt", "") for call in calls if call.get("updatedAt")
                )
                if not oldest_updated_at or oldest_updated_at == current_upper_bound:
                    # No progress, stop to avoid infinite loop
                    break

                current_upper_bound = oldest_updated_at
                print(f"Fetched {len(calls)} calls, total so far: {len(all_calls)}")

            except Exception as e:
                print(f"Failed to fetch calls on page {page_count + 1}: {e}")
                break

        # Filter by call type if specified
        if call_type:
            all_calls = [c for c in all_calls if c.get("type") == call_type]

        # Remove duplicates based on call id (in case of overlap at boundaries)
        seen_ids: set = set()
        unique_calls: list = []
        for call in all_calls:
            call_id = call.get("id")
            if call_id and call_id not in seen_ids:
                seen_ids.add(call_id)
                unique_calls.append(call)

        print(f"Fetched total {len(unique_calls)} unique calls in {page_count} pages")
        return unique_calls

    def find_task_for_call(self, call_data: dict) -> Optional[dict]:
        """
        Find existing task for a call using multiple matching strategies.

        Matching priority:
        1. Match by call_id (output.call_id)
        2. Match by vapi_agent_id + number_id + contact_number (for pending/failed tasks)

        Args:
            call_data: Raw call data from VAPI API containing:
                - id: call_id
                - assistantId: vapi_agent_id
                - phoneNumberId: number_id
                - customer.number or destination.number: contact_number

        Returns:
            Task dict if found, None otherwise
        """
        call_id = call_data.get("id")

        # Strategy 1: Match by call_id
        if call_id:
            try:
                tasks = list(
                    TaskModel._get_collection().find(
                        {"output.call_id": call_id}, sort=[("modified", -1)]
                    )
                )
                if tasks:
                    return tasks[0]
            except Exception as e:
                print(f"Error finding task by call_id {call_id}: {e}")

        # Strategy 2: Match by vapi_agent_id + number_id + contact_number
        assistant_id = call_data.get("assistantId")
        phone_number_id = call_data.get("phoneNumberId")

        # Get contact number from customer or destination
        contact_number = call_data.get("customer", {}).get("number")
        if not contact_number:
            contact_number = call_data.get("destination", {}).get("number")

        if assistant_id and contact_number:
            try:
                # Build query for matching pending/in-progress/failed tasks
                query = {
                    "input.vapi_agent_id": assistant_id,
                    "input.contact_number": contact_number,
                    "status": {"$in": ["pending", "in_progress", "queued", "failed"]},
                }

                # Add number_id filter if available
                if phone_number_id:
                    query["input.number_id"] = phone_number_id

                tasks = list(
                    TaskModel._get_collection().find(query, sort=[("modified", -1)])
                )

                if tasks:
                    return tasks[0]

                # Fallback: Try without number_id (some tasks may not have it)
                if phone_number_id:
                    query_without_number = {
                        "input.vapi_agent_id": assistant_id,
                        "input.contact_number": contact_number,
                        "status": {
                            "$in": ["pending", "in_progress", "queued", "failed"]
                        },
                    }
                    tasks = list(
                        TaskModel._get_collection().find(
                            query_without_number, sort=[("modified", -1)]
                        )
                    )
                    if tasks:
                        return tasks[0]

            except Exception as e:
                print(f"Error finding task by agent+number: {e}")

        return None

    def find_task_by_call_id(self, call_id: str) -> Optional[dict]:
        """Find existing task by call_id in output field (legacy method)."""
        if not call_id:
            return None

        try:
            tasks = list(
                TaskModel._get_collection().find(
                    {"output.call_id": call_id}, sort=[("modified", -1)]
                )
            )
            return tasks[0] if tasks else None
        except Exception as e:
            print(f"Error finding task by call_id {call_id}: {e}")
            return None

    def update_task_output_from_call(self, task: dict, call_data: dict) -> dict:
        """
        Update task output with latest data from VAPI call API.

        Merges new data from call_data into task's output field without
        overwriting existing values unless they are empty/None.

        Args:
            task: Existing task dict
            call_data: Raw call data from VAPI API

        Returns:
            Updated task dict
        """
        output = task.get("output", {})
        updated = False

        # Build transcript from VAPI response
        transcript = None
        artifact = call_data.get("artifact", {})
        if artifact.get("messagesOpenAIFormatted"):
            transcript = artifact["messagesOpenAIFormatted"][1:]  # Skip system message
        elif call_data.get("transcript"):
            transcript = call_data["transcript"]

        # Fields to update from call_data (only if not already set)
        updates = {
            "call_id": call_data.get("id"),
            "call_end_reason": call_data.get("endedReason"),
            "call_summary": call_data.get("summary"),
            "transcript": transcript,
            "start_time": call_data.get("startedAt"),
            "end_time": call_data.get("endedAt"),
            "cost": call_data.get("cost"),
            "duration": call_data.get("duration"),
            "customer": call_data.get("customer", {}).get("name"),
            "contact_number": call_data.get("customer", {}).get("number"),
        }

        for key, value in updates.items():
            if value is not None and not output.get(key):
                output[key] = value
                updated = True

        # Update assistant_number if not set
        if not output.get("assistant_number"):
            phone_number_id = call_data.get("phoneNumberId")
            if phone_number_id:
                assistant_number = self.get_agent_number(phone_number_id)
                if assistant_number:
                    output["assistant_number"] = assistant_number
                    updated = True

        if updated:
            TaskModel.update_one({"task_id": task.get("task_id")}, {"output": output})
            task["output"] = output
            print(f"Updated task {task.get('task_id')} output from call data")

        return task

    def search_s3_recording(self, call_id: str) -> Optional[str]:
        """Search S3 for recording by call_id in high-quality bucket."""
        if not call_id:
            return None

        try:
            # Build prefix with call_id for efficient search
            prefix = (
                f"{self.vapi_s3_prefix}{call_id}" if self.vapi_s3_prefix else call_id
            )
            paginator = self.s3_client.get_paginator("list_objects_v2")

            for page in paginator.paginate(Bucket=self.aws_bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    if obj["Key"].endswith(".wav"):
                        url = f"https://{self.aws_bucket}.s3.{self.aws_region}.amazonaws.com/{obj['Key']}"
                        print(f"Found S3 recording for {call_id}: {url}")
                        return url

            return None
        except Exception as e:
            print(f"Error searching S3 for recording {call_id}: {e}")
            return None

    def search_sbc_recording(
        self,
        source_number: str,
        dest_number: str,
        call_time: Optional[datetime] = None,
    ) -> Optional[str]:
        """
        Search SBC S3 bucket for recording by phone numbers and time.

        File format: sbc_prefix/YYYY/YYYY-MM-DD-HH-MM-SS_+source_+dest_uuid.wav

        Args:
            source_number: Source phone number (last 10 digits used)
            dest_number: Destination phone number (last 10 digits used)
            call_time: Call time to build date-specific prefix

        Returns:
            Recording URL or None
        """
        if not dest_number or not call_time:
            return None

        # Normalize numbers to last 10 digits
        source_normalized = source_number[-10:] if source_number else ""
        dest_normalized = dest_number[-10:] if dest_number else ""

        # Strip timezone for comparison
        search_time = call_time.replace(tzinfo=None) if call_time.tzinfo else call_time

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            # Build date-specific prefix: sbc_prefix/YYYY/YYYY-MM-DD
            date_str = search_time.strftime("%Y-%m-%d")
            date_prefix = f"{self.sbc_s3_prefix}/{search_time.year}/{date_str}"

            for page in paginator.paginate(Bucket=self.aws_bucket, Prefix=date_prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if not key.endswith(".wav"):
                        continue

                    # Parse filename: sbc_prefix/YYYY/YYYY-MM-DD-HH-MM-SS_+source_+dest_uuid.wav
                    filename = key.split("/")[-1]
                    parts = filename.split("_")
                    if len(parts) < 3:
                        continue

                    raw_source = parts[1].lstrip("+").lstrip("0")[-10:]
                    raw_dest = parts[2].lstrip("+").lstrip("0")[-10:]

                    # Match by destination (and source if available)
                    if raw_dest != dest_normalized:
                        continue
                    if source_normalized and raw_source != source_normalized:
                        continue

                    # Check time proximity
                    try:
                        time_part = parts[0]
                        file_time = datetime.strptime(time_part, "%Y-%m-%d-%H-%M-%S")
                        diff = abs((file_time - search_time).total_seconds())
                        if diff > 300:  # 5 minutes threshold
                            continue
                    except (ValueError, IndexError):
                        continue

                    url = f"https://{self.aws_bucket}.s3.{self.aws_region}.amazonaws.com/{key}"
                    print(f"Found SBC recording: {url}")
                    return url

            return None
        except Exception as e:
            print(f"Error searching SBC S3 for recording: {e}")
            return None

    def fetch_sbc_recordings_for_period(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> dict[str, dict]:
        """
        Fetch all SBC recordings for a time period and build a mapping.

        File format: sbc_prefix/YYYY/YYYY-MM-DD-HH-MM-SS_+source_+dest_uuid.wav

        Args:
            start_time: Start of the period
            end_time: End of the period (defaults to now)

        Returns:
            Dict mapping recording key to metadata (source, dest, time, url)
        """
        if not end_time:
            end_time = datetime.now(timezone.utc)

        # Strip timezone for comparison
        start_naive = (
            start_time.replace(tzinfo=None) if start_time.tzinfo else start_time
        )
        end_naive = end_time.replace(tzinfo=None) if end_time.tzinfo else end_time

        recordings_map: dict[str, dict] = {}
        url_prefix = f"https://{self.aws_bucket}.s3.{self.aws_region}.amazonaws.com/"

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")

            # Build date-specific prefixes: sbc_prefix/YYYY/YYYY-MM-DD
            date_prefixes: list[str] = []
            current = start_naive.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_naive.replace(hour=23, minute=59, second=59)

            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                prefix = f"{self.sbc_s3_prefix}/{current.year}/{date_str}"
                date_prefixes.append(prefix)
                current += timedelta(days=1)

            print(f"Searching SBC recordings in {len(date_prefixes)} date prefix(es)")

            for date_prefix in date_prefixes:
                for page in paginator.paginate(
                    Bucket=self.aws_bucket, Prefix=date_prefix
                ):
                    for obj in page.get("Contents", []):
                        key = obj["Key"]

                        if not key.endswith(".wav"):
                            continue

                        # Parse filename: sbc_prefix/YYYY/YYYY-MM-DD-HH-MM-SS_+source_+dest_uuid.wav
                        filename = key.split("/")[-1]
                        parts = filename.split("_")
                        if len(parts) < 3:
                            continue

                        try:
                            time_part = parts[0]
                            file_time = datetime.strptime(
                                time_part, "%Y-%m-%d-%H-%M-%S"
                            )
                        except (ValueError, IndexError):
                            continue

                        # Filter by time range
                        if file_time < start_naive or file_time > end_naive:
                            continue

                        raw_source = parts[1].lstrip("+").lstrip("0")[-10:]
                        raw_dest = parts[2].lstrip("+").lstrip("0")[-10:]

                        recordings_map[key] = {
                            "url": url_prefix + key,
                            "source": raw_source,
                            "destination": raw_dest,
                            "time": file_time,
                        }

            print(f"Found {len(recordings_map)} SBC recordings in period")
            return recordings_map

        except Exception as e:
            print(f"Error fetching SBC recordings: {e}")
            return {}

    def match_task_to_sbc_recording(
        self,
        task: dict,
        recordings_map: dict[str, dict],
    ) -> Optional[str]:
        """
        Match a task to an SBC recording from the pre-fetched map.

        Args:
            task: Task dict with input/output containing phone numbers
            recordings_map: Pre-fetched recordings map

        Returns:
            Recording URL if matched, None otherwise
        """
        dest_number = task.get("input", {}).get("contact_number", "")
        if not dest_number:
            dest_number = task.get("input", {}).get("number", "")
        dest_normalized = dest_number[-10:] if dest_number else ""

        source_number = task.get("output", {}).get("assistant_number", "")
        source_normalized = source_number[-10:] if source_number else ""

        task_modified = task.get("modified")
        if task_modified and task_modified.tzinfo:
            task_modified = task_modified.replace(tzinfo=None)

        if not dest_normalized:
            return None

        best_match: Optional[dict] = None
        best_diff = float("inf")

        for recording in recordings_map.values():
            if recording["destination"] != dest_normalized:
                continue

            # Check source if available
            if source_normalized and recording["source"] != source_normalized:
                continue

            # Calculate time difference
            if task_modified:
                record_time = recording["time"]
                diff = abs((task_modified - record_time).total_seconds())
                if diff < best_diff:
                    best_diff = diff
                    best_match = recording

        # Return best match if within threshold (90 minutes for single, 5 min for multiple)
        if best_match and best_diff <= 5400:  # 90 minutes max
            return best_match["url"]

        return None

    async def get_recording_url(
        self,
        call_id: str,
        call_data: dict,
        task: Optional[dict],
        sbc_recordings_map: Optional[dict[str, dict]] = None,
    ) -> str:
        """
        Get recording URL - check task first, then call data, then S3, then SBC, then provider API.

        Args:
            call_id: The call ID
            call_data: Raw call data from VAPI API
            task: Existing task dict (if found)
            sbc_recordings_map: Pre-fetched SBC recordings map for batch matching

        Returns:
            Recording URL or empty string
        """
        # Check existing in task
        if task:
            existing_url = task.get("output", {}).get("recording_url")
            if existing_url:
                return existing_url

        # Check in call_data from API
        recording_url = call_data.get("recordingUrl", "")
        if recording_url:
            return recording_url

        # Check S3 in High quality recordings (VAPI bucket)
        s3_url = self.search_s3_recording(call_id)
        if s3_url:
            return s3_url

        # Fallback to SBC recordings
        if task and sbc_recordings_map:
            sbc_url = self.match_task_to_sbc_recording(task, sbc_recordings_map)
            if sbc_url:
                return sbc_url
        elif task:
            # Search SBC directly if no pre-fetched map
            dest_number = call_data.get("customer", {}).get("number", "")
            source_number = self.get_agent_number(call_data.get("phoneNumberId", ""))
            call_time = None
            if call_data.get("startedAt"):
                try:
                    call_time = datetime.fromisoformat(
                        call_data["startedAt"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
            sbc_url = self.search_sbc_recording(source_number, dest_number, call_time)
            if sbc_url:
                return sbc_url

        # Fallback to provider API (re-fetch call details)
        try:
            from super.app.providers.vapi_provider import VapiProvider

            provider = VapiProvider()
            call_response, _ = await provider._fetch_call_status_with_retry(
                call_id, self.get_auth_headers()
            )
            if call_response:
                return call_response.get("recordingUrl", "")
        except Exception as e:
            print(f"Error fetching recording from provider for {call_id}: {e}")

        return ""

    def create_task_for_call(self, call_data: dict, pilot_data: dict) -> Optional[dict]:
        """
        Create task for a call, reusing space and run from last agent task.

        Args:
            call_data: Raw call data from VAPI API
            pilot_data: Dict mapping assistant_id to pilot info

        Returns:
            Created task dict or None
        """
        assistant_id = call_data.get("assistantId")
        call_id = call_data.get("id")
        call_type = call_data.get("type", "inboundPhoneCall")

        if not assistant_id or not call_id:
            return None

        # Get pilot info
        pilot = pilot_data.get(assistant_id, {})
        if not pilot or not pilot.get("handle"):
            print(f"No pilot found for assistant {assistant_id}")
            return None

        handle = pilot.get("handle", "")
        created_by = pilot.get("created_by")

        # Find last executed task by this agent to get space_id and run_id
        last_task = None
        try:
            tasks = list(
                TaskModel._get_collection()
                .find(
                    {"assignee": handle, "execution_type": "call"},
                    sort=[("modified", -1)],
                )
                .limit(1)
            )
            last_task = tasks[0] if tasks else None
        except Exception as e:
            print(f"Error finding last task for agent {handle}: {e}")

        if last_task:
            # Reuse space_id and run_id from last task
            space_id = last_task.get("space_id")
            run_id = last_task.get("run_id")
            space_token = last_task.get("input", {}).get("token", "")
            print(f"Reusing space={space_id} run={run_id} from last agent task")
        else:
            # Fallback: Get space from pilot or user's organization
            space_id = pilot.get("space_id")

            if not space_id and created_by:
                space_id = self.get_space_for_user(created_by)
                if space_id:
                    print(f"Using fallback space {space_id} from user org")

            if not space_id:
                print(f"No space_id found for assistant {assistant_id}")
                return None

            # Get space token
            token_data = self.get_space_token(space_id)
            space_token = token_data.get("token", "") if token_data else ""

            # Create new run only if no last task found
            run_id = f"R{uuid.uuid1().hex}"
            try:
                RunModel.save_single_to_db(
                    {
                        "run_id": run_id,
                        "space_id": space_id,
                        "batch_count": 1,
                        "collection_ref": "",
                        "run_mode": "dev",
                        "thread_id": "",
                        "owner_org_id": "",
                        "status": TaskStatusEnum.completed,
                        "user": "",
                    }
                )
                print(f"Created new run {run_id} for agent {handle}")
            except Exception as e:
                print(f"Error creating run for call {call_id}: {e}")
                return None

        # Build transcript from VAPI response
        transcript = []
        artifact = call_data.get("artifact", {})
        if artifact.get("messagesOpenAIFormatted"):
            transcript = artifact["messagesOpenAIFormatted"][1:]  # Skip system message
        elif call_data.get("transcript"):
            transcript = call_data["transcript"]

        # Determine call type string
        call_type_str = "inbound" if "inbound" in call_type.lower() else "outbound"

        # Create task
        task_id = f"T{uuid.uuid1().hex}"
        task_data = {
            "task_id": task_id,
            "space_id": space_id,
            "user": "",
            "run_id": run_id,
            "thread_id": "",
            "collection_ref": "",
            "task": {"objective": f"{call_type_str.capitalize()} call"},
            "assignee": handle,
            "status": TaskStatusEnum.completed,
            "execution_type": "call",
            "provider": "vapi",
            "retry_attempt": 0,
            "last_status_change": datetime.utcnow().isoformat(),
            "input": {
                "token": space_token,
                "vapi_agent_id": assistant_id,
                "quality": "high",
                "call_type": call_type_str,
            },
            "output": {
                "call_id": call_id,
                "customer": call_data.get("customer", {}).get("name", ""),
                "contact_number": call_data.get("customer", {}).get("number", ""),
                "call_end_reason": call_data.get("endedReason", ""),
                "recording_url": call_data.get("recordingUrl", ""),
                "transcript": transcript,
                "start_time": call_data.get("startedAt"),
                "end_time": call_data.get("endedAt"),
                "assistant_number": self.get_agent_number(
                    call_data.get("phoneNumberId", "")
                ),
                "call_summary": call_data.get("summary", ""),
                "cost": call_data.get("cost", 0),
                "call_type": call_type_str,
            },
        }

        try:
            TaskModel.save_single_to_db(task_data)
            print(f"Created task {task_id} for call {call_id}")
            return task_data
        except Exception as e:
            print(f"Error creating task for call {call_id}: {e}")
            return None

    async def execute_post_call_for_task(self, task: dict) -> Optional[dict]:
        """
        Execute post-call workflow for a task.

        Args:
            task: Task dict with output containing transcript

        Returns:
            Post-call workflow result or None
        """
        from super.app.call_execution import execute_post_call_workflow

        agent_id = task.get("assignee")
        task_dict = {
            "task_id": task.get("task_id"),
            "instructions": task.get("task", {}).get("objective", ""),
            "input": task.get("input", {}),
        }
        result = task.get("output", {})

        try:
            workflow_result = await execute_post_call_workflow(
                agent_id, ModelConfig(), result, task_dict
            )
            return workflow_result
        except Exception as e:
            print(f"Post-call workflow failed for task {task.get('task_id')}: {e}")
            traceback.print_exc()
            return None

    def execute_webhook_if_configured(self, task: dict, pilot: dict) -> Optional[dict]:
        """
        Execute webhook if configured for the pilot.

        Args:
            task: Task dict
            pilot: Pilot data dict with webhook config

        Returns:
            Execution log dict or None
        """
        webhook = pilot.get("webhook")

        if isinstance(webhook, str):
            try:
                webhook = json.loads(webhook)
            except json.JSONDecodeError:
                webhook = {}

        if not webhook or not webhook.get("enable_webhook"):
            return None

        url = webhook.get("webhook_url")
        if not url:
            return None

        # Build payload
        payload = {
            "task_id": task.get("task_id"),
            "space_id": task.get("space_id"),
            "run_id": task.get("run_id"),
            "assignee": task.get("assignee"),
            "status": task.get("status"),
            "execution_type": task.get("execution_type"),
            "output": task.get("output"),
        }

        # Execute webhook
        try:
            res = requests.post(url, json=payload, timeout=30)
            res_data = res.json()
        except json.JSONDecodeError:
            res_data = {"response": res.text if res else "No response"}
        except Exception as e:
            res_data = {"error": str(e)}

        # Create execution log
        exec_id = f"TE{uuid.uuid1().hex}"
        exec_log = {
            "task_exec_id": exec_id,
            "task_id": task.get("task_id"),
            "run_id": task.get("run_id"),
            "executor_id": "webhook",
            "status": "success" if "error" not in res_data else "failed",
            "input": payload,
            "output": {"step": "webhook", "data": res_data},
            "space_id": task.get("space_id"),
            "data": {},
        }

        try:
            TaskExecutionLogModel.save_single_to_db(exec_log)
            print(f"Webhook executed for task {task.get('task_id')}")
        except Exception as e:
            print(f"Error saving webhook execution log: {e}")

        return exec_log

    def recover_recent_failed_runs(self, minutes: int = 5) -> dict:
        """
        Recover failed/pending/partial runs from last N minutes.

        Args:
            minutes: Number of minutes to look back

        Returns:
            Stats dict with recovered and failed counts
        """
        from super_services.orchestration.task.task_service import TaskService

        task_service = TaskService()
        stats = {"recovered": 0, "failed": 0}

        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

            # Find runs with status in failed/partial/pending
            failed_runs = list(
                RunModel._get_collection().find(
                    {
                        "status": {"$in": ["failed", "partial", "pending"]},
                        "modified": {"$gt": cutoff_time},
                    }
                )
            )

            print(f"Found {len(failed_runs)} runs to recover")

            for run in failed_runs:
                try:
                    task_service.recover_call_tasks(run_id=run.get("run_id"))
                    stats["recovered"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    print(f"Failed to recover run {run.get('run_id')}: {e}")

        except Exception as e:
            print(f"Error in recover_recent_failed_runs: {e}")
            traceback.print_exc()

        return stats

    def create_sql_entries(
        self, call_data: dict, pilot_data: dict, assistant_ids: list
    ) -> None:
        """Create SQL entries for call logs in metrics_calllog table."""
        query = """
          INSERT INTO metrics_calllog (
                call_status,
                end_reason,
                start_time,
                end_time,
                call_type,
                call_duration,
                source_number,
                destination_number,
                metrics_metadata,
                agent_id,
                bridge_id,
                organization_id,
                space_id,
                creation_time,
                product_types,
                calculated,
                product_id
                )
                VALUES (
                %(call_status)s,
                %(end_reason)s,
                %(start_time)s,
                %(end_time)s,
                %(call_type)s,
                EXTRACT(EPOCH FROM (%(end_time)s::timestamp - %(start_time)s::timestamp))::integer,
                %(source)s,
                %(destination)s,
                %(metadata)s,
                (SELECT id FROM core_components_pilot WHERE handle = %(assignee)s LIMIT 1),
                (SELECT tvn.bridge_id
                FROM telephony_voicebridgenumber tvn
                JOIN core_components_telephony_number n ON tvn.number_id = n.id
                WHERE n.number = %(source)s OR n.number = %(destination)s
                LIMIT 1),
                (SELECT space_organization_id FROM space_space WHERE id = %(space_id)s LIMIT 1),
                %(space_id)s,
                NOW(),
                'ai_agents',
                FALSE,
                'unpod.ai'
                );
        """

        for assistant_id in assistant_ids:
            logs = call_data.get(assistant_id, [])
            pilot = pilot_data.get(assistant_id)

            if not logs or not pilot:
                continue

            for log in logs:
                call_type_raw = log.get("type", "")
                call_type = (
                    "inbound" if "inbound" in call_type_raw.lower() else "outbound"
                )

                params = {
                    "call_status": log.get("status"),
                    "end_reason": log.get("endedReason", ""),
                    "start_time": self.convert_iso_to_mysql(log.get("startedAt")),
                    "end_time": self.convert_iso_to_mysql(log.get("endedAt")),
                    "call_type": call_type,
                    "source": log.get("customer", {}).get("number", ""),
                    "destination": self.get_agent_number(
                        log.get("phoneNumberId", None)
                    ),
                    "metadata": json.dumps(
                        {
                            "cost": log.get("cost", 0),
                            "type": call_type,
                            "provider": os.getenv("AGENT_PROVIDER", "call"),
                        }
                    ),
                    "assignee": pilot.get("handle"),
                    "space_id": pilot.get("space_id"),
                    "duration": log.get("duration", 0),
                }

                try:
                    executeQuery(query, params=params, commit=True)
                except Exception as e:
                    # Ignore duplicate entry errors (PostgreSQL uses "duplicate key")
                    if "duplicate key" not in str(
                        e
                    ).lower() and "Duplicate entry" not in str(e):
                        print(f"Error inserting call log: {e}")

            print(f"{len(logs)} calls processed for {assistant_id}")

    async def sync_flow(
        self,
        assistant_id: Optional[str] = None,
        start_date: Optional[str] = None,
    ) -> dict:
        """
        Main sync flow - runs every 5 minutes.

        Steps:
        1. Get last execution time (or use start_date if provided)
        2. Fetch all recent calls (inbound + outbound), optionally filtered by assistant_id
        3. For each call:
           a. Find task by call_id
           b. If no task and call is inbound/ended → create task
           c. Get recording URL if missing
           d. Execute post-call workflow if not done
           e. Execute webhook if configured
        4. Recover failed/pending runs
        5. Update last execution time

        Args:
            assistant_id: Optional filter by VAPI assistant ID
            start_date: Optional start datetime in ISO 8601 format

        Returns:
            Stats dict with processing results
        """
        print(f"\n[SYNC] {'='*50}")
        print(f"[SYNC] Starting at {datetime.utcnow().isoformat()}")

        # Step 1: Get last execution time (use start_date if provided)
        if start_date:
            last_run_time = start_date
            print(f"[SYNC] Step 1: Using provided start_date = {last_run_time}")
        else:
            last_run_time = self.get_last_execution_time()
            print(f"[SYNC] Step 1: Last run = {last_run_time}")

        # Step 2: Fetch recent calls
        all_calls = self.fetch_all_recent_calls(
            last_run_time=last_run_time,
            assistant_id=assistant_id,
            call_type="inboundPhoneCall",
        )
        print(f"[SYNC] Step 2: Fetched {len(all_calls)} calls")

        if not all_calls:
            print("[SYNC] No new calls to process")
            self.update_last_execution_time()
            return {"total_calls": 0, "message": "No new calls"}

        # Group calls by assistant_id
        calls_by_assistant: dict[str, list] = {}
        for call in all_calls:
            assistant_id = call.get("assistantId")
            if assistant_id:
                if assistant_id not in calls_by_assistant:
                    calls_by_assistant[assistant_id] = []
                calls_by_assistant[assistant_id].append(call)

        # Get pilot data for all assistants
        print(f"[SYNC] Step 3: Loading pilot data for {len(calls_by_assistant)} agents")
        pilot_data = self.get_pilot_data(list(calls_by_assistant.keys()))

        # # Create SQL entries for metrics
        # self.create_sql_entries(
        #     calls_by_assistant, pilot_data, list(calls_by_assistant.keys())
        # )

        stats = {
            "total_calls": len(all_calls),
            "tasks_found": 0,
            "tasks_created": 0,
            "tasks_updated": 0,
            "recordings_updated": 0,
            "post_call_executed": 0,
            "webhooks_executed": 0,
            "errors": 0,
        }

        # Pre-fetch SBC recordings for the period (for fallback matching)
        print("[SYNC] Step 3.5: Pre-fetching SBC recordings...")
        sbc_start_time = datetime.now(timezone.utc) - timedelta(days=1)
        if last_run_time:
            try:
                sbc_start_time = datetime.fromisoformat(
                    last_run_time.replace("Z", "+00:00")
                )
            except ValueError:
                pass
        sbc_recordings_map = self.fetch_sbc_recordings_for_period(sbc_start_time)

        # Step 4: Process each call
        print(f"[SYNC] Step 4: Processing {len(all_calls)} calls...")
        for idx, call in enumerate(all_calls):
            call_id = call.get("id")
            assistant_id = call.get("assistantId")
            call_type = call.get("type", "")
            call_status = call.get("status")

            if not call_id:
                continue

            try:
                # Find existing task using multiple matching strategies
                task = self.find_task_for_call(call)

                if task:
                    stats["tasks_found"] += 1
                    print(
                        f"  [{idx+1}] FOUND task={task.get('task_id')} call={call_id[:8]}..."
                    )
                    # Update task output with latest call data from API
                    original_output = task.get("output", {}).copy()
                    task = self.update_task_output_from_call(task, call)
                    if task.get("output") != original_output:
                        stats["tasks_updated"] += 1
                        print(f"  [{idx+1}] UPDATED task output from API")
                else:
                    # Create task only for inbound calls that ended
                    if call_status == "ended":
                        pilot = pilot_data.get(assistant_id, {})
                        if pilot:
                            print(
                                f"  [{idx+1}] CREATING task for {call_type} call={call_id[:8]}..."
                            )
                            task = self.create_task_for_call(call, pilot_data)
                            if task:
                                stats["tasks_created"] += 1
                                print(f"  [{idx+1}] CREATED task={task.get('task_id')}")

                if not task:
                    continue

                # Get recording URL if missing
                recording_url = task.get("output", {}).get("recording_url")
                if not recording_url:
                    recording_url = await self.get_recording_url(
                        call_id, call, task, sbc_recordings_map
                    )
                    if recording_url:
                        output = task.get("output", {})
                        output["recording_url"] = recording_url
                        TaskModel.update_one(
                            {"task_id": task.get("task_id")}, {"output": output}
                        )
                        task["output"] = output  # Update local reference
                        stats["recordings_updated"] += 1
                        print(f"  [{idx+1}] RECORDING updated")

                # Execute post-call workflow if not done and has transcript
                post_call_data = task.get("output", {}).get("post_call_data")
                transcript = task.get("output", {}).get("transcript")

                if not post_call_data and transcript:
                    print(f"  [{idx+1}] POST-CALL workflow starting...")
                    result = await self.execute_post_call_for_task(task)
                    if result:
                        output = task.get("output", {})
                        output["post_call_data"] = result
                        TaskModel.update_one(
                            {"task_id": task.get("task_id")}, {"output": output}
                        )
                        task["output"] = output  # Update local reference
                        stats["post_call_executed"] += 1
                        print(f"  [{idx+1}] POST-CALL completed")

                # Execute webhook if configured
                pilot = pilot_data.get(assistant_id, {})
                if pilot:
                    exec_log = self.execute_webhook_if_configured(task, pilot)
                    if exec_log:
                        stats["webhooks_executed"] += 1
                        print(f"  [{idx+1}] WEBHOOK executed")

            except Exception as e:
                stats["errors"] += 1
                print(f"  [{idx+1}] ERROR: {e}")
                traceback.print_exc()

        # Step 5: Recover failed runs
        print(f"[SYNC] Step 5: Recovering failed runs...")
        recovery_stats = self.recover_recent_failed_runs(minutes=5)
        stats["runs_recovered"] = recovery_stats.get("recovered", 0)
        stats["recovery_failed"] = recovery_stats.get("failed", 0)

        # Step 6: Update last execution time
        self.update_last_execution_time()

        print(f"[SYNC] {'='*50}")
        print(f"[SYNC] Completed: {json.dumps(stats)}")
        print(f"[SYNC] {'='*50}\n")

        return stats


async def sync_run_tasks(run_id: str) -> dict:
    """
    Sync tasks for a specific run by fetching calls from VAPI and updating task statuses.

    Steps:
    1. Fetch run by run_id
    2. Fetch all tasks for the run
    3. Get assignee(s) from tasks
    4. Fetch all calls for that duration (run start time to now) and assignee
    5. Match calls to tasks and update task status from call data

    Args:
        run_id: The run ID to sync tasks for

    Returns:
        Stats dict with sync results
    """
    from super_services.orchestration.task.task_service import TaskService

    service = CallsSyncService()
    task_service = TaskService()

    print(f"\n[RUN_SYNC] {'='*50}")
    print(f"[RUN_SYNC] Syncing run {run_id}")

    stats = {
        "run_id": run_id,
        "tasks_found": 0,
        "calls_fetched": 0,
        "tasks_updated": 0,
        "post_call_executed": 0,
        "errors": 0,
    }

    # Step 1: Fetch run
    run = RunModel.find_one(run_id=run_id)
    if not run:
        print(f"[RUN_SYNC] Run {run_id} not found")
        return {"error": "Run not found", **stats}

    run_created = run.get("created") or run.get("modified")
    print(f"[RUN_SYNC] Step 1: Found run, created={run_created}")

    # Step 2: Fetch all tasks for the run
    tasks = list(TaskModel._get_collection().find({"run_id": run_id}))
    stats["tasks_found"] = len(tasks)
    print(f"[RUN_SYNC] Step 2: Found {len(tasks)} tasks")

    if not tasks:
        print(f"[RUN_SYNC] No tasks found for run {run_id}")
        return stats

    # Step 3: Get unique assignees from tasks
    assignees = set()
    for task in tasks:
        assignee = task.get("assignee")
        if assignee:
            assignees.add(assignee)

    print(f"[RUN_SYNC] Step 3: Found {len(assignees)} unique assignees: {assignees}")

    # Get vapi_agent_ids for assignees
    assistant_ids = set()
    for task in tasks:
        vapi_agent_id = task.get("input", {}).get("vapi_agent_id")
        if vapi_agent_id:
            assistant_ids.add(vapi_agent_id)

    print(f"[RUN_SYNC] Found {len(assistant_ids)} unique assistant_ids")

    # Step 4: Determine time range for call fetching
    # Use run created time as start, current time as end
    start_time = None
    if run_created:
        if isinstance(run_created, str):
            start_time = run_created
        elif hasattr(run_created, "isoformat"):
            start_time = run_created.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            )

    if not start_time:
        # Fallback: use earliest task modified time
        earliest_task = min(
            tasks, key=lambda t: t.get("created") or t.get("modified") or datetime.max
        )
        task_time = earliest_task.get("created") or earliest_task.get("modified")
        if task_time:
            if isinstance(task_time, str):
                start_time = task_time
            elif hasattr(task_time, "isoformat"):
                start_time = task_time.isoformat(timespec="milliseconds").replace(
                    "+00:00", "Z"
                )

    print(f"[RUN_SYNC] Step 4: Fetching calls from {start_time}")

    # Fetch all calls from that time
    all_calls = service.fetch_all_recent_calls(last_run_time=start_time)
    stats["calls_fetched"] = len(all_calls)
    print(f"[RUN_SYNC] Fetched {len(all_calls)} calls")

    # Filter calls by assistant_ids if we have them
    if assistant_ids:
        all_calls = [c for c in all_calls if c.get("assistantId") in assistant_ids]
        print(f"[RUN_SYNC] Filtered to {len(all_calls)} calls matching assistants")

    # Build a map of call_id to call data for quick lookup
    calls_by_id: dict[str, dict] = {c.get("id"): c for c in all_calls if c.get("id")}

    # Build a map of assistant_id + contact_number to calls for matching
    calls_by_contact: dict[str, list] = {}
    for call in all_calls:
        assistant_id = call.get("assistantId")
        contact = call.get("customer", {}).get("number") or call.get(
            "destination", {}
        ).get("number")
        if assistant_id and contact:
            key = f"{assistant_id}:{contact}"
            if key not in calls_by_contact:
                calls_by_contact[key] = []
            calls_by_contact[key].append(call)

    # Step 5: Match calls to tasks and update
    print(f"[RUN_SYNC] Step 5: Matching {len(tasks)} tasks to calls...")

    for idx, task in enumerate(tasks):
        task_id = task.get("task_id")
        task_status = task.get("status")

        # Skip already completed tasks with post_call_data
        if task_status == "completed" and task.get("output", {}).get("post_call_data"):
            continue

        try:
            call_data = None

            # Try to match by call_id first
            existing_call_id = task.get("output", {}).get("call_id")
            if existing_call_id and existing_call_id in calls_by_id:
                call_data = calls_by_id[existing_call_id]
                print(f"  [{idx+1}] Matched task {task_id[:8]}... by call_id")

            # Try to match by assistant_id + contact_number
            if not call_data:
                assistant_id = task.get("input", {}).get("vapi_agent_id")
                contact = task.get("input", {}).get("contact_number")
                if assistant_id and contact:
                    key = f"{assistant_id}:{contact}"
                    matching_calls = calls_by_contact.get(key, [])
                    if matching_calls:
                        # Use the most recent call
                        call_data = max(
                            matching_calls,
                            key=lambda c: c.get("updatedAt") or "",
                        )
                        print(f"  [{idx+1}] Matched task {task_id[:8]}... by contact")

            if not call_data:
                continue

            # Update task output from call data
            original_output = task.get("output", {}).copy()
            updated_task = service.update_task_output_from_call(task, call_data)

            if updated_task.get("output") != original_output:
                stats["tasks_updated"] += 1
                print(f"  [{idx+1}] Updated task output from API")

            # Execute post-call workflow if not done and has transcript
            post_call_data = updated_task.get("output", {}).get("post_call_data")
            transcript = updated_task.get("output", {}).get("transcript")

            if not post_call_data and transcript:
                print(f"  [{idx+1}] Executing post-call workflow...")
                result = await service.execute_post_call_for_task(updated_task)
                if result:
                    output = updated_task.get("output", {})
                    output["post_call_data"] = result
                    TaskModel.update_one({"task_id": task_id}, {"output": output})
                    stats["post_call_executed"] += 1
                    print(f"  [{idx+1}] Post-call workflow completed")

        except Exception as e:
            stats["errors"] += 1
            print(f"  [{idx+1}] ERROR: {e}")
            traceback.print_exc()

    # Update run status and analytics
    print(f"[RUN_SYNC] Updating run status and analytics...")
    task_service.check_and_update_run_status(run_id)

    print(f"[RUN_SYNC] {'='*50}")
    print(f"[RUN_SYNC] Completed: {json.dumps(stats)}")
    print(f"[RUN_SYNC] {'='*50}\n")

    return stats


def sync_run(run_id: str) -> dict:
    """Synchronous entry point for syncing a specific run."""
    return asyncio.run(sync_run_tasks(run_id))


def calls_sync_cron(
    assistant_id: Optional[str] = None,
    start_date: Optional[str] = None,
) -> dict:
    """Synchronous entry point for cron scheduler."""
    service = CallsSyncService()
    return asyncio.run(
        service.sync_flow(
            assistant_id=assistant_id,
            start_date=start_date,
        )
    )


# Legacy function for backward compatibility
def inbound_calls_flow() -> dict:
    """Legacy entry point - now calls the unified sync flow."""
    return calls_sync_cron()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Calls Sync Service")
    parser.add_argument("--assistant-id", type=str, help="Filter by VAPI assistant ID")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start datetime in ISO 8601 format (e.g., 2025-01-01T10:00:00Z)",
    )
    parser.add_argument("--run-id", type=str, help="Sync a specific run ID")

    args = parser.parse_args()

    if args.run_id:
        print(f"Syncing run: {args.run_id}")
        result = sync_run(args.run_id)
        print(f"Result: {result}")
    else:
        # Run full sync flow with optional filters
        result = calls_sync_cron(
            assistant_id=args.assistant_id,
            start_date=args.start_date,
        )
        print(f"Result: {result}")
