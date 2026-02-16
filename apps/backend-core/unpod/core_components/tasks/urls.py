from django.urls import path

from unpod.core_components.tasks.views import TaskServiceViewSet

# fmt: off
urlpatterns = [
    # Task Service
    path(
        'space-task/<space_token>/',
        TaskServiceViewSet.as_view({"post": "create_space_task", "get": "get_space_task"}),
        name='space_task'
    ),
    path(
        'space-task/<space_token>/export/',
        TaskServiceViewSet.as_view({"get": "export_space_tasks"}),
        name='export_space_tasks'
    ),
    path(
        'space-runs/<space_token>/',
        TaskServiceViewSet.as_view({"get": "get_space_run"}),
        name='space_runs'
    ),
    path(
        'space-runs/<space_token>/<str:run_id>/',
        TaskServiceViewSet.as_view({"get": "get_run_task"}),
        name='space_run_task'
    ),
]
