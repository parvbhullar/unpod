import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from unpod.common.geo import getIPAddressLocation, getUserIp
from unpod.common.mongodb import MongoDBQueryManager
from unpod.common.string import machine_to_label
from unpod.common.utils import get_global_configs
from unpod.core_components.tasks.constants import TASKS_DATA
from unpod.core_components.utils import get_user_data
from unpod.knowledge_base.utils import get_collection
import requests

User = get_user_model()


def get_pilot_data(pilot):
    from unpod.core_components.models import Pilot
    from django.db.models import Q

    query = Q(handle=pilot)

    pilot_obj = Pilot.objects.filter(query).values("config").first()
    if pilot_obj:
        return pilot_obj.get("config", {})
    return {}


def get_agent_schedule_data(pilot):
    from unpod.core_components.models import Pilot
    from django.db.models import Q

    query = Q(handle=pilot)

    pilot_obj = Pilot.objects.filter(query).first()
    if pilot_obj:
        return {
            "type": "auto",
            "calling_days": pilot_obj.calling_days,
            "calling_time_ranges": pilot_obj.calling_time_ranges,
            "quality": (pilot_obj.telephony_config or {}).get("quality", "good"),
        }
    return {}


def get_execution_type(content_type):
    if content_type == "contact":
        return "call"
    elif content_type == "email":
        return "email"
    return "answer"


def get_run_mode():
    prefect_config = get_global_configs("prefect-config")
    if prefect_config and prefect_config.get("enable", False):
        return "prefect"
    return "prod" if getattr(settings, "ENV_NAME", "Prod").lower() == "prod" else "dev"


def convert_run_data(validated_data, space, user, request):
    content_type = space.content_type
    run_data = {"space_id": str(space.id)}
    pilot = validated_data.get("pilot")
    pilot_data = get_pilot_data(pilot)
    loc_data = getIPAddressLocation(getUserIp(request))
    run_data["assignee"] = pilot
    run_data["run_mode"] = get_run_mode()
    run_data["collection_ref"] = get_collection(space.token, content_type)
    run_data["user"] = get_user_data(user)
    run_data["user"]["id"] = str(run_data["user"]["id"])
    run_data["user"]["location"] = loc_data
    run_data["org_id"] = str(space.space_organization_id)
    run_data["data"] = {"context": validated_data.get("context")}

    execution_type = get_execution_type(content_type)
    extra_input = {}
    extra_data = {}
    extra_data["space_token"] = space.token
    if validated_data.get("filters"):
        extra_data["filters"] = validated_data.get("filters")
    if execution_type == "call":
        vapi_agent_id = pilot_data.get("voice", {}).get("vapi_agent_id")
        if vapi_agent_id:
            extra_input["vapi_agent_id"] = vapi_agent_id
            if pilot_data.get("number_id", None):
                extra_input["number_id"] = pilot_data.get("number_id")

    tasks_data = []

    data = get_agent_schedule_data(pilot)
    extra_input["quality"] = data.get("quality")
    if validated_data.get("schedule", {}).get("type") == "auto":
        extra_data["schedule"] = data

    elif validated_data.get("schedule", {}).get("type") == "custom":
        extra_data["schedule"] = {
            "type": "custom",
            "calling_date": validated_data.get("schedule").get("calling_date"),
            "calling_time": validated_data.get("schedule").get("calling_time"),
        }

    for doc in validated_data.get("documents", []):
        if "token" not in doc:
            doc["token"] = space.token
        doc_id = doc.get("id") or doc.get("document_id")
        tasks_data.append(
            {
                "objective": validated_data.get("context"),
                "input_data": {**doc, **extra_input},
                "attachments": [],
                "ref_id": doc_id,
                "execution_type": execution_type,
            }
        )
    run_data["tasks"] = tasks_data
    extra_data["extra_input"] = extra_input
    if not tasks_data:
        extra_data["execution_type"] = execution_type
    if extra_data:
        run_data["data"].update(extra_data)
    return run_data


def push_to_tasks(run_data):
    print("run_data", run_data)
    url = f"{settings.API_SERVICE_URL}/task/create_run/"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=run_data, headers=headers)
    res_data = {}
    status = False
    if response.status_code == 200:
        res_data = response.json()["data"]
        status = True
    else:
        try:
            data = response.json()
        except Exception as ex:
            data = response.text
        res_data["message"] = data
    return res_data, status, response.status_code


def fetch_space_runs(space_id, request):
    url = f"{settings.API_SERVICE_URL}/task/get_runs/"
    query_params = {"space_id": str(space_id), **request.query_params.dict()}
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, params=query_params)
    res_data = {}
    status = False
    count = 0
    if response.status_code == 200:
        response = response.json()
        res_data = response["data"]
        status = True
        count = response["count"]
    else:
        res_data["message"] = response.text
    return res_data, status, count


def fetch_space_tasks(space_id, request):
    url = f"{settings.API_SERVICE_URL}/task/get_tasks/"
    query_params = {"space_id": str(space_id), **request.query_params.dict()}
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, params=query_params)
    res_data = {}
    status = False
    count = 0
    if response.status_code == 200:
        response = response.json()
        res_data = response["data"]
        status = True
        count = response["count"]
    else:
        res_data["message"] = response.text
    return res_data, status, count


def fetch_space_run_tasks(space_id, run_id, request):
    url = f"{settings.API_SERVICE_URL}/task/get_run_tasks/{run_id}/"
    query_params = {"space_id": str(space_id), **request.query_params.dict()}
    headers = {"Content-Type": "application/json"}
    response = requests.get(url, headers=headers, params=query_params)
    res_data = {}
    status = False
    count = 0
    if response.status_code == 200:
        response = response.json()
        res_data = response["data"]
        status = True
        count = response["count"]
    else:
        res_data["message"] = response.text
    return res_data, status, count


def prepare_columns(task):
    columns = {}

    if task:
        # print("task", task.get("space_id", 0), task.get("_id", 0), task)
        inputData = task.get("input", {})
        outputData = task.get("output", {})
        post_call_data = outputData.get("post_call_data", {})
        classification = post_call_data.get("classification", {})
        summary = post_call_data.get("summary", {})
        summary = summary if isinstance(summary, dict) else {"summary": summary}
        recording_url = outputData.get("recording_url", "")

        base_url = f"{getattr(settings, 'BASE_URL', 'https://unpod.ai')}/api/v1/"

        download_url = (
            f"{base_url}media/download-signed-url/?url={recording_url}"
            if recording_url
            else ""
        )

        columns["task_run_id"] = task.get("run_id", "")
        columns["task_id"] = task.get("task_id", "")
        columns["task_contact_number"] = (
            inputData.get("contact_number")
            or outputData.get("contact_number")
            or outputData.get("customer")
            or ""
        )
        columns["task_customer_name"] = inputData.get("name", "")
        columns["call_start_time"] = outputData.get("start_time", "")
        columns["call_end_time"] = outputData.get("end_time", "")
        columns["task_duration"] = outputData.get("duration", 0)
        columns["task_recording_url"] = download_url
        columns["task_summary_status"] = summary.get("status", "")
        columns["task_summary_summary"] = summary.get("summary", "")
        columns["task_summary_name"] = summary.get("name", "")
        columns["task_summary_contact"] = summary.get("contact", "")
        columns["task_success_evaluator"] = post_call_data.get("success_evaluator", 0)
        columns["task_structured_data"] = post_call_data.get("structured_data", "")
        columns["task_callback_datetime"] = summary.get("callback_datetime", "")
        columns["task_transcript"] = str(outputData.get("transcript", ""))
        columns["task_status"] = task.get("status", "")
        columns["task_ref_id"] = task.get("ref_id", "")
        columns["task_labels"] = classification.get("labels", [])

        created = task.get("created", "")
        if created:
            if isinstance(created, dict) and "$date" in created:
                action_date = created["$date"]
                created_date = timezone.datetime.fromtimestamp(
                    action_date / 1000, tz=timezone.get_current_timezone()
                )
                columns["call_date"] = created_date.strftime("%d-%m-%Y")
                columns["call_time"] = created_date.strftime("%I:%M:%S")

        callback_datetime = summary.get("callback_datetime", "")
        if callback_datetime:
            if isinstance(callback_datetime, dict) and "$date" in callback_datetime:
                action_date = callback_datetime["$date"]
                action_time = timezone.datetime.fromtimestamp(
                    action_date / 1000, tz=timezone.get_current_timezone()
                )
                columns["callback_datetime"] = action_time.strftime("%d-%m-%Y %I:%M:%S")

        # Add structured data fields
        structured_data = post_call_data.get("structured_data", None)
        if structured_data:
            try:
                structured_data_json = json.loads(structured_data)
                for key, value in structured_data_json.items():
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value)

                    columns[key] = value
            except Exception as e:
                print("Error parsing structured data:", e)

    return columns


def _extract_structured_data_keys(collection, query):
    """
    Extract all unique keys from structured_data across all matching documents.

    Args:
        collection: MongoDB collection
        query: MongoDB query dict

    Returns:
        set: Unique keys found in structured_data fields
    """
    print("Collecting column names from structured_data...")
    all_structured_keys = set()

    structured_cursor = (
        collection.find(
            {
                **query,
                "output.post_call_data.structured_data": {
                    "$exists": True,
                    "$nin": ["{}", {}, None],
                },
            },
            {"output.post_call_data.structured_data": 1, "_id": 0},
        )
        .batch_size(1000)
        .sort("created", -1)
    )

    for doc in structured_cursor:
        try:
            structured_data = (
                doc.get("output", {})
                .get("post_call_data", {})
                .get("structured_data", None)
            )
            if structured_data and isinstance(structured_data, str):
                all_structured_keys.update(json.loads(structured_data).keys())
        except Exception as e:
            print(f"Error parsing structured_data: {e}")
            continue

    return all_structured_keys


def _build_export_headers(structured_keys):
    """
    Build CSV headers and column keys from base columns and structured_data keys.

    Args:
        structured_keys: Set of structured_data field names

    Returns:
        tuple: (headers list, columns_keys list)
    """
    headers = list(TASKS_DATA.values())
    columns_keys = list(TASKS_DATA.keys())

    # Add structured_data columns dynamically (sorted for consistency)
    for key in sorted(structured_keys):
        headers.append(f"SR Data {machine_to_label(str(key))}")
        columns_keys.append(key)

    print(f"Total columns: {len(columns_keys)}")
    return headers, columns_keys


def _process_task_chunk(tasks, columns_keys, structured_keys):
    """
    Convert a chunk of tasks into a pandas DataFrame ready for CSV export.

    Args:
        tasks: List of task documents
        columns_keys: List of column names
        structured_keys: Set of structured_data field names

    Returns:
        pandas.DataFrame: Processed data ready for CSV export
    """
    import pandas as pd

    # Convert tasks to row dictionaries
    rows = [prepare_columns(task) for task in tasks]

    # Fill in missing structured_data columns with empty strings
    for row in rows:
        for key in structured_keys:
            if key not in row:
                row[key] = ""

    # Create DataFrame with proper column ordering
    return pd.DataFrame(rows, columns=columns_keys)


def _parse_datetime(value):
    from datetime import datetime

    if isinstance(value, datetime):
        return value

    if not value:
        raise ValueError("Empty datetime value")

    # Handle ISO-8601 with Z (UTC)
    if isinstance(value, str) and value.endswith("Z"):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return value


def _process_missing_fields(task):
    if not task.get("output", {}).get("duration"):
        output = task.get("output", {})
        if output.get("start_time") and output.get("end_time"):
            try:
                start_time = _parse_datetime(output["start_time"])
                end_time = _parse_datetime(output["end_time"])
                duration = (end_time - start_time).total_seconds()
                task["output"]["duration"] = duration

            except Exception as e:
                task["output"]["duration"] = "0"

    return task


def _generate_csv_chunks(
    collection, query, headers, columns_keys, structured_keys, chunk_size=5000
):
    """
    Generator that yields CSV data in chunks for streaming response.

    Args:
        collection: MongoDB collection
        query: MongoDB query dict
        headers: List of CSV header names
        columns_keys: List of column keys
        structured_keys: Set of structured_data field names
        chunk_size: Number of records to process per chunk

    Yields:
        str: CSV data chunks
    """
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers once
    writer.writerow(headers)
    yield output.getvalue()
    output.truncate(0)
    output.seek(0)

    # Stream data in chunks
    tasks_cursor = collection.find(query).batch_size(chunk_size).sort("created", -1)
    chunk = []
    total_processed = 0

    for task in tasks_cursor:
        task = _process_missing_fields(task)

        chunk.append(task)

        # Process when chunk is full
        if len(chunk) >= chunk_size:
            df_chunk = _process_task_chunk(chunk, columns_keys, structured_keys)

            # Write entire chunk to CSV at once (much faster than row-by-row)
            csv_buffer = io.StringIO()
            df_chunk.to_csv(csv_buffer, index=False, header=False)
            yield csv_buffer.getvalue()

            total_processed += len(chunk)
            print(f"Processed {total_processed} records...")

            chunk = []  # Clear for next batch

    # Process remaining records
    if chunk:
        df_chunk = _process_task_chunk(chunk, columns_keys, structured_keys)

        csv_buffer = io.StringIO()
        df_chunk.to_csv(csv_buffer, index=False, header=False)
        yield csv_buffer.getvalue()

        total_processed += len(chunk)
        print(f"Completed! Total records: {total_processed}")

    # Handle no data case
    if total_processed == 0:
        writer.writerow(["No tasks found"])
        yield output.getvalue()


def _prepare_filters(request):
    filters = {}
    runs = request.query_params.get("runs", None)
    if runs:
        filters["run_id"] = {"$in": runs.split(",")}

    agents = request.query_params.get("agents", None)
    if agents:
        filters["assignee"] = {"$in": agents.split(",")}

    user_token = request.query_params.get("user_token", None)
    if user_token:
        user = User.objects.filter(user_token=user_token).first()

        if user:
            filters["user"] = user.id

    document_id = request.query_params.get("document_id", None)
    if document_id:
        filters["ref_id"] = document_id

    contact_numbers = request.query_params.get("contact_numbers", None)
    if contact_numbers:
        filters["input.contact_number"] = {"$in": contact_numbers.split(",")}

    from_date = request.query_params.get("from_date", None)
    to_date = request.query_params.get("to_date", None)
    date_field = request.query_params.get("date_field", "created")
    if from_date and to_date:
        from_date = datetime.strptime(from_date, "%Y-%m-%d %H:%M:%S")

        # to_date = datetime.strptime(to_date, "%Y-%m-%d") + timezone.timedelta(hours=23, minutes=59, seconds=59)
        to_date = datetime.strptime(to_date, "%Y-%m-%d %H:%M:%S")

        filters[date_field] = {
            "$gte": from_date.replace(tzinfo=timezone.utc),
            "$lte": to_date.replace(tzinfo=timezone.utc),
        }

    return filters


def export_space_tasks(space, request, chunk_size=5000):
    """
    Export all tasks for a space as a streaming CSV file.

    This function efficiently exports large datasets by:
    - Processing data in configurable chunks (default 5000 records)
    - Streaming response to avoid memory issues
    - Dynamically discovering all structured_data columns
    - Using pandas for fast CSV generation

    Args:
        space: Space model instance
        chunk_size: Number of records to process per chunk (default: 5000)

    Returns:
        StreamingHttpResponse: CSV file download response

    Memory Complexity: O(chunk_size) - constant memory regardless of total dataset size
    Time Complexity: O(n) where n is total number of tasks
    """
    from django.http import StreamingHttpResponse

    collection_name = "tasks"
    collection = MongoDBQueryManager.get_collection(collection_name)
    query = {
        "space_id": str(space.id),
        "output": {"$ne": {}, "$exists": True},
        **_prepare_filters(request),
    }

    # print("Export Query:", query)

    # Step 1: Discover all unique structured_data column names
    structured_keys = _extract_structured_data_keys(collection, query)

    # Step 2: Build complete headers and column keys
    headers, columns_keys = _build_export_headers(structured_keys)

    # Step 3: Generate CSV in chunks using streaming generator
    csv_generator = _generate_csv_chunks(
        collection, query, headers, columns_keys, structured_keys, chunk_size
    )

    # Step 4: Create streaming HTTP response
    response = StreamingHttpResponse(csv_generator, content_type="text/csv")
    now = timezone.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="space_tasks_{now}.csv"'

    return response
