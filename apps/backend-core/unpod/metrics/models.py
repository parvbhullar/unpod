from django.db import models
from unpod.common.enum import TrendTypes, StatusType, TrunkDirection ,MetricTypes
from unpod.core_components.models import Pilot
from unpod.space.models import SpaceOrganization, Space
from unpod.common.enum import ProductTypes


class CallLog(models.Model):
    call_status = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
    )
    end_reason = models.CharField(max_length=100, null=True, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    call_type = models.CharField(
        max_length=22,
        choices=TrunkDirection.choices(),
        null=True,
        blank=True,
        db_index=True,
    )
    call_duration = models.DurationField(null=True, blank=True)
    product_types = models.CharField(
        max_length=20,
        choices=ProductTypes.choices(),
        default=ProductTypes.telephony_sip.value,
    )
    source_number = models.CharField(max_length=15, null=True, db_index=True)
    destination_number = models.CharField(max_length=15, null=True, db_index=True)
    organization = models.ForeignKey(
        SpaceOrganization, on_delete=models.SET_NULL, null=True
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    agent = models.ForeignKey(Pilot, on_delete=models.SET_NULL, null=True, blank=True)
    space = models.ForeignKey(Space, on_delete=models.SET_NULL, null=True, blank=True)
    metrics_metadata = models.JSONField(null=True, blank=True)
    calculated = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            "organization",
            "start_time",
            "source_number",
            "destination_number",
            "end_time",
        )
        indexes = [
            # Note: organization+creation_time index exists in migration 'add_critical_indexes_metrics.py'
            # Space-level call metrics
            models.Index(fields=['space', 'creation_time'], name='calllog_space_time_idx'),
            # Agent/pilot performance metrics
            models.Index(fields=['agent', 'creation_time'], name='calllog_agent_time_idx'),
            # Call success rate analysis over time
            models.Index(fields=['call_status', 'creation_time'], name='calllog_status_time_idx'),
            # Find uncalculated call logs for background processing
            models.Index(fields=['calculated', 'creation_time'], name='calllog_calc_time_idx'),
            # Subscription voice usage stats query optimization
            models.Index(fields=['organization', 'product_id', 'start_time'], name='calllog_org_prod_start_idx'),
        ]


class Metrics(models.Model):
    METRIC_NAMES = [
        ("Number of Calls", "Number of Calls"),
        ("Avg Duration", "Avg Duration"),
        ("Total Cost", "Total Cost"),
        ("Avg Cost", "Avg Cost"),
        ("Successful Calls", "Successful Calls"),
        ("Failed Calls", "Failed Calls"),
    ]

    name = models.CharField(
        max_length=50,
        choices=METRIC_NAMES,
        default="Number of Calls",
    )

    product_types = models.CharField(
        max_length=20,
        choices=ProductTypes.choices(),
        default=ProductTypes.telephony_sip.name,
    )
    value = models.CharField(max_length=20)
    unit = models.CharField(max_length=20, blank=True)
    growth = models.FloatField(default=0.0)
    trend = models.CharField(
        max_length=50, choices=TrendTypes.choices(), default=TrendTypes.positive.name
    )
    status = models.CharField(
        max_length=20,
        choices=StatusType.choices(),
        default=StatusType.active.name,
        db_index=True,
    )
    pilot = models.ForeignKey(Pilot, on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(
        SpaceOrganization, on_delete=models.CASCADE, null=True, blank=True
    )
    product_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metric_type=models.CharField(choices=MetricTypes.choices(), default=MetricTypes.Agents.value, max_length=50)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Metrics"
        verbose_name_plural = "Metrics"
        indexes = [
            # Organization metrics by type over time
            models.Index(fields=['organization', 'metric_type', 'created_at'], name='metrics_org_type_time_idx'),
            # Pilot-specific metrics over time
            models.Index(fields=['pilot', 'metric_type', 'created_at'], name='metrics_pilot_type_time_idx'),
            # Active metrics filtering
            models.Index(fields=['status', 'metric_type'], name='metrics_status_type_idx'),
        ]
