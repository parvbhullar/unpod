from django.db.models import Avg, F, ExpressionWrapper, DurationField, Sum, FloatField

from django.db.models.functions import Cast
from rest_framework import serializers
from  unpod.common.enum import MetricTypes ,ProductTypes
from .models import Metrics, CallLog
from datetime import timedelta


class MetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metrics
        fields = [
            "id",
            "name",
            "value",
            "unit",
            "growth",
            "trend",
            "status",
            "created_at",
            "updated_at",
            "metric_type",
            # "product_id",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        logs = CallLog.objects.filter(
            organization=instance.organization, product_id=instance.product_id
        )

        success_full = ["completed", "success", "ANSWERED"]
        failed = ["FAILURE", "failed", "FAILED", "REJECTED"]

        if instance.metric_type == MetricTypes.Telephony.value:
            temp_logs = logs.filter(product_types= ProductTypes.telephony_sip.value)
        else:
            temp_logs = logs.filter(product_types= ProductTypes.ai_agents.value)

        if temp_logs.count() == 0:
            data["value"] = 0
            instance.value = 0
            instance.save(update_fields=["value"])
            return data

        # print(instance.metric_type)

        if instance.name == "Number of Calls":
            data["value"] = temp_logs.count()
            instance.value = temp_logs.count()
            instance.unit = "number"

        elif instance.name == "Avg Duration":

            old_avg = float(instance.value) if instance.value else 0

            new_logs = temp_logs.filter(calculated=False)

            new_count = new_logs.count()
            if new_count > 0:
                new_avg_dur = new_logs.aggregate(
                    avg_dur=Avg(
                        ExpressionWrapper(
                            F("end_time") - F("start_time"), output_field=DurationField()
                        )
                    )
                )["avg_dur"]

                new_avg_secs = new_avg_dur.total_seconds() / 60 if new_avg_dur else 0

                total_count = temp_logs.count()
                old_count = total_count - new_count
                if old_count > 0:
                    avg_secs = ((old_avg * old_count) + (new_avg_secs * new_count)) / total_count
                else:
                    avg_secs = new_avg_secs

                avg_secs = round(avg_secs, 3)
            else:
                avg_secs = old_avg

            instance.value = avg_secs
            data["value"] = avg_secs
            instance.unit = "duration"

        elif instance.name == "Total Cost":
            total_cost = (
                temp_logs.annotate(
                    cost_value=Cast(F("metrics_metadata__cost"), FloatField())
                ).aggregate(total=Sum("cost_value"))["total"]
                or 0
            )

            instance.value = round(total_cost, 2)
            data["value"] = round(total_cost, 2)
            instance.unit = "currency"

        elif instance.name == "Avg Cost":
            # Get old average from instance
            old_avg = float(instance.value) if instance.value else 0

            # Get new logs that haven't been calculated yet
            new_logs = temp_logs.filter(calculated=False)
            new_count = new_logs.count()

            if new_count > 0:
                # Calculate average for new logs only
                new_avg_cost = (
                    new_logs.annotate(
                        cost_value=Cast(F("metrics_metadata__cost"), FloatField())
                    ).aggregate(avg=Avg("cost_value"))["avg"]
                    or 0
                )

                # Get total count (old + new)
                total_count = temp_logs.count()
                old_count = total_count - new_count

                # Calculate incremental average
                if old_count > 0:
                    avg_cost = ((old_avg * old_count) + (new_avg_cost * new_count)) / total_count
                else:
                    avg_cost = new_avg_cost

                avg_cost = round(avg_cost, 2)
            else:
                # No new logs, use old average
                avg_cost = old_avg

            instance.value = avg_cost
            data["value"] = avg_cost
            instance.unit = "currency"

        elif instance.name == "Successful Calls":
            count = temp_logs.filter(call_status__in=success_full).count()
            instance.value = count
            data["value"] = count
            instance.unit = "number"

        elif instance.name == "Failed Calls":
            count = temp_logs.filter(call_status__in=failed).count()
            instance.value = count
            data["value"] = count
            instance.unit = "number"

        instance.save(update_fields=["value", "unit"])

        return data


class CallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallLog
        fields = [
            "id",
            "call_status",
            "end_reason",
            "call_type",
            "organization",
            "product_id",
            "agent",
            "space",
            "creation_time",
            "start_time",
            "end_time",
            "call_duration",
            "source_number",
            "destination_number",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        duration = (
            instance.end_time - instance.start_time
            if instance.end_time and instance.start_time
            else None
        )
        # Return corrected duration in response
        if duration:
            data["call_duration"] = duration.total_seconds()
            if instance.call_duration != timedelta(seconds=duration.total_seconds()):
                instance.call_duration = timedelta(seconds=duration.total_seconds())
                instance.save(update_fields=["call_duration"])
        else:
            data["call_duration"] = 0
        # Handle agent
        if instance.agent:
            data["agent"] = {
                "id": instance.agent.id,
                "name": getattr(instance.agent, "name", ""),
            }
        else:
            data["agent"] = None

        # Handle space
        if instance.space:
            data["space"] = {
                "id": instance.space.id,
                "name": getattr(instance.space, "name", ""),
            }
        else:
            data["space"] = None

        # Handle organization
        if instance.organization:
            data["organization"] = {
                "id": instance.organization.id,
                "name": getattr(instance.organization, "name", ""),
            }
        else:
            data["organization"] = None

        return data
