import sys

from datetime import datetime ,timedelta ,timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
import boto3
import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.insert(0, PROJECT_ROOT)
load_dotenv()
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
import json

from super_services.db.services.models.task import TaskModel

bucket = os.getenv("AWS_STORAGE_BUCKET_NAME")
prefix = os.getenv("VAPI_S3_FILE_PATH", "")  # Set default or add to .env
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
        parts = record.split("/")

        call_map[record]= {
            "is_num":True,
            "url":url_pre+record,
            "call_id":parts[3][:36],
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
def update_map_task(call_data,last_execution_time,current_execution_time):

    url_pre =f"https://{bucket}.s3.{region}.amazonaws.com/"
    updated_records = 0
    skipped_records = 0
    alredy_have_recording=0

    for call in call_data.keys():
        print(f"updating recording for {call_data[call].get('call_id')}")
        record=call_data[call]
        tasks = list(
            TaskModel._get_collection().find(
                {"output.call_id":record.get('call_id'),"modified": {"$gt": last_execution_time, "$lt": current_execution_time}},
                sort=[("modified", -1)])
        )

        if tasks:
            task=tasks[0]
            if not task.get("output",{}).get("recording_url"):
                update_data = task
                output_data = task.get("output")
                output_data['recording_url'] = record.get("url")
                update_data["output"] = output_data
                TaskModel.update_one({"task_id": task.get("task_id")}, update_data)
                updated_records+=1
                continue
            else:
                alredy_have_recording+=1
                continue

        skipped_records+=1

    print(f"skipped {skipped_records} records as dont have specific tasks")
    print(f"already have recording for : {alredy_have_recording} tasks")
    print(f"updated {updated_records} tasks with recordings")




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
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if last_execution_time < obj['LastModified'] < current_execution_time and obj['Key'].endswith(".wav"):
                all_recordings.append(obj['Key'])


    print(f"Found {len(all_recordings)} files")

    call_data = get_number_map(all_recordings)
    #
    update_map_task(call_data,last_execution_time,current_execution_time)
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