import pandas as pd
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from rest_framework.pagination import PageNumberPagination
from unpod.common.enum import MetricTypes, Product
from .models import Metrics, CallLog
from unpod.space.models import SpaceOrganization
from django.db import transaction
from unpod.common.logger import UnpodLogger


metrics_logger = UnpodLogger("metrics")


class CallLogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        return value


def create_metric(org, product_id):
    metrics = Metrics.objects.filter(organization=org, product_id=product_id)
    prev_logs = CallLog.objects.filter(organization=org, product_id=product_id)
    call_count = prev_logs.count()

    for metric in metrics:
        if metric.name == "Number of Calls":
            metric.value = call_count
        if metric.name == "Avg Duration":
            avg_dur = prev_logs.aggregate(
                avg_dur=Avg(
                    ExpressionWrapper(
                        F("end_time") - F("start_time"), output_field=DurationField()
                    )
                )
            )["avg_dur"]

            avg_secs = round(avg_dur.total_seconds() / 60, 3) if avg_dur else 0

            metric.value = avg_secs
        metric.save()


def load_csv(uploaded_file):
    df = None
    cols = [
        "col1",
        "source",
        "destination",
        "type",
        "start_time",
        "call_picked",
        "end_time",
        "col8",
        "duration",
        "status",
        "col11",
        "col12",
        "col13",
        "col14",
        "col15",
    ]

    # load data from csv or excel file only the related columns we will use
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(
            uploaded_file,
            header=None,
            names=cols,
            usecols=[
                "source",
                "destination",
                "start_time",
                "end_time",
                "duration",
                "status",
            ],
            parse_dates=["start_time", "end_time"],
        )

    elif uploaded_file.name.endswith((".xls", ".xlsx")):
        df = pd.read_excel(
            uploaded_file,
            header=None,
            names=cols,
            usecols=[
                "source",
                "destination",
                "start_time",
                "end_time",
                "duration",
                "status",
            ],
            parse_dates=["start_time", "end_time"],
        )

    for col in ["start_time", "end_time"]:
        df[col] = df[col].dt.tz_localize("UTC")

    # delete any duplicate entries from dataframe
    df = df.drop_duplicates(subset=["start_time", "end_time", "source", "destination"])

    return df


def create_update_metric(org, product_id):
    # Handle both string (domain_handle) and SpaceOrganization object
    if org is None:
        metrics_logger.info("Skipping metric creation: organization is None")
        return

    if isinstance(org, str):
        try:
            org = SpaceOrganization.objects.get(domain_handle=org)
        except SpaceOrganization.DoesNotExist:
            metrics_logger.info(
                f"Skipping metric creation: organization with domain_handle '{org}' does not exist"
            )
            return
    elif not isinstance(org, SpaceOrganization):
        raise ValueError(
            f"org must be either a string or SpaceOrganization object, got {type(org)}"
        )

    metrics_logger.info("creating metric table")

    metric_name = [
        "Number of Calls",
        "Avg Duration",
        "Total Cost",
        "Avg Cost",
        "Successful Calls",
        "Failed Calls",
    ]
    success_full = ["completed", "success", "ANSWERED"]
    failed = ["FAILURE", "failed", "FAILED", "REJECTED"]
    metrics_obj = []

    metric_types = [MetricTypes.Agents.value]

    if product_id == Product.Dev.value:
        metric_types.append(MetricTypes.Telephony.value)

    logs = CallLog.objects.filter(organization=org, product_id=product_id)

    for metric in metric_types:
        existing_metrics = set(
            Metrics.objects.filter(
                organization=org, product_id=product_id, metric_type=metric
            ).values_list("name", flat=True)
        )
        for i in metric_name:
            value = 0
            unit = "currency"

            if i in existing_metrics:
                metrics_logger.info(f"Skipping existing metric: {i}")
                continue

            if i == "Number of Calls":
                value = logs.count()
                unit = "number"

            elif i == "Avg Duration":
                if metric == MetricTypes.Agents.value:
                    dur = logs.annotate(
                        duration=ExpressionWrapper(
                            F("end_time") - F("start_time"),
                            output_field=DurationField(),
                        )
                    ).aggregate(avg_duration=Avg("duration"))["avg_duration"]
                    value = round((dur.total_seconds() / 60), 3) if dur else 0
                else:
                    value = 0

                unit = "duration"

            elif i == "Total Cost":
                value = 0
                unit = "currency"

            elif i == "Avg Cost":
                value = 0
                unit = "currency"

            elif i == "Successful Calls":
                value = logs.filter(call_status__in=success_full).count()
                unit = "number"
            elif i == "Failed Calls":
                value = logs.filter(call_status__in=failed).count()
                unit = "number"

            metrics_obj.append(
                Metrics(
                    name=i,
                    value=value,
                    organization=org,
                    product_id=product_id,
                    unit=unit,
                    metric_type=metric,
                )
            )

    with transaction.atomic():
        Metrics.objects.bulk_create(metrics_obj, ignore_conflicts=True)


def normalize_number(number: str, default_country_code: str = "+91") -> str:
    number = number.strip()
    if number.startswith("+"):
        return number
    elif number.startswith(default_country_code.lstrip("+")):
        return "+" + number

    return default_country_code + number


def send_webhook_request(org, data):
    from unpod.core_components.models import Pilot
    from unpod.dynamic_forms.models import DynamicFormValues

    if not org:
        metrics_logger.info("Skipping webhook request organization is not available")
        return

    pilot_list = Pilot.objects.filter(organization=org)

    if not pilot_list:
        metrics_logger.info("Skipping webhook request pilot is not available")
        return

    pilot = pilot_list.first()

    form = DynamicFormValues.objects.get(parent_id=pilot.handle, form__slug="")
