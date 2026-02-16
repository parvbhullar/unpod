from unpod.common.mongodb import MongoDBQueryManager
from unpod.common.pagination import getPagination


def fetch_tasks_by_agent(handle, request):
    """
    Fetch tasks by handle from MongoDB directly
    """
    collection = MongoDBQueryManager.get_collection("tasks")
    query = {"assignee": handle}

    # Pagination
    skip, limit = getPagination(request.query_params.dict(), default_limit=20)

    # Get total count
    count = collection.count_documents(query)

    # Fetch tasks with pagination
    tasks = list(collection.find(query).sort("created", -1).skip(skip).limit(limit))

    # Convert ObjectId to string
    for task in tasks:
        if "_id" in task:
            task["_id"] = str(task["_id"])

    return tasks, True, count


# ========== Call Logs Utils ==========


def fetch_call_logs(domain_handle, product_id, request):
    """
    Fetch call logs from MySQL (similar to metrics app but for API v2)
    """
    from unpod.metrics.models import CallLog
    from unpod.metrics.serializers import CallLogSerializer
    from datetime import datetime, timedelta
    import json

    try:
        # Base queryset
        logs = CallLog.objects.filter(
            organization__domain_handle=domain_handle, product_id=product_id
        ).only(
            "id",
            "source_number",
            "destination_number",
            "call_type",
            "call_status",
            "creation_time",
            "start_time",
            "end_time",
            "call_duration",
            "end_reason",
            "bridge",
        )

        # Apply filters from query params
        start_date = request.query_params.get("start_time")
        end_date = request.query_params.get("end_time")
        call_type = request.query_params.get("call_type")
        call_status = request.query_params.get("call_status")
        bridge_name = request.query_params.get("bridge")
        source_number = request.query_params.get("source_number")
        call_id = request.query_params.get("call_id")
        destination_number = request.query_params.get("destination_number")
        duration = request.query_params.get("call_duration")

        # Build filters
        filters = {}
        if start_date:
            filters["start_time__date__gte"] = datetime.strptime(
                start_date, "%d-%m-%Y %H:%M:%S"
            ).date()
        if end_date:
            filters["end_time__date__lte"] = datetime.strptime(
                end_date, "%d-%m-%Y %H:%M:%S"
            ).date()
        if call_type:
            filters["call_type__iexact"] = call_type
        if call_status:
            filters["call_status__iexact"] = call_status
        if source_number:
            filters["source_number__istartswith"] = source_number
        if destination_number:
            filters["destination_number__istartswith"] = destination_number
        if call_id:
            filters["id__icontains"] = call_id
        if duration:
            seconds = int(duration)
            duration_obj = timedelta(seconds=seconds)
            filters["call_duration__lte"] = duration_obj

        logs = logs.filter(**filters)

        if bridge_name:
            logs = logs.filter(bridge__name__icontains=bridge_name)

        # Sorting
        sort = request.query_params.get("sort")
        sort_by = "-creation_time"  # default
        if sort:
            try:
                sort = json.loads(sort)
                key = list(sort.keys())[0]
                sort_keys = ["start_time", "end_time", "call_duration"]
                if key in sort_keys:
                    sort_by = key if sort[key] == "ascend" else f"-{key}"
            except Exception:
                pass

        logs = logs.order_by(sort_by)

        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        skip = (page - 1) * page_size

        total_count = logs.count()
        logs_page = logs[skip : skip + page_size]

        # Serialize
        serializer = CallLogSerializer(logs_page, many=True)

        # Build next/previous URLs
        base_url = request.build_absolute_uri(request.path)
        next_url = None
        previous_url = None

        if skip + page_size < total_count:
            next_url = f"{base_url}?page={page + 1}&page_size={page_size}"
        if page > 1:
            previous_url = f"{base_url}?page={page - 1}&page_size={page_size}"

        return {
            "count": total_count,
            "data": serializer.data,
            "next": next_url,
            "previous": previous_url,
        }, True

    except Exception as e:
        print(f"❌ Error fetching call logs: {str(e)}")
        return {"message": f"Failed to fetch call logs: {str(e)}"}, False
