import csv
import os
from typing import List, Optional, Dict
from datetime import datetime
import dspy

from super.core.voice.workflows.custom_call_analysis import CallAnalyzer
from super_services.db.services.models.task import TaskModel
from super_services.db.services.schemas.task import TaskStatusEnum


def update_csv_with_db_data(
        input_csv_path: str,
        output_csv_path: str = None
) -> Dict:
    """
    Read CSV file and update Contact Number and Transcript from database.

    This function iterates over rows in the CSV file, fetches task data from
    the database using task_id and run_id, and updates the Contact Number
    and Transcript columns with the actual data from DB.

    Args:
        input_csv_path: Path to the input CSV file
        output_csv_path: Path where updated CSV will be saved (defaults to input_csv_path with '_updated' suffix)

    Returns:
        Dictionary with processing statistics
    """

    # Default output path if not provided
    if output_csv_path is None:
        base_name = input_csv_path.rsplit('.', 1)[0]
        output_csv_path = f"{base_name}_updated.csv"

    # Statistics
    stats = {
        "total_rows": 0,
        "updated": 0,
        "not_found": 0,
        "errors": 0,
        "contact_updated": 0,
        "transcript_updated": 0
    }

    # Read the input CSV
    rows_to_write = []

    print(f"Reading CSV from: {input_csv_path}")

    with open(input_csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames

        # Add Transcript column if it doesn't exist
        if 'Transcript' not in headers:
            headers = list(headers) + ['Transcript']

        for row in reader:
            stats["total_rows"] += 1

            run_id = row.get('Run ID', '').strip()
            task_id = row.get('Task ID', '').strip()

            if not run_id or not task_id:
                print(f"⚠ Row {stats['total_rows']}: Missing Run ID or Task ID, skipping")
                rows_to_write.append(row)
                continue

            try:
                # Fetch task from database
                query = {
                    "task_id": task_id,
                    "run_id": run_id
                }

                tasks = list(TaskModel.find(**query))

                if not tasks:
                    print(f"✗ Row {stats['total_rows']}: Task not found - Task ID: {task_id}, Run ID: {run_id}")
                    stats["not_found"] += 1
                    rows_to_write.append(row)
                    continue

                task = tasks[0].dict()
                updated = False

                # Update Contact Number
                contact_number = task.get("input", {}).get("contact_number", "")
                if contact_number:
                    old_contact = row.get('Contact Number', '')
                    row['Contact Number'] = contact_number
                    if old_contact != contact_number:
                        stats["contact_updated"] += 1
                        updated = True

                # Update Transcript
                output = task.get("output", {})
                transcript = output.get("transcript", "")
                if transcript:
                    old_transcript = row.get('Transcript', '')
                    row['Transcript'] = transcript
                    if old_transcript != transcript:
                        stats["transcript_updated"] += 1
                        updated = True

                # Update customer name if available
                customer_name = task.get("input", {}).get("name", "")
                if customer_name and not row.get('Customer Name'):
                    row['Customer Name'] = customer_name
                    updated = True

                # Update call date and time if missing
                if row.get('Call Date') in ['N/A', 'NULL', ''] or row.get('Call Time') in ['N/A', 'NULL', '']:
                    start_time = output.get("start_time", "")
                    if start_time:
                        try:
                            dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                            row['Call Date'] = dt.strftime("%Y-%m-%d")
                            row['Call Time'] = dt.strftime("%I:%M %p")
                            updated = True
                        except Exception:
                            pass

                # Update call duration if missing or 0
                if row.get('Call Duration (sec)') in ['0', '0.0', '']:
                    duration_raw = output.get("duration", 0)
                    try:
                        duration = float(duration_raw) if duration_raw else 0
                        if duration > 0:
                            row['Call Duration (sec)'] = str(round(duration, 2))
                            updated = True
                    except (TypeError, ValueError):
                        pass

                # Update Transcript if missing
                # if not row.get('Transcript'):
                #     recording_url = output.get("recording_url", "")
                #     if recording_url:
                #         row['Transcript'] = recording_url
                #         updated = True

                if updated:
                    stats["updated"] += 1
                    print(f"✓ Row {stats['total_rows']}: Updated - {row.get('Customer Name', 'N/A')} ({task_id})")
                else:
                    print(f"→ Row {stats['total_rows']}: No updates needed - {row.get('Customer Name', 'N/A')}")

                rows_to_write.append(row)

            except Exception as e:
                stats["errors"] += 1
                print(f"✗ Row {stats['total_rows']}: Error - {str(e)}")
                rows_to_write.append(row)

    # Write updated CSV
    print(f"\nWriting updated CSV to: {output_csv_path}")

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_to_write)

    # Print summary
    print("\n" + "=" * 60)
    print("UPDATE COMPLETE")
    print("=" * 60)
    print(f"Total Rows Processed: {stats['total_rows']}")
    print(f"Rows Updated: {stats['updated']}")
    print(f"Tasks Not Found: {stats['not_found']}")
    print(f"Errors: {stats['errors']}")
    print(f"Contact Numbers Updated: {stats['contact_updated']}")
    print(f"Transcripts Updated: {stats['transcript_updated']}")
    print(f"\nUpdated CSV saved to: {output_csv_path}")
    print("=" * 60)

    return stats


def analyze_and_export_calls(
        run_ids: List[str],
        output_csv_path: str = "call_analysis_report.csv",
        space_id: Optional[str] = None,
        task_id: Optional[str] = None
) -> Dict:
    """
    Analyze call tasks for given run IDs and export results to CSV.

    Args:
        run_ids: List of run IDs to process
        output_csv_path: Path where CSV file will be saved
        space_id: Optional space ID filter
        task_id: Optional task ID filter

    Returns:
        Dictionary with processing statistics
    """

    # Initialize DSPy with language model
    lm = dspy.LM('openai/gpt-4o-mini', api_key=os.getenv("OPENAI_API_KEY"))
    dspy.configure(lm=lm, skip_logprobs=True)

    # Initialize the call analyzer
    analyzer = CallAnalyzer()

    # Statistics
    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "by_status": {}
    }

    # CSV Headers
    csv_headers = [
        "Run ID",
        "Task ID",
        "Contact Number",
        "Customer Name",
        "Call Date",
        "Call Time",
        "Call Duration (sec)",
        "Call Status",
        "Summary",
        "Child Name",
        "Child Grade",
        "Callback Date",
        "Callback Time",
        "Transcript",
        "Task Status",
        "Document ID"
    ]

    # Open CSV file for writing
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()

        # Process each run_id
        for run_id in run_ids:
            print(f"\nProcessing run_id: {run_id}")

            # Build query
            query = {
                "execution_type": "call",
                "run_id": run_id,
                "status": TaskStatusEnum.completed
            }

            if space_id:
                query["space_id"] = space_id
            if task_id:
                query["task_id"] = task_id

            # Fetch tasks
            tasks = list(TaskModel.find(**query))
            print(f"Found {len(tasks)} completed call tasks for run_id: {run_id}")

            # Process each task
            for task in tasks:
                task = task.dict()
                stats["total_processed"] += 1

                try:
                    # Extract basic information
                    contact_number = task.get("input", {}).get("contact_number", "N/A")
                    customer_name = task.get("input", {}).get("name", "N/A")

                    # Extract output information
                    output = task.get("output", {})
                    transcript = output.get("transcript", str(output))
                    start_time = output.get("start_time", "")
                    # Ensure duration is numeric (handle string or None values)
                    duration_raw = output.get("duration", 0)
                    try:
                        duration = float(duration_raw) if duration_raw else 0
                    except (TypeError, ValueError):
                        duration = 0
                    recording_url = output.get("recording_url", "")

                    # Parse call date and time
                    call_date = "N/A"
                    call_time = "N/A"
                    if start_time:
                        try:
                            dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                            call_date = dt.strftime("%Y-%m-%d")
                            call_time = dt.strftime("%I:%M %p")
                        except:
                            call_date = start_time.split()[0] if " " in start_time else start_time
                            call_time = start_time.split()[1] if " " in start_time else ""

                    # Analyze call using DSPy
                    if transcript:
                        # pass
                        analysis = analyzer(call_transcript=transcript)

                        call_status = analysis.status
                        summary = analysis.summary
                        child_name = analysis.child_name if analysis.child_name != "N/A" else ""
                        child_grade = analysis.child_grade if analysis.child_grade != "N/A" else ""
                        callback_date = analysis.callback_date if analysis.callback_date != "N/A" else ""
                        callback_time = analysis.callback_time if analysis.callback_time != "N/A" else ""

                        # Update statistics
                        stats["by_status"][call_status] = stats["by_status"].get(call_status, 0) + 1
                        stats["successful"] += 1
                    else:
                        # No transcript available
                        call_status = "No Transcript"
                        summary = "No transcript available for analysis"
                        child_name = ""
                        child_grade = ""
                        callback_date = ""
                        callback_time = ""
                        transcript = ""
                        stats["by_status"]["No Transcript"] = stats["by_status"].get("No Transcript", 0) + 1

                    # Write row to CSV
                    row = {
                        "Run ID": run_id,
                        "Task ID": task.get("task_id", "N/A"),
                        "Contact Number": contact_number,
                        "Customer Name": customer_name,
                        "Call Date": call_date,
                        "Call Time": call_time,
                        "Call Duration (sec)": round(duration, 2) if duration else 0,
                        "Call Status": call_status,
                        "Summary": summary,
                        "Child Name": child_name,
                        "Child Grade": child_grade,
                        "Callback Date": callback_date,
                        "Callback Time": callback_time,
                        "Transcript": transcript,
                        "Task Status": task.get("status", "N/A"),
                        "Document ID": task.get("ref_id", "N/A")
                    }

                    writer.writerow(row)

                    print(f"✓ Processed: {customer_name} ({contact_number}) - Status: {call_status}")

                except Exception as e:
                    stats["failed"] += 1
                    print(f"✗ Error processing task {task.get('_id')}: {str(e)}")

                    # Write error row
                    error_row = {
                        "Run ID": run_id,
                        "Task ID": task.get("task_id", "N/A"),
                        "Contact Number": task.get("input", {}).get("contact_number", "N/A"),
                        "Customer Name": task.get("input", {}).get("name", "N/A"),
                        "Call Date": "ERROR",
                        "Call Time": "ERROR",
                        "Call Duration (sec)": 0,
                        "Call Status": "Error",
                        "Summary": f"Error: {str(e)}",
                        "Child Name": "",
                        "Child Grade": "",
                        "Callback Date": "",
                        "Callback Time": "",
                        "Transcript": "",
                        "Task Status": task.get("status", "N/A"),
                        "Document ID": task.get("ref_id", "N/A")
                    }
                    writer.writerow(error_row)

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Total Processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"\nCSV saved to: {output_csv_path}")
    print("\nBreakdown by Status:")
    for status, count in sorted(stats['by_status'].items()):
        print(f"  {status}: {count}")
    print("=" * 60)

    return stats


# Alternative function with enhanced filtering and options
def analyze_and_export_calls_advanced(
        run_ids: List[str],
        output_csv_path: str = "call_analysis_report.csv",
        space_id: Optional[str] = None,
        task_id: Optional[str] = None,
        include_transcript: bool = False,
        filter_by_status: Optional[List[str]] = None
) -> Dict:
    """
    Advanced version with more options.

    Args:
        run_ids: List of run IDs to process
        output_csv_path: Path where CSV file will be saved
        space_id: Optional space ID filter
        task_id: Optional task ID filter
        include_transcript: Include full transcript in CSV
        filter_by_status: Only export specific call statuses (e.g., ['Registered', 'Call Back'])

    Returns:
        Dictionary with processing statistics and file path
    """

    # Initialize DSPy with language model
    lm = dspy.LM('openai/gpt-4o-mini', api_key=os.getenv("OPENAI_API_KEY"))
    dspy.configure(lm=lm, skip_logprobs=True)

    analyzer = CallAnalyzer()

    stats = {
        "total_processed": 0,
        "successful": 0,
        "failed": 0,
        "filtered_out": 0,
        "by_status": {},
        "output_file": output_csv_path
    }

    # CSV Headers
    csv_headers = [
        "Run ID",
        "Task ID",
        "Contact Number",
        "Customer Name",
        "Call Date",
        "Call Time",
        "Call Duration (sec)",
        "Call Status",
        "Summary",
        "Child Name",
        "Child Grade",
        "Callback Date",
        "Callback Time",
        "Transcript",
        "Task Status",
        "Document ID"
    ]

    if include_transcript:
        csv_headers.append("Transcript")

    rows_to_write = []

    # Process each run_id
    for run_id in run_ids:
        print(f"\nProcessing run_id: {run_id}")

        query = {
            "execution_type": "call",
            "run_id": run_id,
            "status": TaskStatusEnum.completed
        }

        if space_id:
            query["space_id"] = space_id
        if task_id:
            query["task_id"] = task_id

        tasks = list(TaskModel.find(**query))
        print(f"Found {len(tasks)} completed call tasks")

        for task in tasks:
            stats["total_processed"] += 1

            try:
                contact_number = task.get("input", {}).get("contact_number", "N/A")
                customer_name = task.get("input", {}).get("name", "N/A")

                output = task.get("output", {})
                transcript = output.get("transcript", "")
                start_time = output.get("start_time", "")
                # Ensure duration is numeric (handle string or None values)
                duration_raw = output.get("duration", 0)
                try:
                    duration = float(duration_raw) if duration_raw else 0
                except (TypeError, ValueError):
                    duration = 0
                recording_url = output.get("recording_url", "")

                call_date = "N/A"
                call_time = "N/A"
                if start_time:
                    try:
                        dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                        call_date = dt.strftime("%Y-%m-%d")
                        call_time = dt.strftime("%I:%M %p")
                    except:
                        pass

                if transcript:
                    analysis = analyzer(call_transcript=transcript)

                    call_status = analysis.status

                    # Filter by status if specified
                    if filter_by_status and call_status not in filter_by_status:
                        stats["filtered_out"] += 1
                        continue

                    summary = analysis.summary
                    child_name = analysis.child_name if analysis.child_name != "N/A" else ""
                    child_grade = analysis.child_grade if analysis.child_grade != "N/A" else ""
                    callback_date = analysis.callback_date if analysis.callback_date != "N/A" else ""
                    callback_time = analysis.callback_time if analysis.callback_time != "N/A" else ""

                    stats["by_status"][call_status] = stats["by_status"].get(call_status, 0) + 1
                    stats["successful"] += 1
                else:
                    call_status = "No Transcript"
                    summary = "No transcript available"
                    child_name = ""
                    child_grade = ""
                    callback_date = ""
                    callback_time = ""

                row = {
                    "Run ID": run_id,
                    "Task ID": task.get("task_id", "N/A"),
                    "Contact Number": contact_number,
                    "Customer Name": customer_name,
                    "Call Date": call_date,
                    "Call Time": call_time,
                    "Call Duration (sec)": round(duration, 2) if duration else 0,
                    "Call Status": call_status,
                    "Summary": summary,
                    "Child Name": child_name,
                    "Child Grade": child_grade,
                    "Callback Date": callback_date,
                    "Callback Time": callback_time,
                    "Transcript": recording_url,
                    "Task Status": task.get("status", "N/A"),
                    "Document ID": task.get("ref_id", "N/A")
                }

                if include_transcript:
                    row["Transcript"] = transcript

                rows_to_write.append(row)
                print(f"✓ {customer_name} - {call_status}")

            except Exception as e:
                stats["failed"] += 1
                print(f"✗ Error: {str(e)}")

    # Write all rows to CSV
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(rows_to_write)

    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Total Processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Filtered Out: {stats['filtered_out']}")
    print(f"\nRows in CSV: {len(rows_to_write)}")
    print(f"CSV saved to: {output_csv_path}")
    print("\nBreakdown by Status:")
    for status, count in sorted(stats['by_status'].items()):
        print(f"  {status}: {count}")
    print("=" * 60)

    return stats