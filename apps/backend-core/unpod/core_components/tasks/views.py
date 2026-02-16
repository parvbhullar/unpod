from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from unpod.common.renderers import UnpodJSONRenderer
from unpod.core_components.tasks.serializers import (
    TaskRunSerializer,
)
from unpod.core_components.tasks.utils import (
    convert_run_data,
    fetch_space_run_tasks,
    fetch_space_runs,
    fetch_space_tasks,
    push_to_tasks,
    export_space_tasks,
)
from unpod.space.utils import checkSpaceAccess, checkSpaceOperationAccess
from drf_spectacular.utils import extend_schema


class TaskServiceViewSet(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Task Runs"],
        operation_id="Create Run",
        request=TaskRunSerializer,
        responses={200: TaskRunSerializer},
        description="Create a Task in a Space",
    )
    def create_space_task(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        ser = TaskRunSerializer(data=request.data)
        if ser.is_valid():
            run_data = convert_run_data(
                ser.validated_data, space, request.user, request
            )
            run_push_res, push_status, status_code = push_to_tasks(run_data)
            if push_status:
                return Response(
                    {"message": "Task Created Successfully", "data": run_push_res},
                    status=status_code,
                )
            else:
                error_message = "Task Creation Failed"
                if isinstance(run_push_res["message"], dict):
                    message = run_push_res.get("message", {}).get("message") or run_push_res.get("message", {}).get("detail")
                    if message:
                        error_message = f'{error_message}: {message}'
                return Response(
                    {
                        "message": error_message,
                        "errors": run_push_res["message"],
                    },
                    status=status_code,
                )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    @extend_schema(
        tags=["Task Runs"],
        operation_id="Gets All the task runs",
        description="Get all Task Runs in a Space. Returns a list of all task runs with their details including run ID, status, and associated user information.",
    )
    def get_space_run(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        runs, status, count = fetch_space_runs(space.id, request)
        if status:
            return Response(
                {"message": "Runs Fetched Successfully", "data": runs, "count": count}
            )
        return Response(
            {"message": "Runs Fetch Failed", "errors": runs["message"]},
            status=206,
        )

    @extend_schema(
        operation_id="Get Task", tags=["Tasks"], description="Get a Task in a Space"
    )
    def get_space_task(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        tasks, status, count = fetch_space_tasks(space.id, request)
        if status:
            return Response(
                {"message": "Tasks Fetched Successfully", "data": tasks, "count": count}
            )
        return Response(
            {"message": "Runs Fetch Failed", "errors": tasks["message"]},
            status=206,
        )

    def export_space_tasks(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)

        return export_space_tasks(space_role.space, request)

    @extend_schema(
        tags=["Task Runs"], operation_id="Get Task Run", description="Get a Task Run"
    )
    def get_run_task(self, request, *args, **kwargs):
        space_token = kwargs.get("space_token")
        run_id = kwargs.get("run_id")
        space_role = checkSpaceAccess(
            request.user,
            token=space_token,
            check_role=True,
            custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
        )
        checkSpaceOperationAccess(request.user, space_role)
        space = space_role.space
        tasks, status, count = fetch_space_run_tasks(space.id, run_id, request)
        if status:
            return Response(
                {"message": "Tasks Fetched Successfully", "data": tasks, "count": count}
            )
        return Response(
            {"message": "Runs Fetch Failed", "errors": tasks["message"]},
            status=206,
        )
