import os
import asyncio
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from super.core.logging.logging import print_log
from super_services.db.services.models.task import TaskModel
# from super_services.db.services.schemas.task import TaskStatusEnum
from super_services.libs.core.jsondecoder import convertFromMongo
from super_services.libs.core.db import executeQuery

API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://0.0.0.0:9116/api/v1").rstrip("/")


def get_token_from_space_id(space_id: str) -> Optional[str]:
    try:
        query = """
        SELECT token FROM space_space WHERE id = %(space_id)s;
        """
        params = {"space_id": space_id}
        # executeQuery returns a single dict by default (fetchone)
        result = executeQuery(query, params)

        if result and isinstance(result, dict):
            token = result.get("token")
            print_log(f"Fetched token for space_id {space_id}: {token}", "profile_update_token_fetch")
            return token
        else:
            print_log(f"No token found for space_id {space_id}", "profile_update_token_not_found")
            return None
    except Exception as e:
        print_log(f"Error fetching token for space_id {space_id}: {str(e)}", "profile_update_token_error")
        return None


class ProfileUpdateService:
    def __init__(self, document_id: str, token: str, collection_ref: str = None):
        self.document_id = document_id
        self.token = token
        self.collection_ref = collection_ref
        self.api_url = f"{API_SERVICE_URL}/store/collection-doc-data/{token}/{document_id}"

    def fetch_tasks_by_document(self) -> List:
        try:
            query = {"ref_id": self.document_id}
            # Use _get_collection().find() for direct pymongo query (avoids OID validation issues)
            tasks_cursor = TaskModel._get_collection().find(query, sort=[("_id", -1)])
            tasks = [convertFromMongo(task) for task in tasks_cursor]
            print_log(f"Found {len(tasks)} tasks for document {self.document_id}", "profile_update_tasks_found")
            return tasks
        except Exception as e:
            print_log(f"Error fetching tasks for document {self.document_id}: {str(e)}", "profile_update_fetch_error")
            return []

    def calculate_profile_analytics(self, tasks: List) -> Dict:
        total_calls = len(tasks)
        connected_calls = 0
        total_duration = 0
        call_hours = []
        last_connected = None

        for task in tasks:
            # Tasks are now dicts (from convertFromMongo)
            output = task.get("output", {}) if isinstance(task, dict) else {}
            status = task.get("status") if isinstance(task, dict) else None

            # Check if call was connected (completed with transcript)
            transcript = output.get("transcript", [])
            is_connected = (
                status == "completed" and
                transcript and
                len(transcript) > 0
            )

            if is_connected:
                connected_calls += 1

                output_data = output.get("data", {})

                # Get duration - check multiple sources
                duration_seconds = 0

                # Option 1: Direct duration field
                if output.get("duration"):
                    try:
                        duration_seconds = float(output.get("duration"))
                    except (ValueError, TypeError):
                        pass

                # Option 2: Calculate from timestamps if duration not found
                if duration_seconds == 0:
                    started_at = (
                        output_data.get("startedAt") or
                        output.get("start_time")
                    )
                    ended_at = (
                        output_data.get("endedAt") or
                        output.get("end_time")
                    )

                    if started_at and ended_at:
                        try:
                            if isinstance(started_at, str):
                                start_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                            else:
                                start_dt = started_at

                            if isinstance(ended_at, str):
                                end_dt = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
                            else:
                                end_dt = ended_at

                            duration_seconds = (end_dt - start_dt).total_seconds()
                        except (ValueError, TypeError) as e:
                            print_log(f"Error calculating duration: {e}", "profile_update_duration_error")

                if duration_seconds > 0:
                    total_duration += duration_seconds

                # Track call time for preferred_time calculation
                start_time = (
                    output_data.get("startedAt") or
                    output.get("start_time") or
                    task.get("updated_at") or
                    task.get("created_at") or
                    task.get("modified") or
                    task.get("created")
                )
                if start_time:
                    try:
                        if isinstance(start_time, str):
                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        else:
                            dt = start_time
                        call_hours.append(dt.hour)
                    except (ValueError, TypeError):
                        pass

                # Track last connected time
                end_time = (
                    output_data.get("endedAt") or
                    output.get("end_time") or
                    task.get("modified") or
                    task.get("created")
                )
                if end_time:
                    try:
                        if isinstance(end_time, str):
                            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        else:
                            end_dt = end_time

                        if last_connected is None or end_dt > last_connected:
                            last_connected = end_dt
                    except (ValueError, TypeError):
                        pass

        # Calculate averages
        avg_call_duration = round(total_duration / connected_calls, 2) if connected_calls > 0 else 0
        response_rate = round((connected_calls / total_calls) * 100, 2) if total_calls > 0 else 0

        # Calculate preferred time (most common hour range)
        preferred_time = self._calculate_preferred_time(call_hours)

        # Format last_connected
        last_connected_str = last_connected.isoformat() if last_connected else None

        return {
            "avg_call_duration": f"{avg_call_duration}s",
            "response_rate": f"{response_rate}%",
            "preferred_time": preferred_time,
            "total_calls": total_calls,
            "connected_calls": connected_calls,
            "last_connected": last_connected_str,
            "sentiment": None  # Will be populated later in build_overview
        }

    def _calculate_preferred_time(self, call_hours: List[int]) -> str:
        if not call_hours:
            return "None"

        # Define time slots
        time_slots = {
            "Early Morning (6AM-9AM)": range(6, 9),
            "Morning (9AM-12PM)": range(9, 12),
            "Afternoon (12PM-3PM)": range(12, 15),
            "Late Afternoon (3PM-6PM)": range(15, 18),
            "Evening (6PM-9PM)": range(18, 21),
            "Night (9PM-12AM)": range(21, 24),
        }

        # Count calls in each slot
        slot_counts = {slot: 0 for slot in time_slots}
        for hour in call_hours:
            for slot_name, hour_range in time_slots.items():
                if hour in hour_range:
                    slot_counts[slot_name] += 1
                    break

        # Find most common slot
        if max(slot_counts.values()) == 0:
            return "None"

        preferred_slot = max(slot_counts, key=slot_counts.get)
        return preferred_slot

    def determine_profile_status(self, tasks: List, analytics: Dict) -> str:
        total_calls = analytics.get("total_calls", 0)
        connected_calls = analytics.get("connected_calls", 0)
        last_connected = analytics.get("last_connected")

        if total_calls == 0:
            return "Not Connected"

        if connected_calls == 0:
            return "Not Connected"

        # Check recency of last connected call
        days_since_last_call = None
        if last_connected:
            try:
                if isinstance(last_connected, str):
                    last_dt = datetime.fromisoformat(last_connected.replace('Z', '+00:00'))
                else:
                    last_dt = last_connected

                # Remove timezone for comparison
                last_dt = last_dt.replace(tzinfo=None)
                days_since_last_call = (datetime.utcnow() - last_dt).days
            except (ValueError, TypeError):
                pass

        response_rate = float(analytics.get("response_rate", "0%").replace("%", ""))

        # Active: Recent call (<=30 days) or good response rate with recent activity
        if days_since_last_call is not None and days_since_last_call <= 30:
            return "Active"

        if response_rate >= 50 and days_since_last_call is not None and days_since_last_call <= 60:
            return "Active"

        # Lost: Had calls but no recent activity (>60 days)
        if days_since_last_call is not None and days_since_last_call > 60:
            return "Lost"

        # Ghosted: Multiple attempts with low response
        if total_calls >= 3 and response_rate < 30:
            return "Ghosted"

        # Default to Active if none of the above
        return "Active"

    def analyze_sentiment(self, tasks: List) -> str:
        positive_indicators = ["interested", "call back", "send details", "yes", "sure", "okay"]
        negative_indicators = ["not interested", "no", "don't call", "stop", "remove", "unsubscribe"]

        positive_count = 0
        negative_count = 0
        total_analyzed = 0

        for task in tasks:
            # Tasks are now dicts (from convertFromMongo)
            output = task.get("output", {}) if isinstance(task, dict) else {}

            # Check post_call_data for status
            post_call_data = output.get("post_call_data", {})
            summary_data = post_call_data.get("summary", {})
            call_status = summary_data.get("status", "").lower()

            # Also check call_summary
            call_summary = output.get("call_summary", "").lower() if output.get("call_summary") else ""

            # Analyze status
            if call_status:
                total_analyzed += 1
                if any(pos in call_status for pos in ["interested", "call back", "send details"]):
                    positive_count += 1
                elif "not interested" in call_status:
                    negative_count += 1

            # Analyze summary text
            if call_summary:
                for indicator in positive_indicators:
                    if indicator in call_summary:
                        positive_count += 0.5
                        break
                for indicator in negative_indicators:
                    if indicator in call_summary:
                        negative_count += 0.5
                        break

        if total_analyzed == 0:
            return "None"

        # Determine overall sentiment
        if positive_count > negative_count and positive_count >= 1:
            return "Positive"
        elif negative_count > positive_count and negative_count >= 1:
            return "Negative"
        else:
            return "None"

    def generate_summary(self, tasks: List, analytics: Dict, status: str, sentiment: str, profile_summary: Dict = None, previous_task: List = None) -> str:
        total_calls = analytics.get("total_calls", 0)
        connected_calls = analytics.get("connected_calls", 0)
        response_rate = analytics.get("response_rate", "0%")
        avg_duration = analytics.get("avg_call_duration", "0s")
        preferred_time = analytics.get("preferred_time", "N/A")

        # Build markdown summary
        md_lines = []
        md_lines.append("## Profile Overview")

        if profile_summary:
            summary_text = profile_summary.get('summary_text')
            if summary_text:
                md_lines.append(summary_text)
                md_lines.append("")

            md_lines.append(f"- **Next Action:** {profile_summary.get('next_action', 'N/A')}")
            md_lines.append(f"- **Interest Level:** {profile_summary.get('interest_level', 'N/A')}")

            if profile_summary.get('callback_requested'):
                callback_time = profile_summary.get('callback_time') or 'Not specified'
                md_lines.append(f"- **Callback Requested:** Yes ({callback_time})")

        # Add History section from recent conversations
        if previous_task:
            md_lines.append("")
            md_lines.append("### History")
            for conv in previous_task:
                date = conv.get('date', '')
                summary = conv.get('summary', '')
                if summary:
                    md_lines.append(f"- {date}: {summary}")

        return "\n".join(md_lines)

    def generate_previous_task(self, tasks: List, limit: int = 10) -> List[Dict]:
        previous_task = []

        call_tasks = [t for t in tasks if t.get("execution_type") == "call"]

        def get_call_date(task):
            """Extract call date for sorting - latest first"""
            if not isinstance(task, dict):
                return ''
            output = task.get('output', {})
            output_data = output.get('data', {}) if isinstance(output, dict) else {}
            # Try to get the actual call start time
            call_date = (
                output_data.get('startedAt') or
                output_data.get('endedAt') or
                output.get('start_time') or
                output.get('end_time') or
                task.get('updated_at') or
                task.get('created_at') or
                task.get('modified') or
                task.get('created') or
                ''
            )
            return str(call_date) if call_date else ''

        sorted_tasks = sorted(
            call_tasks,
            key=get_call_date,
            reverse=True  # Descending - latest first
        )[:limit]

        for task in sorted_tasks:
            output = task.get("output", {}) if isinstance(task, dict) else {}
            status = task.get("status") if isinstance(task, dict) else None

            output_data = output.get("data", {})
            call_date = (
                output_data.get("startedAt") or
                output_data.get("endedAt") or
                output.get("start_time") or
                output.get("end_time") or
                task.get("updated_at") or
                task.get("created_at") or
                task.get("modified") or
                task.get("created") or
                ""
            )

            # Calculate call duration
            duration_seconds = 0
            duration_val = output.get("duration")
            if duration_val:
                try:
                    # Handle timedelta object
                    if hasattr(duration_val, 'total_seconds'):
                        duration_seconds = duration_val.total_seconds()
                    else:
                        duration_seconds = float(duration_val)
                except (ValueError, TypeError):
                    pass

            # Fallback: Calculate from timestamps
            if duration_seconds == 0:
                started_at = output_data.get("startedAt") or output.get("start_time")
                ended_at = output_data.get("endedAt") or output.get("end_time")
                if started_at and ended_at:
                    try:
                        if isinstance(started_at, str):
                            start_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                        else:
                            start_dt = started_at
                        if isinstance(ended_at, str):
                            end_dt = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
                        else:
                            end_dt = ended_at
                        duration_seconds = (end_dt - start_dt).total_seconds()
                    except (ValueError, TypeError):
                        pass

            # Format duration as "Xm Ys" or "Xs"
            if duration_seconds > 0:
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                if minutes > 0:
                    call_duration = f"{minutes}m {seconds}s"
                else:
                    call_duration = f"{seconds}s"
            else:
                call_duration = "0s"

            # Format call_date to string with date and time (convert to IST)
            # IST = UTC + 5:30
            IST = timezone(timedelta(hours=5, minutes=30))

            if call_date and str(call_date).upper() != "NULL":
                try:
                    dt = None
                    if isinstance(call_date, str):
                        # Handle multiple formats:
                        # 1. ISO format: "2025-12-16T14:30:00.000Z"
                        # 2. SQL format: "2025-12-16 14:30:00"
                        call_date_str = call_date.replace('Z', '+00:00')

                        # Try parsing with 'T' separator first (ISO format)
                        if 'T' in call_date_str:
                            dt = datetime.fromisoformat(call_date_str)
                        else:
                            # SQL format - parse directly or replace space with T
                            try:
                                dt = datetime.strptime(call_date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
                                # Assume UTC if no timezone info
                                dt = dt.replace(tzinfo=timezone.utc)
                            except ValueError:
                                # Fallback: try fromisoformat anyway
                                dt = datetime.fromisoformat(call_date_str)
                    elif isinstance(call_date, datetime):
                        dt = call_date
                        # If naive datetime, assume UTC
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)

                    # Convert to IST
                    if dt:
                        dt_ist = dt.astimezone(IST)
                        call_date = dt_ist.strftime("%Y-%m-%d %H:%M")

                except Exception as e:
                    # If all parsing fails, keep original or set empty
                    if isinstance(call_date, str) and len(call_date) >= 10:
                        # At least show the date part
                        call_date = call_date[:16] if len(call_date) >= 16 else call_date[:10]
                    else:
                        call_date = ""

            # Get actual call summary from post_call_data
            post_call_data = output.get("post_call_data", {})
            classification = post_call_data.get("classification", {})

            # Try multiple sources for the actual summary
            summary = (
                classification.get("summary") or
                post_call_data.get("summary", {}).get("text") or
                post_call_data.get("summary", {}).get("summary") or
                output.get("call_summary") or
                output_data.get("summary") or
                ""
            )

            # Only add to history if there's an actual summary
            if summary and summary.strip():
                previous_task.append({
                    "date": call_date,
                    "summary": summary[:300] + "..." if len(summary) > 300 else summary
                })

        return previous_task

    def get_latest_profile_summary(self, tasks: List) -> Dict:
        call_tasks = [t for t in tasks if t.get("execution_type") == "call"]

        sorted_tasks = sorted(
            call_tasks,
            key=lambda t: t.get('updated_at', t.get('modified', t.get('created_at', t.get('created', '')))) if isinstance(t, dict) else '',
            reverse=True
        )

        for task in sorted_tasks:
            output = task.get("output", {}) if isinstance(task, dict) else {}
            post_call_data = output.get("post_call_data", {})
            profile_summary = post_call_data.get("profile_summary")

            if profile_summary:
                return profile_summary

        return None

    def build_overview(self, tasks: List = None) -> Dict:
        if tasks is None:
            tasks = self.fetch_tasks_by_document()

        # Calculate all components
        profile_analytics = self.calculate_profile_analytics(tasks)
        profile_status = self.determine_profile_status(tasks, profile_analytics)
        sentiment = self.analyze_sentiment(tasks)
        previous_task = self.generate_previous_task(tasks, limit=5)
        profile_summary = self.get_latest_profile_summary(tasks)

        # Add sentiment to analytics after last_connected (same as profile_summary.sentiment)
        profile_analytics["sentiment"] = profile_summary.get("sentiment") if profile_summary else None

        summary = self.generate_summary(tasks, profile_analytics, profile_status, sentiment, profile_summary, previous_task)

        overview = {
            "summary": summary,
            "analytics": profile_analytics,
            "profile_status": profile_status,
            "recent_conversations": previous_task,
            "profile_summary": profile_summary
        }

        print_log(f"Built overview for document {self.document_id}: {overview}", "profile_update_overview_built")

        return overview

    def update_document_in_mongodb(self, overview: Dict) -> bool:
        if not self.collection_ref:
            print_log("No collection_ref provided, skipping MongoDB update", "profile_update_skip_mongo")
            return False

        try:
            from bson import ObjectId
            from pymongo import MongoClient
            from super_services.libs.config import settings

            # Get MongoDB connection using correct settings
            client = MongoClient(settings.MONGO_DSN)
            db = client[settings.MONGO_DB]

            # Access the collection by collection_ref name
            collection = db[self.collection_ref]

            # Update document by _id with overview
            result = collection.update_one(
                {"_id": ObjectId(self.document_id)},
                {"$set": {"overview": overview}}
            )

            client.close()

            if result.modified_count > 0:
                print_log(f"Updated document {self.document_id} in collection {self.collection_ref} with overview", "profile_update_mongo_success")
                return True
            else:
                print_log(f"Document {self.document_id} not modified in MongoDB (may already have same data)", "profile_update_mongo_no_change")
                return True

        except Exception as e:
            print_log(f"Error updating document {self.document_id} in collection {self.collection_ref}: {str(e)}", "profile_update_mongo_error")
            return False

    async def update_document(self, overview: Dict = None) -> Dict:
        try:
            if overview is None:
                overview = self.build_overview()

            # # Fetch current document
            # response = requests.get(self.api_url)

            # if response.status_code != 200:
            #     print_log(f"Failed to fetch document {self.document_id}: {response.status_code}", "profile_update_fetch_failed")
            #     return {"status": "failed", "error": f"Failed to fetch document: {response.status_code}"}

            # doc_data = response.json().get("data", {})

            # # Update with overview
            # doc_data["overview"] = overview

            # POST updated document to Store Service
            # update_response = requests.post(self.api_url, json=doc_data)

            # if update_response.status_code == 200:
            #     print_log(f"Successfully updated document {self.document_id} with overview in Store Service", "profile_update_success")

                # Also update document in MongoDB collection (collection_ref)
            self.update_document_in_mongodb(overview)

            return {
                "status": "completed",
                "data": {},
                "overview": overview
            }
            # else:
            #     print_log(f"Failed to update document {self.document_id}: {update_response.status_code}", "profile_update_failed")
            #     return {"status": "failed", "error": f"Failed to update: {update_response.status_code}"}

        except Exception as e:
            print_log(f"Error updating document {self.document_id}: {str(e)}", "profile_update_error")
            return {"status": "failed", "error": str(e)}


async def update_profile_after_call(document_id: str = None, token: str = None, collection_ref: str = None, task_id: str = None) -> Dict:
    if task_id:
        try:
            task_cursor = TaskModel._get_collection().find_one({"task_id": task_id})
            if task_cursor:
                task = convertFromMongo(task_cursor)
                # Get document_id from ref_id
                document_id = task.get("ref_id")
                # Get collection_ref
                collection_ref = task.get("collection_ref")
                # Get space_id to fetch token
                space_id = task.get("space_id")

                # Fetch token from MySQL using space_id
                if space_id:
                    token = get_token_from_space_id(space_id)
                else:
                    print_log(f"No space_id found in task {task_id}", "profile_update_no_space_id")

                print_log(f"Fetched from task {task_id}: document_id={document_id}, collection_ref={collection_ref}, space_id={space_id}, token={token}", "profile_update_task_fetch")
            else:
                print_log(f"Task {task_id} not found", "profile_update_task_not_found")
                return {"status": "failed", "error": f"Task {task_id} not found"}
        except Exception as e:
            print_log(f"Error fetching task {task_id}: {str(e)}", "profile_update_task_fetch_error")
            return {"status": "failed", "error": str(e)}

    # Validate required fields
    if not document_id or not token:
        return {"status": "failed", "error": "Missing document_id or token"}

    service = ProfileUpdateService(document_id, token, collection_ref)
    return await service.update_document()




async def update_profile_by_task_id(task_id: str) -> Dict:
    return await update_profile_after_call(task_id=task_id)


def _print_result(result: Dict):
    print(f"\n{'='*60}")
    print("PROFILE UPDATE RESULT")
    print(f"{'='*60}")
    print(f"Status: {result.get('status')}")

    if result.get('error'):
        print(f"Error: {result.get('error')}")

    if result.get('overview'):
        overview = result['overview']
        print(f"\nSummary: {overview.get('summary')}")
        print(f"Profile Status: {overview.get('profile_status')}")
        print(f"Sentiment: {overview.get('sentiment')}")

        print(f"\nProfile Analytics:")
        analytics = overview.get('profile_analytics', {})
        for key, value in analytics.items():
            print(f"  - {key}: {value}")

        print(f"\nPrevious Tasks:")
        previous_task = overview.get('previous_task', [])
        for item in previous_task:
            print(f"  - {item.get('date')}: {item.get('labels')} - {item.get('summary')}")

        print(f"\nProfile Summary:")
        profile_summary = overview.get('profile_summary')
        if profile_summary:
            print(f"  - Sentiment: {profile_summary.get('sentiment')}")
            print(f"  - Tone: {profile_summary.get('tone')}")
            print(f"  - Engagement: {profile_summary.get('engagement')}")
            print(f"  - Interest Level: {profile_summary.get('interest_level')}")
            print(f"  - Outcome: {profile_summary.get('outcome')}")
            print(f"  - Next Action: {profile_summary.get('next_action')}")
            print(f"  - Callback Requested: {profile_summary.get('callback_requested')}")
            print(f"  - Summary: {profile_summary.get('summary_text')}")
        else:
            print("  - No profile summary available")

    print(f"{'='*60}\n")


# Direct execution for testing
if __name__ == "__main__":
    # Test with sample data - update these values as needed
    test_task_id = os.getenv("TEST_PROFILE_TASK_ID", "T0765733fbf9e11f082ac156368e7acc4")

    async def main():
        print(f"Updating profile using task_id: {test_task_id}")

        result = await update_profile_by_task_id(test_task_id)
        _print_result(result)

        return result

    asyncio.run(main())
