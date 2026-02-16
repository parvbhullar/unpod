import uuid
from datetime import datetime
from typing import Dict, Optional, List
from libs.core.pagination import paginateData
from services.task_service.models.task import (
    RunModel,
    TaskModel,
    ArtifactModel,
)
from services.task_service.schemas.task import TaskStatusEnum


class TaskService:
    """Core Task Service for handling task execution and management"""

    def create_run(
        self,
        space_id: str,
        user: str,
        collection_ref: str,
        batch_count: int = 0,
        run_mode: str = "dev",
        thread_id: Optional[str] = None,
        user_org_id: Optional[str] = None,
        **run_data,
    ) -> Dict:
        """Create a new run"""
        run_id = f"R{uuid.uuid1().hex}"

        run = RunModel.save_single_to_db(
            {
                "run_id": run_id,
                "space_id": space_id,
                "batch_count": batch_count,
                "collection_ref": collection_ref,
                "run_mode": run_mode,
                "thread_id": thread_id,
                "user_org_id": user_org_id,
                "user": user,
                **run_data,
            }
        )
        return run.dict()

    def add_task(
        self,
        run_id: str,
        task_data: Dict,
        assignee: str,
        collection_ref: str,
        thread_id: Optional[str] = None,
        execution_type: Optional[str] = None,
        **task_data_kargs,
    ) -> Dict:
        """Add a task to a run"""
        task_id = f"T{uuid.uuid1().hex}"
        task_obj = {
            "task_id": task_id,
            "run_id": run_id,
            "thread_id": thread_id,
            "collection_ref": collection_ref,
            "task": task_data,
            "assignee": assignee,
            "status": TaskStatusEnum.pending,
            "execution_type": execution_type,
            **task_data_kargs,
        }
        task = TaskModel.save_single_to_db(task_obj)
        return task.dict()

    def update_task_status(
        self, task_id: str, status: TaskStatusEnum, output: Optional[Dict] = None
    ) -> Dict:
        """Update task status and output"""
        task = TaskModel.get({"task_id": task_id})
        if task:
            update_data = {"status": status}
            if output:
                update_data["output"] = output
            TaskModel.update_one({"task_id": task_id}, update_data)
            return TaskModel.get(task_id=task_id).dict()
        return {"error": "Task not found"}

    def get_run_status(self, run_id: str) -> Dict:
        """Get status of a run and its tasks"""
        run = RunModel.find_one({"run_id": run_id})
        if not run:
            return {"error": "Run not found"}

        tasks = list(TaskModel.find(runId=run_id))
        task_stats = {
            "total": len(tasks),
            "completed": len(
                [t for t in tasks if t.status == TaskStatusEnum.completed]
            ),
            "failed": len([t for t in tasks if t.status == TaskStatusEnum.failed]),
            "pending": len([t for t in tasks if t.status == TaskStatusEnum.pending]),
        }

        return {"run": run.dict(), "task_stats": task_stats}

    def add_artifact(
        self,
        file_id: str,
        path: str,
        space_id: str,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Dict:
        """Add an artifact"""
        artifact_data = {
            "file_id": file_id,
            "path": path,
            "space_id": space_id,
            "thread_id": thread_id,
            "run_id": run_id,
            "task_id": task_id,
        }
        artifact = ArtifactModel.create(artifact_data)
        return artifact.dict()

    def get_pending_tasks(self, run_id: Optional[str] = None) -> List[Dict]:
        """Get pending tasks for processing"""
        query = {"status": TaskStatusEnum.pending}
        if run_id:
            query["run_id"] = run_id
        tasks = TaskModel.find(**query)
        return [task.dict() for task in list(tasks)]

    def get_query(
        self,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ):
        query = {}
        if space_id:
            query["space_id"] = space_id
        if user_id:
            query["user"] = user_id
        if thread_id:
            query["thread_id"] = thread_id
        return query

    def get_filters(self, request):
        search_str = request.query_params.get("search")
        call_type = request.query_params.get("call_type")
        date_from = request.query_params.get("from_ts")
        date_to = request.query_params.get("to_ts")
        status = request.query_params.get("status")

        filters = []

        if date_from or date_to:
            date_filter = {}
            try:
                if date_from:
                    date_filter["$gte"] = datetime.fromtimestamp(int(date_from))
                if date_to:
                    date_filter["$lte"] = datetime.fromtimestamp(int(date_to))
                filters.append({"created": date_filter})
            except Exception:
                pass

        if call_type:
            if call_type == "inbound":
                call_type_values = ["inbound", "inboundPhoneCall"]
            elif call_type == "outbound":
                call_type_values = ["outbound", "outboundPhoneCall"]
            else:
                call_type_values = [call_type]
            filters.append(
                {
                    "$or": [
                        {"output.call_type": {"$in": call_type_values}},
                        {"output.type": {"$in": call_type_values}},
                    ]
                }
            )

        if search_str:
            filters.append(
                {
                    "$or": [
                        {"input.name": {"$regex": search_str, "$options": "i"}},
                        {"input.phone": {"$regex": search_str, "$options": "i"}},
                        {"output.customer": {"$regex": search_str, "$options": "i"}},
                        {
                            "output.contact_number": {
                                "$regex": search_str,
                                "$options": "i",
                            }
                        },
                    ]
                }
            )

        if status:
            status_values = [s.strip().replace("+", " ") for s in status.split(",")]

            filters.append(
                {"output.post_call_data.summary.status": {"$in": status_values}}
            )

        return filters

    def get_runs(
        self,
        request,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get pending runs for processing"""
        query = self.get_query(space_id, user_id, thread_id)
        if not query:
            return [], 0
        res_data = paginateData(RunModel, request, mongo=True, query=query)
        return res_data["data"], res_data["count"]

    def get_tasks(
        self,
        request,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get pending tasks for processing"""
        query = self.get_query(space_id, user_id, thread_id)

        if not query:
            return [], 0

        filters = self.get_filters(request)

        if filters:
            query["$and"] = filters

        res_data = paginateData(TaskModel, request, mongo=True, query=query)
        return res_data["data"], res_data["count"]

    def get_run_tasks(
        self,
        request,
        run_id,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> List[Dict]:
        """Get pending tasks for processing"""
        query_extra = self.get_query(space_id, user_id, thread_id)
        if not query_extra:
            return [], 0
        query = {"run_id": run_id, **query_extra}
        res_data = paginateData(TaskModel, request, mongo=True, query=query)
        return res_data["data"], res_data["count"]
