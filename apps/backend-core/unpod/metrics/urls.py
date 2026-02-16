from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MetricsViewSet, CallLogViewSet

router = DefaultRouter()
router.register(r"", MetricsViewSet, basename="metrics-list")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "organization/",
        MetricsViewSet.as_view({"get": "get_metrics"}),
        name="organization",
    ),
    path(
        "organization/",
        MetricsViewSet.as_view({"post": "create_metrics"}),
        name="organization_metrics",
    ),
    path(
        "space-logs/",
        MetricsViewSet.as_view({"get": "get_space_logs"}),
        name="space_logs",
    ),
    # metric logs api
    path(
        "log-metrics/",
        CallLogViewSet.as_view({"post": "log_metrics_data"}),
        name="metrics_log",
    ),
    path(
        "log-metrics/upload/",
        CallLogViewSet.as_view({"post": "log_metric_file"}),
        name="metrics_log",
    ),
    path(
        "call-logs/",
        CallLogViewSet.as_view({"get": "get_call_logs"}),
        name="metrics_log",
    ),
]
