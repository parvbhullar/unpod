"""
Calls Tool Plugin - CSV-based call task creation for SuperKik.

Provides tools for processing CSV files to create call runs and tasks.
Integrates with TaskService for run/task creation and Prefect for execution.
"""

import csv
import io
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated, Any, Callable, Dict, List, Optional

import httpx
from pydantic import Field

from super.core.logging import logging as app_logging
from super.core.voice.superkik.tools.base import ToolPlugin

if TYPE_CHECKING:
    from super.core.voice.superkik.handler import SuperKikHandler

logger = app_logging.get_logger("superkik.tools.calls")


@dataclass
class CSVColumnMapping:
    """Configuration for mapping CSV columns to task fields."""

    name_column: str = "name"
    contact_number_column: str = "contact_number"
    ref_id_column: Optional[str] = None
    extra_columns: List[str] = field(default_factory=list)


@dataclass
class CSVParseResult:
    """Result of parsing CSV data."""

    rows: List[Dict[str, Any]]
    headers: List[str]
    row_count: int
    errors: List[str] = field(default_factory=list)


@dataclass
class CallRunResult:
    """Result of creating a call run from CSV."""

    run_id: str
    task_ids: List[str]
    task_count: int
    status: Dict[str, str]
    errors: List[str] = field(default_factory=list)


async def fetch_csv_content(url: str) -> Optional[str]:
    """
    Fetch CSV content from a URL.

    Args:
        url: URL to fetch CSV from

    Returns:
        CSV content as string, or None if fetch failed
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to fetch CSV from {url}: {e}")
        return None


def parse_csv_content(
    content: str,
    column_mapping: CSVColumnMapping,
) -> CSVParseResult:
    """
    Parse CSV content with configurable column mapping.

    Args:
        content: CSV content as string
        column_mapping: Configuration for column mapping

    Returns:
        CSVParseResult with parsed rows
    """
    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    headers: List[str] = []

    try:
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames or []

        # Validate required columns exist
        if column_mapping.name_column not in headers:
            errors.append(f"Missing required column: {column_mapping.name_column}")
        if column_mapping.contact_number_column not in headers:
            errors.append(
                f"Missing required column: {column_mapping.contact_number_column}"
            )

        if errors:
            return CSVParseResult(rows=[], headers=headers, row_count=0, errors=errors)

        for row_num, row in enumerate(reader, start=2):
            name = row.get(column_mapping.name_column, "").strip()
            contact = row.get(column_mapping.contact_number_column, "").strip()

            if not name or not contact:
                errors.append(f"Row {row_num}: Missing name or contact_number")
                continue

            task_row = {
                "name": name,
                "contact_number": contact,
            }

            # Add ref_id if configured
            if column_mapping.ref_id_column and column_mapping.ref_id_column in headers:
                task_row["ref_id"] = row.get(column_mapping.ref_id_column, "")

            # Add extra columns
            for col in column_mapping.extra_columns:
                if col in headers:
                    task_row[col] = row.get(col, "")

            # Include all other columns in extra_data
            for header in headers:
                if header not in [
                    column_mapping.name_column,
                    column_mapping.contact_number_column,
                    column_mapping.ref_id_column,
                ] + column_mapping.extra_columns:
                    if header not in task_row:
                        task_row[header] = row.get(header, "")

            rows.append(task_row)

    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error parsing CSV: {e}")

    return CSVParseResult(
        rows=rows,
        headers=headers,
        row_count=len(rows),
        errors=errors,
    )


async def create_call_run_impl(
    handler: "SuperKikHandler",
    csv_rows: List[Dict[str, Any]],
    objective: str,
    collection_ref: str,
    assignee: Optional[str] = None,
    extra_input: Optional[Dict[str, Any]] = None,
    schedule: Optional[Dict[str, Any]] = None,
    require_approval: bool = True,
) -> CallRunResult:
    """
    Create a call run with tasks from parsed CSV rows.

    Args:
        handler: SuperKikHandler instance
        csv_rows: List of parsed CSV row dictionaries
        objective: Call objective/instructions for all tasks
        collection_ref: Collection reference for the run
        assignee: Agent handle to assign tasks to (defaults to handler's agent)
        extra_input: Additional data to include in all task inputs
        schedule: Optional scheduling configuration
        require_approval: If True, creates run with pending_approval status
            and does NOT trigger execution. User must approve first.

    Returns:
        CallRunResult with run_id and task_ids
    """
    errors: List[str] = []

    # Get context from handler
    user_state = handler.user_state
    space_id = getattr(user_state, "space_id", None) or handler.config.get("space_id")
    thread_id = str(getattr(user_state, "thread_id", None) or uuid.uuid4())
    user_id = getattr(user_state, "user_id", None)
    org_id = handler.config.get("org_id")

    if not space_id:
        errors.append("Missing space_id - cannot create run")
        return CallRunResult(
            run_id="",
            task_ids=[],
            task_count=0,
            status={},
            errors=errors,
        )

    # Default assignee to handler's agent
    if not assignee:
        assignee = handler.config.get("agent_handle") or handler.config.get(
            "pilot_handle"
        )

    if not assignee:
        errors.append("Missing assignee - cannot create tasks")
        return CallRunResult(
            run_id="",
            task_ids=[],
            task_count=0,
            status={},
            errors=errors,
        )

    try:
        from super_services.orchestration.task.task_service import TaskService

        task_service = TaskService()
    except ImportError as e:
        errors.append(f"TaskService not available: {e}")
        return CallRunResult(
            run_id="",
            task_ids=[],
            task_count=0,
            status={},
            errors=errors,
        )

    # Build run kwargs
    run_kwargs: Dict[str, Any] = {}
    task_kwargs: Dict[str, Any] = {}

    # Set status based on approval requirement
    if require_approval:
        run_kwargs["status"] = "pending_approval"
        task_kwargs["status"] = "pending_approval"
    elif schedule:
        run_kwargs["status"] = "scheduled"
        task_kwargs["status"] = "scheduled"
        scheduled_timestamp = _get_schedule_time(schedule)
        if scheduled_timestamp:
            run_kwargs["scheduled_timestamp"] = scheduled_timestamp
            task_kwargs["scheduled_timestamp"] = scheduled_timestamp

    # Create run
    try:
        run = task_service.create_run(
            space_id=space_id,
            user=user_id,
            collection_ref=collection_ref,
            batch_count=len(csv_rows),
            run_mode="prefect",
            thread_id=thread_id,
            user_org_id=org_id,
            user_info={"id": user_id} if user_id else {},
            run_type="call",
            **run_kwargs,
        )
        run_id = run["run_id"]
    except Exception as e:
        errors.append(f"Failed to create run: {e}")
        return CallRunResult(
            run_id="",
            task_ids=[],
            task_count=0,
            status={},
            errors=errors,
        )

    # Create tasks
    task_ids: List[str] = []
    status: Dict[str, str] = {}
    extra_input = extra_input or {}

    for row in csv_rows:
        task_input = {**row, **extra_input}
        task_data = {"objective": objective}
        ref_id = row.get("ref_id") or row.get("id") or row.get("document_id")

        try:
            result = task_service.add_task(
                run_id,
                task_data,
                assignee,
                collection_ref,
                thread_id,
                "call",
                input=task_input,
                attachments=[],
                ref_id=ref_id,
                space_id=space_id,
                user=user_id,
                user_org_id=org_id,
                user_info={"id": user_id} if user_id else {},
                **task_kwargs,
            )
            task_ids.append(result["task_id"])
            status[result["task_id"]] = result["status"]
        except Exception as e:
            errors.append(f"Failed to create task for {row.get('name')}: {e}")

    # Trigger prefect deployment if NOT requiring approval
    if task_ids and not require_approval:
        try:
            from super_services.orchestration.task.prefect import trigger_deployment

            data = {"run_id": run_id, "run_type": "call"}
            prefect_kwargs: Dict[str, Any] = {"parameters": {"job": data}}

            if schedule and "scheduled_timestamp" in run_kwargs:
                prefect_kwargs["state"] = _get_schedule_state(
                    run_kwargs["scheduled_timestamp"]
                )

            await trigger_deployment("Execute Run", **prefect_kwargs)
            logger.info(f"Triggered prefect deployment for run {run_id}")
        except Exception as e:
            logger.warning(f"Failed to trigger prefect deployment: {e}")
            # Don't add to errors - run was still created
    elif require_approval:
        logger.info(f"Run {run_id} awaiting approval before execution")

    logger.info(f"Created call run {run_id} with {len(task_ids)} tasks")

    return CallRunResult(
        run_id=run_id,
        task_ids=task_ids,
        task_count=len(task_ids),
        status=status,
        errors=errors,
    )


def _get_schedule_time(schedule: Dict[str, Any]) -> Optional[int]:
    """Get scheduled timestamp from schedule config."""
    try:
        if schedule.get("type") == "auto":
            auto_mins = schedule.get("delay_minutes", 10)
            return int(datetime.now(timezone.utc).timestamp()) + auto_mins * 60

        calling_date = schedule.get("calling_date")
        calling_time = schedule.get("calling_time")

        if calling_date and calling_time:
            import dateutil.parser

            dt_str = f"{calling_date} {calling_time}"
            dt_obj = dateutil.parser.parse(dt_str)
            scheduled_timestamp = int(dt_obj.timestamp())

            if scheduled_timestamp < int(datetime.now(timezone.utc).timestamp()):
                logger.warning("Scheduled time is in the past")
                return None

            return scheduled_timestamp
    except Exception as e:
        logger.error(f"Failed to parse schedule: {e}")

    return None


def _get_schedule_state(scheduled_timestamp: int) -> Dict[str, Any]:
    """Get prefect schedule state from timestamp."""
    return {
        "type": "SCHEDULED",
        "message": "",
        "state_details": {
            "scheduled_time": datetime.fromtimestamp(
                scheduled_timestamp, timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        },
    }


@dataclass
class ExecuteRunResult:
    """Result of executing an approved run."""

    run_id: str
    status: str
    task_count: int
    message: str
    errors: List[str] = field(default_factory=list)


async def execute_call_run_impl(
    _handler: "SuperKikHandler",
    run_id: str,
    schedule: Optional[Dict[str, Any]] = None,
) -> ExecuteRunResult:
    """
    Execute an approved call run.

    Called when user approves a pending run (clicks "YES - Execute Calls").
    Updates run/task status and triggers prefect deployment.

    Args:
        _handler: SuperKikHandler instance (unused but kept for consistency)
        run_id: The run ID to execute
        schedule: Optional scheduling configuration

    Returns:
        ExecuteRunResult with status and message
    """
    errors: List[str] = []

    try:
        from super_services.orchestration.task.task_service import TaskService

        task_service = TaskService()
    except ImportError as e:
        return ExecuteRunResult(
            run_id=run_id,
            status="error",
            task_count=0,
            message=f"TaskService not available: {e}",
            errors=[str(e)],
        )

    # Get run details
    try:
        run = task_service.get_run(run_id)
        if not run:
            return ExecuteRunResult(
                run_id=run_id,
                status="error",
                task_count=0,
                message=f"Run {run_id} not found",
                errors=["Run not found"],
            )

        current_status = run.get("status", "")
        if current_status not in ["pending_approval", "draft"]:
            return ExecuteRunResult(
                run_id=run_id,
                status="error",
                task_count=0,
                message=f"Run {run_id} cannot be executed (status: {current_status})",
                errors=[f"Invalid status: {current_status}"],
            )
    except Exception as e:
        return ExecuteRunResult(
            run_id=run_id,
            status="error",
            task_count=0,
            message=f"Failed to get run: {e}",
            errors=[str(e)],
        )

    # Update run status
    new_status = "scheduled" if schedule else "queued"
    try:
        update_data: Dict[str, Any] = {"status": new_status}

        if schedule:
            scheduled_timestamp = _get_schedule_time(schedule)
            if scheduled_timestamp:
                update_data["scheduled_timestamp"] = scheduled_timestamp

        task_service.update_run(run_id, update_data)
        logger.info(f"Updated run {run_id} status to {new_status}")
    except Exception as e:
        errors.append(f"Failed to update run status: {e}")

    # Update task statuses
    task_count = 0
    try:
        tasks = task_service.get_tasks_by_run(run_id)
        task_count = len(tasks) if tasks else 0

        for task in tasks or []:
            task_id = task.get("task_id")
            if task_id:
                task_service.update_task(task_id, {"status": new_status})
    except Exception as e:
        errors.append(f"Failed to update task statuses: {e}")

    # Trigger prefect deployment
    try:
        from super_services.orchestration.task.prefect import trigger_deployment

        data = {"run_id": run_id, "run_type": "call"}
        prefect_kwargs: Dict[str, Any] = {"parameters": {"job": data}}

        if schedule:
            scheduled_timestamp = _get_schedule_time(schedule)
            if scheduled_timestamp:
                prefect_kwargs["state"] = _get_schedule_state(scheduled_timestamp)

        await trigger_deployment("Execute Run", **prefect_kwargs)
        logger.info(f"Triggered prefect deployment for approved run {run_id}")
    except Exception as e:
        errors.append(f"Failed to trigger deployment: {e}")
        return ExecuteRunResult(
            run_id=run_id,
            status="error",
            task_count=task_count,
            message=f"Failed to trigger execution: {e}",
            errors=errors,
        )

    return ExecuteRunResult(
        run_id=run_id,
        status="executing",
        task_count=task_count,
        message=f"Execution started for {task_count} call tasks",
        errors=errors,
    )


async def reject_call_run_impl(
    _handler: "SuperKikHandler",
    run_id: str,
) -> ExecuteRunResult:
    """
    Reject a pending call run.

    Called when user rejects a pending run (clicks "NO - Reject").
    Updates run/task status to cancelled.

    Args:
        _handler: SuperKikHandler instance (unused but kept for consistency)
        run_id: The run ID to reject

    Returns:
        ExecuteRunResult with status and message
    """
    try:
        from super_services.orchestration.task.task_service import TaskService

        task_service = TaskService()
    except ImportError as e:
        return ExecuteRunResult(
            run_id=run_id,
            status="error",
            task_count=0,
            message=f"TaskService not available: {e}",
            errors=[str(e)],
        )

    # Update run status to cancelled
    try:
        task_service.update_run(run_id, {"status": "cancelled"})
        logger.info(f"Rejected run {run_id}")
    except Exception as e:
        return ExecuteRunResult(
            run_id=run_id,
            status="error",
            task_count=0,
            message=f"Failed to reject run: {e}",
            errors=[str(e)],
        )

    # Update task statuses
    task_count = 0
    try:
        tasks = task_service.get_tasks_by_run(run_id)
        task_count = len(tasks) if tasks else 0

        for task in tasks or []:
            task_id = task.get("task_id")
            if task_id:
                task_service.update_task(task_id, {"status": "cancelled"})
    except Exception as e:
        logger.warning(f"Failed to update task statuses: {e}")

    return ExecuteRunResult(
        run_id=run_id,
        status="cancelled",
        task_count=task_count,
        message=f"Rejected call run with {task_count} tasks",
    )


async def process_csv_for_calls_impl(
    handler: "SuperKikHandler",
    csv_url: Optional[str] = None,
    csv_content: Optional[str] = None,
    objective: str = "",
    collection_ref: str = "",
    name_column: str = "name",
    contact_column: str = "contact_number",
    ref_id_column: Optional[str] = None,
    assignee: Optional[str] = None,
    extra_input: Optional[Dict[str, Any]] = None,
    schedule_type: Optional[str] = None,
    schedule_date: Optional[str] = None,
    schedule_time: Optional[str] = None,
) -> CallRunResult:
    """
    Process CSV file and create call tasks.

    Args:
        handler: SuperKikHandler instance
        csv_url: URL to fetch CSV from (takes priority over csv_content)
        csv_content: Raw CSV content as string
        objective: Call objective/instructions
        collection_ref: Collection reference for the run
        name_column: CSV column name for contact name
        contact_column: CSV column name for phone number
        ref_id_column: Optional CSV column for reference ID
        assignee: Agent handle to assign tasks to
        extra_input: Additional data to include in all task inputs
        schedule_type: Schedule type ("auto", "manual", or None for immediate)
        schedule_date: Date for manual scheduling (YYYY-MM-DD)
        schedule_time: Time for manual scheduling (HH:MM)

    Returns:
        CallRunResult with run_id and task_ids
    """
    errors: List[str] = []

    # Get CSV content
    content: Optional[str] = None

    if csv_url:
        content = await fetch_csv_content(csv_url)
        if not content:
            errors.append(f"Failed to fetch CSV from URL: {csv_url}")
    elif csv_content:
        content = csv_content
    else:
        # Try to get from handler's pending attachments
        content = await _get_csv_from_attachments(handler)
        if not content:
            errors.append(
                "No CSV provided - pass csv_url, csv_content, or attach file"
            )

    if not content:
        return CallRunResult(
            run_id="",
            task_ids=[],
            task_count=0,
            status={},
            errors=errors,
        )

    # Parse CSV
    column_mapping = CSVColumnMapping(
        name_column=name_column,
        contact_number_column=contact_column,
        ref_id_column=ref_id_column,
    )

    parse_result = parse_csv_content(content, column_mapping)

    if parse_result.errors:
        errors.extend(parse_result.errors)

    if not parse_result.rows:
        errors.append("No valid rows found in CSV")
        return CallRunResult(
            run_id="",
            task_ids=[],
            task_count=0,
            status={},
            errors=errors,
        )

    # Build schedule config
    schedule: Optional[Dict[str, Any]] = None
    if schedule_type:
        schedule = {"type": schedule_type}
        if schedule_type == "manual" and schedule_date and schedule_time:
            schedule["calling_date"] = schedule_date
            schedule["calling_time"] = schedule_time

    # Create run and tasks
    result = await create_call_run_impl(
        handler=handler,
        csv_rows=parse_result.rows,
        objective=objective or "Execute call campaign",
        collection_ref=collection_ref or "calls",
        assignee=assignee,
        extra_input=extra_input,
        schedule=schedule,
    )

    result.errors.extend(errors)
    return result


async def _get_csv_from_attachments(handler: "SuperKikHandler") -> Optional[str]:
    """
    Get CSV content from handler's message attachments.

    Checks the user_state for recent messages with CSV attachments.
    Supports both raw file metadata (media_url) and processed files (local_path).

    Args:
        handler: SuperKikHandler instance

    Returns:
        CSV content as string, or None if not found
    """
    try:
        # Check user_state for attachments in recent messages
        user_state = handler.user_state
        if not user_state:
            logger.debug("No user_state available for CSV lookup")
            return None

        # Check for files in user_state.files (populated by voice mode handler)
        files = getattr(user_state, "files", None) or []

        # Also check model_config for backward compatibility
        if not files and hasattr(user_state, "model_config"):
            config = user_state.model_config or {}
            files = config.get("files", [])

        logger.debug(f"Found {len(files)} file(s) in user_state for CSV lookup")

        for file_info in files:
            if isinstance(file_info, dict):
                media_url = file_info.get("media_url", "")
                media_type = file_info.get("media_type", "")
                name = file_info.get("name", "")
                local_path = file_info.get("local_path")
                original_url = file_info.get("original_url", "")

                logger.debug(
                    f"Checking file: name={name}, media_type={media_type}, "
                    f"has_local_path={bool(local_path)}, "
                    f"has_media_url={bool(media_url)}"
                )

                # Check if this is a CSV or Excel file
                is_csv = (
                    media_type in ("csv", "text/csv", "application/csv")
                    or name.endswith(".csv")
                    or media_url.endswith(".csv")
                    or (original_url and original_url.endswith(".csv"))
                )
                is_excel = (
                    media_type
                    in (
                        "xlsx",
                        "xls",
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet",
                        "application/vnd.ms-excel",
                    )
                    or name.endswith(".xlsx")
                    or name.endswith(".xls")
                )

                if is_csv or is_excel:
                    logger.info(
                        f"Found CSV/Excel file: {name} (type={media_type})"
                    )

                    # First try local path (already downloaded)
                    if local_path:
                        try:
                            if is_excel:
                                # Convert Excel to CSV
                                content = await _read_excel_as_csv(local_path)
                            else:
                                with open(local_path, "r", encoding="utf-8") as f:
                                    content = f.read()

                            if content:
                                logger.info(
                                    f"Read {len(content)} bytes from local file: "
                                    f"{local_path}"
                                )
                                return content
                        except Exception as e:
                            logger.warning(
                                f"Failed to read local file {local_path}: {e}"
                            )

                    # Fall back to fetching from URL
                    url = media_url or original_url
                    if url:
                        content = await fetch_csv_content(url)
                        if content:
                            logger.info(f"Fetched CSV from URL: {url}")
                            return content

    except Exception as e:
        logger.error(f"Failed to get CSV from attachments: {e}")
        import traceback

        logger.error(traceback.format_exc())

    return None


async def _read_excel_as_csv(file_path: str) -> Optional[str]:
    """
    Read an Excel file and convert it to CSV string.

    Args:
        file_path: Path to the Excel file

    Returns:
        CSV content as string, or None if conversion failed
    """
    try:
        import pandas as pd

        # Read Excel file
        df = pd.read_excel(file_path)

        # Convert to CSV string
        csv_content = df.to_csv(index=False)
        logger.info(f"Converted Excel to CSV: {len(df)} rows")
        return csv_content

    except ImportError:
        logger.warning("pandas not available for Excel conversion")
        return None
    except Exception as e:
        logger.error(f"Failed to convert Excel to CSV: {e}")
        return None


class CallsToolPlugin(ToolPlugin):
    """
    Tool plugin for CSV-based call task creation.

    Provides tools:
    - process_csv_for_calls: Parse CSV and create call run/tasks (pending approval)
    - execute_call_run: Execute an approved call run
    - reject_call_run: Reject/cancel a pending call run
    """

    name = "calls"

    def _create_tools(self) -> List[Callable]:
        """Create calls-related tool functions."""
        return [
            self._create_process_csv_tool(),
            self._create_execute_call_run_tool(),
            self._create_reject_call_run_tool(),
        ]

    def _create_process_csv_tool(self) -> Callable:
        """Create the process_csv_for_calls function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def process_csv_for_calls(
            objective: Annotated[
                str,
                Field(
                    description=(
                        "Call objective/instructions for all calls. "
                        "What should be accomplished during each call."
                    )
                ),
            ],
            csv_url: Annotated[
                Optional[str],
                Field(
                    description=(
                        "URL to fetch CSV file from. "
                        "If not provided, will use attached CSV file."
                    )
                ),
            ] = None,
            collection_ref: Annotated[
                Optional[str],
                Field(
                    description=(
                        "Collection reference for organizing the run. "
                        "Defaults to 'calls'."
                    )
                ),
            ] = None,
            name_column: Annotated[
                Optional[str],
                Field(
                    description=(
                        "CSV column name containing contact name. "
                        "Defaults to 'name'."
                    )
                ),
            ] = None,
            contact_column: Annotated[
                Optional[str],
                Field(
                    description=(
                        "CSV column name containing phone number. "
                        "Defaults to 'contact_number'."
                    )
                ),
            ] = None,
            schedule_type: Annotated[
                Optional[str],
                Field(
                    description=(
                        "Schedule type: 'auto' (10 min delay), "
                        "'manual' (specify date/time), or None for immediate."
                    )
                ),
            ] = None,
        ) -> str:
            """
            Process a CSV file to create call tasks for a calling campaign.

            Use this tool when the user wants to:
            - Process a CSV file with contacts for calling
            - Create a batch of call tasks
            - Start a calling campaign

            The CSV file should have columns for name and contact_number.
            Additional columns will be included as task input data.

            Example triggers:
            - "Process this CSV for calls"
            - "Create calls from this contact list"
            - "Start a calling campaign with this file"
            """
            try:
                result = await process_csv_for_calls_impl(
                    handler=handler,
                    csv_url=csv_url,
                    objective=objective,
                    collection_ref=collection_ref or "calls",
                    name_column=name_column or "name",
                    contact_column=contact_column or "contact_number",
                    schedule_type=schedule_type,
                )

                if result.errors and not result.task_ids:
                    return json.dumps(
                        {
                            "status": "failed",
                            "errors": result.errors,
                            "message": (
                                f"Failed to process CSV: {'; '.join(result.errors)}"
                            ),
                        }
                    )

                response = {
                    "status": "pending_approval",
                    "run_id": result.run_id,
                    "task_count": result.task_count,
                    "task_ids": result.task_ids[:5],  # First 5 for display
                    "message": (
                        f"Created call run with {result.task_count} tasks. "
                        f"Awaiting approval to execute calls."
                    ),
                    "approval_required": True,
                    "approval_actions": {
                        "approve": "execute_call_run",
                        "reject": "reject_call_run",
                    },
                }

                if result.errors:
                    response["warnings"] = result.errors

                return json.dumps(response)

            except Exception as e:
                self._logger.error(f"process_csv_for_calls error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error processing CSV: {str(e)}",
                    }
                )

        return process_csv_for_calls

    def _create_execute_call_run_tool(self) -> Callable:
        """Create the execute_call_run function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def execute_call_run(
            run_id: Annotated[
                str,
                Field(
                    description="The run ID to execute (from process_csv_for_calls)"
                ),
            ],
        ) -> str:
            """
            Execute an approved call run.

            Use this tool when the user approves a pending call run:
            - "Yes, execute the calls"
            - "Approve the call run"
            - "Start the calls"

            Requires a run_id from a previous process_csv_for_calls call.
            """
            try:
                result = await execute_call_run_impl(
                    _handler=handler,
                    run_id=run_id,
                )

                return json.dumps(
                    {
                        "status": result.status,
                        "run_id": result.run_id,
                        "task_count": result.task_count,
                        "message": result.message,
                        "errors": result.errors if result.errors else None,
                    }
                )

            except Exception as e:
                self._logger.error(f"execute_call_run error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error executing run: {str(e)}",
                    }
                )

        return execute_call_run

    def _create_reject_call_run_tool(self) -> Callable:
        """Create the reject_call_run function tool."""
        try:
            from livekit.agents.llm import function_tool
        except ImportError:
            self._logger.warning("livekit.agents not available")
            return lambda: None

        handler = self._handler

        @function_tool
        async def reject_call_run(
            run_id: Annotated[
                str,
                Field(
                    description="The run ID to reject (from process_csv_for_calls)"
                ),
            ],
        ) -> str:
            """
            Reject/cancel a pending call run.

            Use this tool when the user rejects a pending call run:
            - "No, cancel the calls"
            - "Reject the call run"
            - "Don't execute"

            Requires a run_id from a previous process_csv_for_calls call.
            """
            try:
                result = await reject_call_run_impl(
                    _handler=handler,
                    run_id=run_id,
                )

                return json.dumps(
                    {
                        "status": result.status,
                        "run_id": result.run_id,
                        "task_count": result.task_count,
                        "message": result.message,
                    }
                )

            except Exception as e:
                self._logger.error(f"reject_call_run error: {e}")
                return json.dumps(
                    {
                        "status": "error",
                        "message": f"Error rejecting run: {str(e)}",
                    }
                )

        return reject_call_run

    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Return calls metrics (placeholder for future tracking)."""
        return None
