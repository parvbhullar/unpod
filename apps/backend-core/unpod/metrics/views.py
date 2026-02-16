import csv
import json
from datetime import datetime, timedelta

from dateutil import parser
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum
from django.http import StreamingHttpResponse
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from unpod.common.logger import UnpodLogger
from unpod.core_components.models import Pilot, TelephonyNumber
from unpod.space.models import Space
from unpod.space.models import SpaceOrganization
from .models import Metrics, CallLog
from .serializers import MetricsSerializer, CallLogSerializer
from .utils import CallLogPagination
from .utils import create_metric, load_csv, create_update_metric, Echo, normalize_number
from unpod.common.enum import Product
from unpod.common.mixin import QueryOptimizationMixin
from ..common.enum import StatusType
from ..common.exception import APIException206
from ..common.renderers import UnpodJSONRenderer
from ..space.utils import checkSpaceOrg

metrics_logger = UnpodLogger("metrics")


class MetricsViewSet(QueryOptimizationMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for handling metrics and logs.

    Phase 2.2: Refactored to use QueryOptimizationMixin for query optimization.
    """

    queryset = Metrics.objects.all()
    serializer_class = MetricsSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status=StatusType.active.name)

        domain_handle = self.request.headers.get("Org-Handle", None)
        if not domain_handle or domain_handle == "":
            raise APIException206({"message": "Please provide Organization handle"})

        organization = checkSpaceOrg(domain_handle)
        queryset = queryset.filter(organization=organization)

        return queryset

    def create_metrics(self, request, *args, **kwargs):
        try:
            product_id = request.headers.get("Product-Id", None)
            handle = request.headers.get("Org-Handle", None)
            if not handle:
                return Response(
                    {"message": "Please provide Organization handle"}, status=400
                )

            metric_units = {
                "Number of Calls": "number",
                "Avg Duration": "duration",
                "Total Cost": "currency",
                "Avg Cost": "currency",
            }

            organization = SpaceOrganization.objects.get(handle=handle)

            metric_names = [name for name, _ in Metrics.METRIC_NAMES]
            metrics_to_create = []
            for metric_name in metric_names:
                metrics_to_create.append(
                    Metrics(
                        name=metric_name,
                        value="0",
                        unit=metric_units.get(metric_name, ""),
                        organization=organization,
                        product_id=product_id,
                    )
                )

            Metrics.objects.bulk_create(metrics_to_create)
            create_metric(organization, product_id)

            return Response(
                {
                    "message": f"{len(metrics_to_create)} metrics created for organization {organization.name}"
                },
                status=201,
            )
        except Exception as e:
            return Response({"message": str(e)}, status=500)

    def get_space_logs(self, request, *args, **kwargs):
        """
        Get logs for a specific space using space_token
        """

        try:
            metrics_logger.info(f"Received request with params: {request.query_params}")

            # Get space token from query params
            space_token = request.query_params.get("space_token")
            if not space_token:
                error_msg = "Space token is required"
                metrics_logger.error(error_msg)
                return Response(
                    {"error": error_msg}, status=status.HTTP_400_BAD_REQUEST
                )

            # Get the space by token
            try:
                metrics_logger.info(f"Looking for space with token: {space_token}")
                space = Space.objects.get(token=space_token)
                metrics_logger.info(f"Found space: {space.id} - {space.name}")
            except Space.DoesNotExist as e:
                error_msg = f"Space not found with token: {space_token}"
                metrics_logger.error(error_msg)
                return Response({"error": error_msg}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                error_msg = f"Error fetching space: {str(e)}"
                metrics_logger.error(error_msg, exc_info=True)
                return Response(
                    {"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            try:
                # Get logs for this space with related data
                logs = (
                    CallLog.objects.filter(space=space)
                    .select_related("space")  # Only include valid related fields
                    .order_by("-creation_time")
                )

                # Calculate metrics with a single aggregation query
                from django.db.models import Count
                metrics_agg = logs.aggregate(
                    total_calls=Count("id"),
                    total_duration=Sum("call_duration")
                )
                total_calls = metrics_agg.get("total_calls", 0)
                total_duration = metrics_agg.get("total_duration")

                metrics_logger.info(
                    f"Found {total_calls} logs for space {space_token}"
                )

                # Convert duration to minutes for better readability
                total_duration_minutes = 0
                if total_duration:
                    try:
                        # Handle both timedelta and integer/float durations
                        if hasattr(total_duration, "total_seconds"):
                            total_duration_minutes = round(
                                total_duration.total_seconds() / 60, 2
                            )
                        else:
                            # If it's already in seconds
                            total_duration_minutes = round(
                                float(total_duration) / 60, 2
                            )
                    except Exception as e:
                        metrics_logger.error(
                            f"Error calculating duration: {str(e)}", exc_info=True
                        )
                        total_duration_minutes = 0

                # Serialize the data
                serializer = CallLogSerializer(logs, many=True)

                # Prepare response
                response_data = {
                    "status": "success",
                    "space": {"token": space_token, "name": space.name, "id": space.id},
                    "metrics": {
                        "total_calls": total_calls,
                        "total_duration_minutes": total_duration_minutes,
                        "total_duration_raw": str(total_duration)
                        if total_duration
                        else None,
                    },
                    "logs_count": len(serializer.data),
                }

                # Only include logs if there aren't too many
                if len(serializer.data) <= 100:
                    response_data["logs"] = serializer.data
                else:
                    response_data[
                        "message"
                    ] = f"{len(serializer.data)} logs found. First 100 logs shown."
                    response_data["logs"] = serializer.data[:100]

                metrics_logger.info(
                    f"Successfully processed request for space {space_token}"
                )
                return Response(response_data)

            except Exception as e:
                error_msg = f"Error processing logs: {str(e)}"
                metrics_logger.error(error_msg, exc_info=True)
                return Response(
                    {"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            metrics_logger.error(error_msg, exc_info=True)
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_metrics(self, request, *args, **kwargs):
        try:
            product_id = request.headers.get("Product-Id", None)
            queryset = self.filter_queryset(self.get_queryset())
            # queryset = Metrics.objects.all()
            # serializer = self.get_serializer(queryset, many=True)

            if product_id:
                queryset = queryset.filter(product_id=product_id)

            serializer = MetricsSerializer(
                queryset, context={"request": request}, many=True
            )

            if (
                len(serializer.data) < 6
                or len(serializer.data) < 12
                and product_id == Product.Dev.value
            ):
                metrics_logger.info("Some metrics are missing creating new metrics")
                create_update_metric(
                    org=request.headers.get("Org-Handle"), product_id=product_id
                )
                queryset = self.filter_queryset(self.get_queryset())
                queryset = queryset.filter(product_id=product_id)
                serializer = MetricsSerializer(
                    queryset, context={"request": request}, many=True
                )

            return Response(
                {
                    "count": len(serializer.data),
                    "data": serializer.data,
                    "message": "Metrics fetched successfully.",
                },
                status=200,
            )

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to fetch data.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            return Response(
                {"data": serializer.data, "message": "Metrics fetched successfully."},
                status=200,
            )

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to fetch data.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class CallLogViewSet(viewsets.ModelViewSet):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]
    pagination_class = CallLogPagination

    def log_metrics_data(self, request):
        data = request.data.copy()
        space = Space.objects.get(id=data["space_id"])
        product_id = request.headers.get("Product-Id", settings.DEFAULT_PRODUCT_ID)

        query = Q(handle=data["pilot"])
        pilot = Pilot.objects.filter(query).first()

        data["organization"] = space.space_organization.id
        data["space"] = space.id
        data["agent"] = pilot.id if pilot else None

        if data["start_time"] and data["end_time"]:
            data["start_time"] = parser.parse(data["start_time"])
            data["end_time"] = parser.parse(data["end_time"])
            data["call_duration"] = data["end_time"] - data["start_time"]

        data["metrics_metadata"] = data.get("metrics_metadata", "")

        org = SpaceOrganization.objects.get(id=data["organization"])
        serializer = CallLogSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            create_update_metric(
                org=org, product_id=product_id
            )
            return Response(
                {
                    "message": "Metrics log created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "error": serializer.errors,
                "message": "invalid data",
                "data": serializer.initial_data,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def log_metric_file(self, request):
        uploaded_file = request.FILES.get("file")
        product_id = request.headers.get("Product-Id", "unpod.dev")
        default_org = settings.DEFAULT_ORG_HANDLE
        if not uploaded_file:
            return Response(
                {
                    "status_code": 400,
                    "message": "No file uploaded under key 'file'",
                    "data": {},
                },
                status=400,
            )

        try:
            df = load_csv(uploaded_file)

            new_metric_log = []
            org = SpaceOrganization.objects.filter(
                domain_handle=default_org
            ).first()

            # unique numbers from list
            all_nums = set(
                df["source"].apply(lambda x: normalize_number(str(x)))
            ) | set(df["destination"].apply(lambda x: normalize_number(str(x))))

            # build a set of known telephony numbers for direction detection
            known_numbers = set(
                TelephonyNumber.objects.filter(
                    number__in=all_nums
                ).values_list("number", flat=True)
            )

            for _, row in df.iterrows():
                source = normalize_number(str(row["source"]))
                destination = normalize_number(str(row["destination"]))

                if source in known_numbers:
                    direction = "outbound"
                    assistant_number = source
                    customer_number = destination
                elif destination in known_numbers:
                    direction = "inbound"
                    assistant_number = destination
                    customer_number = source
                else:
                    continue

                new_metric_log.append(
                    CallLog(
                        start_time=row["start_time"],
                        end_time=row["end_time"],
                        source_number=assistant_number,
                        call_type=direction,
                        destination_number=customer_number,
                        organization=org,
                        product_id=product_id,
                        end_reason=row["status"],
                        call_duration=row["end_time"] - row["start_time"],
                        call_status="success"
                        if (row["end_time"] - row["start_time"]).total_seconds()
                        > 10
                        else "failed",
                        metrics_metadata=json.loads(row.to_json()),
                    )
                )

            # create metric logs
            with transaction.atomic():
                CallLog.objects.bulk_create(new_metric_log, ignore_conflicts=True)

            create_update_metric(org=org, product_id=product_id)

            return Response(
                {"message": "log updates successfully", "data": ""}, status=200
            )

        except Exception as e:
            return Response(
                {"message": "Failed to fetch logs.", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_call_logs(self, request, *args, **kwargs):
        domain_handle = request.headers.get("Org-Handle")
        download = request.query_params.get("download", "false")

        if not domain_handle:
            return Response({"error": "Organization handle is required"}, status=400)

        try:
            # Start with base queryset with optimized joins to prevent N+1 queries
            logs = CallLog.objects.filter(
                organization__domain_handle=domain_handle
            ).select_related(
                'agent',
                'space',
                'organization'
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
                "agent",
                "agent__id",
                "agent__name",
                "space",
                "space__id",
                "space__name",
                "organization",
                "organization__id",
                "organization__name",
            )

            # Apply filters from query params
            start_date = request.query_params.get("start_time")
            end_date = request.query_params.get("end_time")
            call_type = request.query_params.get("call_type")
            call_status = request.query_params.get("call_status")
            source_number = request.query_params.get("source_number")
            call_id = request.query_params.get("call_id")
            destination_number = request.query_params.get("destination_number")
            duration = request.query_params.get("call_duration")
            # Apply filters if provided
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
                duration = timedelta(seconds=seconds)
                filters["call_duration__lte"] = duration

            logs = logs.filter(**filters)

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

            # For CSV download
            if download.lower() == "true":
                response = StreamingHttpResponse(
                    self.stream_call_logs_csv(logs), content_type="text/csv"
                )
                response["Content-Disposition"] = 'attachment; filename="call_logs.csv"'
                return response

            # Apply pagination
            page = self.paginate_queryset(logs)
            if page is not None:
                serializer = CallLogSerializer(page, many=True)
                response = self.get_paginated_response(serializer.data)
                data = response.data
                # Return with 'data' key instead of 'results'
                return Response(
                    {
                        "count": data["count"],
                        "next": data["next"],
                        "previous": data["previous"],
                        "data": data["results"],
                    }
                )

            # Non-paginated response
            serializer = CallLogSerializer(logs[:100], many=True)
            return Response(
                {
                    "count": logs.count(),
                    "next": None,
                    "previous": None,
                    "data": serializer.data,
                }
            )

        except Exception as e:
            return Response(
                {
                    "message": "Failed to fetch logs.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def stream_call_logs_csv(self, queryset):
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        # Yield headers
        yield writer.writerow(
            [
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
            ]
        )

        # Iterate queryset in chunks
        for log in queryset.iterator(chunk_size=1000):
            yield writer.writerow(
                [
                    log.id,
                    log.source_number,
                    log.destination_number,
                    log.call_type,
                    log.call_status,
                    log.creation_time,
                    log.start_time,
                    log.end_time,
                    log.call_duration,
                    log.end_reason,
                ]
            )

    def destroy_multiple(self, request, *args, **kwargs):
        domain_handle = request.headers.get("Org-Handle")
        if not domain_handle:
            return Response({"error": "Organization handle is required"}, status=400)
        try:
            CallLog.objects.filter(organization__domain_handle=domain_handle).delete()

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


