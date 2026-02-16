import sys

from prefect import flow, task
from datetime import datetime ,timedelta ,timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
import boto3
import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
import json

from super_services.db.services.models.task import TaskModel

bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
prefix = os.getenv("S3_FILE_PATH", "")  # Set default or add to .env
region = os.getenv("AWS_DEFAULT_REGION")
s3 = boto3.client("s3")
STATE_FILE = os.getenv("RECORDING_CRON","")

def normalize_number(num):
    if len(num) == 12:
        return "+"+num
    else:
        return num


# @task(name="get_last_execution_time")
def get_last_execution_time() -> datetime | None:
    if not os.path.exists(STATE_FILE):
        with open(STATE_FILE, "w") as f:
            json.dump({"recording_update": None}, f)
        return None

    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            value = data.get("recording_update")

            if value:
                # Convert "Z" to "+00:00" so datetime.fromisoformat() works
                value = value.replace("Z", "+00:00")
                return datetime.fromisoformat(value)

            return None

    except (json.JSONDecodeError, KeyError, ValueError):
        with open(STATE_FILE, "w") as f:
            json.dump({"recording_update": None}, f)
        return None


# @task(name="get_number_map")
def get_number_map(recordings) :
    call_map ={}
    url_pre = f"https://{bucket}.s3.{region}.amazonaws.com/"

    for record in recordings:
        parts = record.split("_")
        raw_source = parts[1]
        raw_dest = parts[2]

        if len(parts[0].split("/"))>5:
            continue

        time = parts[0].split("/")[4]

        dt = datetime.strptime(time, "%Y-%m-%d-%H-%M-%S")

        source = raw_source.lstrip("0")
        destination = raw_dest.lstrip("0")

        call_map[record]= {
            "is_num":True,
            "url":url_pre+record,
            "source":source[-10:],
            "destination": destination[-10:],
            "time":dt
        }


    print(f"Found {len(call_map)} recordings ")
    return  call_map

# @task(name="update_last_execution_time")
def update_last_execution_time(new_time: datetime):
    print(f"{STATE_FILE} updating cron run time")

    # Convert incoming datetime to UTC Zulu ISO format
    new_time_utc = new_time.astimezone(timezone.utc)
    iso_z_format = new_time_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # Save formatted string to JSON
    with open(STATE_FILE, "w") as f:
        json.dump({"recording_update": iso_z_format}, f)

    return iso_z_format


# @task(name="update_map_task")
def update_map_task(numbers,last_execution_time,current_execution_time):

    url_pre =f"https://{bucket}.s3.{region}.amazonaws.com/"
    tasks = list(
        TaskModel._get_collection().find(
            {"modified": {"$gt": last_execution_time, "$lt": current_execution_time}},
            sort=[("modified", -1)])
    )

    # Debug counters - per recording
    no_phone_match = 0
    time_diff_too_large = 0
    already_has_recording = 0
    updated_count = 0
    total_tasks = len(tasks)

    print(f"{len(tasks)} tasks ")
    for record in numbers.values():
        match_status = "no_match"  # Track best match status for this recording

        # First pass: find all matching tasks (by phone number)
        matching_tasks = []
        for task in tasks:
            destination = task.get("input",{}).get("contact_number","")[-10:] if task.get("input",{}).get("contact_number") else ""

            if not destination:
                destination = task.get("input",{}).get("number","")[-10:] if task.get("input",{}).get("number") else ""

            source = task.get("output",{}).get("assistant_number","")[-10:] if task.get("output",{}).get("assistant_number") else ""

            # Match on both src+dest, or fallback to dest only if src is empty
            src_dest_match = destination == record.get("destination") and source == record.get("source")
            dest_only_match = destination == record.get("destination") and (not source or not record.get("source"))

            if src_dest_match or dest_only_match:
                # Both times appear to be in the same timezone - compare directly
                record_time = record.get("time")
                task_modified = task["modified"]

                # Strip timezone info for naive comparison
                if record_time.tzinfo is not None:
                    record_time = record_time.replace(tzinfo=None)
                if task_modified.tzinfo is not None:
                    task_modified = task_modified.replace(tzinfo=None)

                diff = abs(task_modified - record_time)
                diff_seconds = diff.total_seconds()

                matching_tasks.append({
                    "task": task,
                    "diff_seconds": diff_seconds,
                    "src_dest_match": src_dest_match
                })

        # Filter out tasks that already have recordings
        eligible_tasks = [m for m in matching_tasks if not m["task"].get("output",{}).get("recording_url")]

        if not matching_tasks:
            match_status = "no_match"
        elif not eligible_tasks:
            match_status = "already_has_recording"
        else:
            # Sort by time difference (nearest first)
            eligible_tasks.sort(key=lambda x: x["diff_seconds"])
            best_match = eligible_tasks[0]

            # If only one eligible task, allow up to 90 minutes (5400s)
            # If multiple eligible tasks, use nearest one within 5 minutes (300s)
            if len(eligible_tasks) == 1:
                time_threshold = 5400  # 90 minutes for single match
            else:
                time_threshold = 300   # 5 minutes for multiple matches

            if best_match["diff_seconds"] <= time_threshold:
                task = best_match["task"]
                update_data = task
                output_data = task.get("output")
                output_data['recording_url'] = record.get("url")
                update_data["output"] = output_data
                TaskModel.update_one({"task_id": task.get("task_id")}, update_data)
                match_type = "src+dest" if best_match["src_dest_match"] else "dest_only"
                threshold_type = "single_90m" if len(eligible_tasks) == 1 else "nearest_5m"
                print(f"updated task with id : - {task.get('task_id')} ({match_type}, {threshold_type}, diff={best_match['diff_seconds']:.0f}s)")
                updated_count += 1
                tasks.remove(task)
                match_status = "updated"
            else:
                match_status = "time_diff_too_large"

        # Count based on final status for this recording
        if match_status == "no_match":
            no_phone_match += 1
        elif match_status == "time_diff_too_large":
            time_diff_too_large += 1
        elif match_status == "already_has_recording":
            already_has_recording += 1

    print(f"\n--- Match Statistics ---")
    print(f"Total recordings: {len(numbers)}")
    print(f"Total tasks in range: {total_tasks}")
    print(f"Updated: {updated_count}")
    print(f"No phone match (src+dest): {no_phone_match}")
    print(f"Phone matched but time diff > 300s: {time_diff_too_large}")
    print(f"Phone+time matched but already has recording: {already_has_recording}")

    # Debug: Show sample unmatched recordings and tasks
    print(f"\n--- Sample Unmatched Recordings (first 5) ---")
    sample_count = 0
    for record in numbers.values():
        if sample_count >= 5:
            break
        # Check if this recording has no match (using same logic as main loop)
        has_match = False
        for task in tasks:
            dest = task.get("input",{}).get("contact_number","")[-10:] if task.get("input",{}).get("contact_number") else ""
            if not dest:
                dest = task.get("input",{}).get("number","")[-10:] if task.get("input",{}).get("number") else ""
            src = task.get("output",{}).get("assistant_number","")[-10:] if task.get("output",{}).get("assistant_number") else ""
            # Same fallback logic: src+dest match OR dest-only if src is empty
            src_dest_match = dest == record.get("destination") and src == record.get("source")
            dest_only_match = dest == record.get("destination") and (not src or not record.get("source"))
            if src_dest_match or dest_only_match:
                has_match = True
                break
        if not has_match:
            print(f"  Recording: src={record.get('source')}, dest={record.get('destination')}, time={record.get('time')}")
            sample_count += 1

    print(f"\n--- Sample Tasks (first 5) ---")
    for i, task in enumerate(tasks[:5]):
        dest = task.get("input",{}).get("contact_number","")[-10:] if task.get("input",{}).get("contact_number") else ""
        if not dest:
            dest = task.get("input",{}).get("number","")[-10:] if task.get("input",{}).get("number") else ""
        src = task.get("output",{}).get("assistant_number","")[-10:] if task.get("output",{}).get("assistant_number") else ""
        print(f"  Task {i+1}: src={src}, dest={dest}, modified={task.get('modified')}")

    # Debug: Show time diff for a few matching but time-failed cases
    print(f"\n--- Sample Time Diff Issues (first 3) ---")
    sample_count = 0
    for record in numbers.values():
        if sample_count >= 3:
            break
        for task in tasks:
            dest = task.get("input",{}).get("contact_number","")[-10:] if task.get("input",{}).get("contact_number") else ""
            if not dest:
                dest = task.get("input",{}).get("number","")[-10:] if task.get("input",{}).get("number") else ""
            src = task.get("output",{}).get("assistant_number","")[-10:] if task.get("output",{}).get("assistant_number") else ""
            src_dest_match = dest == record.get("destination") and src == record.get("source")
            dest_only_match = dest == record.get("destination") and (not src or not record.get("source"))
            if src_dest_match or dest_only_match:
                record_time = record.get("time")
                task_modified = task["modified"]
                if record_time.tzinfo is not None:
                    record_time = record_time.replace(tzinfo=None)
                if task_modified.tzinfo is not None:
                    task_modified = task_modified.replace(tzinfo=None)
                diff = abs(task_modified - record_time)
                diff_seconds = diff.total_seconds()
                if diff_seconds >= 300 and not task.get("output",{}).get("recording_url"):
                    print(f"  Recording: dest={record.get('destination')}, time={record.get('time')} (raw)")
                    print(f"  Task: dest={dest}, modified={task['modified']} (raw)")
                    print(f"  Diff: {diff_seconds:.0f}s ({diff_seconds/60:.1f}min)")
                    print()
                    sample_count += 1
                    break





def search_recordings(search_string: str):
    """Search S3 recordings by phone number or any string in filename."""
    paginator = s3.get_paginator("list_objects_v2")
    found_files = []

    print(f"Searching for '{search_string}' in recordings...")

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if search_string in obj['Key'] and obj['Key'].endswith(".wav"):
                found_files.append(obj['Key'])

    print(f"\nFound {len(found_files)} files matching '{search_string}':\n")
    for f in found_files:
        print(f"  {f}")

    return found_files


# @flow(name="recordings_cron",log_prints=True)
def recordings_cron():
    """List all recording file names from S3."""
    paginator = s3.get_paginator("list_objects_v2")

    all_recordings = []

    last_execution_time = get_last_execution_time()
    if not last_execution_time:
        last_execution_time = datetime.now(timezone.utc) - timedelta(days=10)

    current_execution_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix+f"/{datetime.now().year}"):
        for obj in page.get("Contents", []):
            if last_execution_time < obj['LastModified'] < current_execution_time and obj['Key'].endswith(".wav"):
                all_recordings.append(obj['Key'])


    print(f"Found {len(all_recordings)} files")

    numbers_map = get_number_map(all_recordings)

    update_map_task(numbers_map,last_execution_time,current_execution_time)
    update_last_execution_time(current_execution_time)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "search":
        # Usage: python recordings_cron.py search 66540010005
        search_string = sys.argv[2] if len(sys.argv) > 2 else ""
        if search_string:
            search_recordings(search_string)
        else:
            print("Usage: python recordings_cron.py search <phone_number>")
    else:
        recordings_cron()