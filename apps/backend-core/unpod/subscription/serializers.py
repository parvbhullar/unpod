from typing import Dict, List, Any
from rest_framework import serializers

from unpod.common.datetime import get_formated_date
from unpod.subscription.constants import PLAN_LIST_FIELDS
from unpod.subscription.models import (
    Subscription,
    ActiveSubscriptionDetail,
    SubscriptionInvoice,
)


class ModuleSerializer(serializers.Serializer):
    """Serializer for module data in subscription plans."""

    quantity = serializers.IntegerField()
    module_name = serializers.CharField(source="module.name")
    unit = serializers.CharField(source="module.unit")
    description = serializers.CharField(source="module.description")


class PlanListSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans with optimized queries."""

    modules = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [*PLAN_LIST_FIELDS, "modules"]
        # Add select_related and prefetch_related in the view's queryset instead of here

    def get_modules(self, instance) -> List[Dict[str, Any]]:
        """
        Get serialized modules data with optimized query.

        The view should use prefetch_related to optimize this:
        Subscription.objects.prefetch_related(
            Prefetch('subscriptionmodules_subscription__module',
                   queryset=PlanModules.objects.only('name', 'unit', 'description'))
        )
        """
        return [
            {
                "module_id": mod.module.id,
                "module_name": mod.module.name,
                "codename": mod.module.codename,
                "description": mod.module.description,
                "quantity": mod.quantity,
                "unit": mod.module.unit,
                "cost": mod.cost,
                "tax_percentage": mod.tax_percentage,
                "tax_code": mod.tax_code,
            }
            for mod in instance.subscriptionmodules_subscription.select_related(
                "module"
            ).all()
        ]

    @staticmethod
    def get_table_data() -> List[Dict[str, Any]]:
        """Get static table data for plans."""
        return [
            {
                "plan": "Standard",
                "title": "Standard",
                "description": "Standard Plan for Startups and Small Business with some additional features",
                "price": 9.99,
                "is_custom": False,
                "custom_price": None,
                "features": [],
            }
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            "id",
            "name",
            "price",
            "description",
            "type",
        ]
        read_only_fields = fields


class ActiveSubscriptionDetailSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source="module.name", read_only=True)

    class Meta:
        model = ActiveSubscriptionDetail
        fields = [
            "id",
            "module_name",
            "display_name",
            "codename",
            "allocated",
            "consumed",
            "unit",
            "price_type",
            "cost",
            "tax_percentage",
            "is_unlimited",
            "include_in_billing",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Convert numeric fields to float for consistency
        for field in ["cost", "tax_percentage"]:
            if representation.get(field) is not None:
                representation[field] = (
                    float(representation[field]) if representation[field] else 0.0
                )

        # Calculate remaining usage
        representation["remaining"] = (
            "Unlimited"
            if instance.is_unlimited
            else max(0, int(instance.allocated) - int(instance.consumed))
        )

        # Add extra cost if applicable
        representation["total_cost"] = instance.get_extra_total()
        representation["display_name"] = instance.display_name or (
            instance.module.name if instance.module else ""
        )

        return representation


class SubscriptionInvoiceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionInvoice
        fields = [
            "id",
            "invoice_number",
            "amount",
            "status",
            "invoice_date",
            "due_date",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Convert numeric fields to float for consistency
        for field in ["amount"]:
            if representation.get(field) is not None:
                representation[field] = (
                    float(representation[field]) if representation[field] else 0.0
                )

        # Format dates to ISO 8601 strings
        for date_field in ["invoice_date", "due_date"]:
            if representation[date_field]:
                datetime = instance.__dict__[date_field]
                representation[date_field] = get_formated_date(datetime)

        return representation
