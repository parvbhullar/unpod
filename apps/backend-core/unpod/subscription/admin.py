from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportActionModelAdmin

from unpod.common.mixin import UnpodCustomModelAdmin
from unpod.subscription.forms import (
    SubscriptionAdminForm,
    SubscriptionModuleInlineForm,
    ActiveSubscriptionAdminForm,
    ActiveSubscriptionDetailInlineForm,
)
from unpod.subscription.models import (
    ActiveSubscription,
    PlanModules,
    Subscription,
    SubscriptionModules,
    SubscriptionRequest,
    SubscriptionInvoice,
    ActiveSubscriptionDetail,
    SubscriptionUsageHistory,
)
from unpod.subscription.services import (
    get_subscription_info,
    get_subscription_modules,
    add_active_subscription_detail,
)


# Register your models here.


@admin.register(PlanModules)
class PlanModulesModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    list_display = ["name", "codename", "unit", "cost", "description"]
    list_filter = ["unit"]
    search_fields = ["name", "codename", "unit"]

    # Enable autocomplete for this model
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )
        return queryset, use_distinct


class SubscriptionModulesInline(admin.TabularInline):
    """
    Inline admin for managing subscription modules with allocation and costs
    """

    model = SubscriptionModules
    form = SubscriptionModuleInlineForm
    extra = 0
    fields = [
        "module",
        "included_in_sub",
        "display_name",
        "description",
        "is_unlimited",
        "quantity",
        "price_type",
        "cost",
        "tax_percentage",
        "tax_code",
        "include_in_billing",
    ]
    autocomplete_fields = ["module"]

    verbose_name = "Module Allocation"
    verbose_name_plural = "Module Allocations & Costs"


@admin.register(Subscription)
class SubscriptionModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    form = SubscriptionAdminForm
    inlines = [SubscriptionModulesInline]

    list_display = [
        "name",
        "price",
        "discount",
        "is_default",
        "is_active",
        "product_id",
        "type",
        "sort_order",
    ]
    list_editable = ["is_active", "sort_order"]  # editable directly in list
    list_filter = ["is_active", "product_id", "type", "currency"]
    search_fields = ["name", "description"]

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "tagline",
                    "help_text",
                    "description",
                    "product_id",
                    "type",
                    "is_popular",
                    "is_active",
                    "is_default",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": ("price", "discount", "final_price", "currency"),
                "description": "Set the base price and discount for the subscription plan.",
            },
        ),
        (
            "Additional Data",
            {
                "fields": (
                    "sort_order",
                    "custom_data",
                ),
                "classes": ("collapse",),
                "description": "JSON field for storing additional custom configuration.",
            },
        ),
    )

    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to add any additional logic when saving
        SubscriptionModules inline data.
        """
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()

        # delete any removed instances
        for instance in formset.deleted_objects:
            instance.delete()

        # Get the subscription instance
        module_price = 0

        subscription = form.instance
        modules = subscription.subscriptionmodules_subscription.all()
        for module in modules:
            amount = (
                float(module.cost) * float(module.quantity)
                if module.price_type == "per_unit" or module.is_unlimited
                else float(module.cost)
            )
            tax_amount = amount * (float(module.tax_percentage) / 100)
            total_cost = amount + tax_amount
            module_price += total_cost

        # Update the subscription price to include module costs
        if module_price > 0:
            subscription.price = module_price
            subscription.save()


@admin.register(SubscriptionRequest)
class SubscriptionRequestModelAdmin(UnpodCustomModelAdmin):
    list_display = [
        "id",
        "subscription",
        "organization",
        "product_id",
        "user",
        "message",
        "resolved",
        "created_at",
    ]
    list_filter = ["resolved", "subscription"]
    search_fields = ["user__username", "subscription__name", "organization__name"]


@admin.register(SubscriptionModules)
class SubscriptionModulesModelAdmin(
    ImportExportActionModelAdmin, UnpodCustomModelAdmin
):
    list_display = [
        "module",
        "quantity",
        "cost",
        "tax_percentage",
        "tax_code",
        "subscription",
    ]
    list_filter = ["module", "subscription"]


class ActiveSubscriptionDetailInline(admin.TabularInline):
    """
    Inline admin for managing user-specific module allocations and costs.
    Data entered here will be automatically synced to subscription_metadata.modules
    """

    model = ActiveSubscriptionDetail
    form = ActiveSubscriptionDetailInlineForm
    can_delete = False
    extra = 0
    fields = [
        "module",
        "display_name",
        "allocated",
        "price_type",
        "cost",
        "is_unlimited",
        "include_in_billing",
    ]
    readonly_fields = ["codename", "display_name", "consumed", "price_type"]
    autocomplete_fields = ["module"]

    verbose_name = "Module Allocation & Cost"
    verbose_name_plural = "Module Allocations & Costs"

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        """
        Get existing module details. If they exist in metadata but not in DB,
        they will be created by the ActiveSubscription.save() method.
        """
        qs = super().get_queryset(request)
        return qs


@admin.register(ActiveSubscription)
class ActiveSubscriptionModelAdmin(ImportExportActionModelAdmin, UnpodCustomModelAdmin):
    form = ActiveSubscriptionAdminForm
    inlines = [ActiveSubscriptionDetailInline]

    list_display = [
        "subscription",
        "user",
        "organization",
        "product_id",
        "is_active",
        "expired",
        "billing_mode",
        "valid_from",
        "valid_to",
        "customize_action",
    ]
    list_filter = ["is_active", "expired", "subscription", "billing_mode"]
    search_fields = [
        "user__username",
        "user__email",
        "subscription__name",
        "organization__name",
    ]

    fieldsets = (
        (
            "User & Subscription",
            {
                "fields": ("user", "subscription", "organization", "product_id"),
                "description": "Select the user and subscription plan. Organization and Product ID are required.",
            },
        ),
        (
            "Custom Pricing",
            {
                "fields": ("price", "discount", "final_price"),
                "description": "Override the default subscription price for this specific user.",
            },
        ),
        (
            "Subscription Status",
            {
                "fields": ("is_active", "expired", "expired_on", "billing_mode"),
            },
        ),
        (
            "Validity Period",
            {
                "fields": ("valid_from", "valid_to"),
                "description": "Set the date range for this subscription.",
            },
        ),
        ("Audit Information", {"fields": ("created_by", "updated_by")}),
        (
            "Metadata",
            {
                "fields": ("subscription_metadata",),
                "classes": ("collapse",),
                "description": "JSON metadata for storing module configurations and custom settings. Module data from "
                "inline will be saved here in 'modules' key.",
            },
        ),
    )

    def customize_action(self, obj):
        """Custom action button to quickly customize a user's subscription"""
        url = reverse("admin:subscription_activesubscription_change", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Customize</a>',
            url,
        )

    customize_action.short_description = "Actions"
    customize_action.allow_tags = True

    def save_model(self, request, obj, form, change):
        """Override save to sync module data to subscription_metadata"""
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        """
        Override save_formset to sync ActiveSubscriptionDetail data
        to subscription_metadata.modules
        """
        instances = formset.save(commit=False)

        # Get the active subscription instance
        active_subscription = form.instance
        modules = get_subscription_modules(active_subscription.subscription)

        # Initialize metadata structure
        if not active_subscription.subscription_metadata:
            active_subscription.subscription_metadata = {}

        if "modules" not in active_subscription.subscription_metadata:
            active_subscription.subscription_metadata = {
                "subscription_details": get_subscription_info(
                    active_subscription.subscription
                ),
                "modules": modules,
                "order": {
                    "order_id": None,
                    "offer_id": None,
                    "online_order_id": None,
                    "subscription_id": active_subscription.subscription.id,
                },
            }

            add_active_subscription_detail(active_subscription, modules)
        else:
            # Get existing modules from metadata
            modules = active_subscription.subscription_metadata.get("modules", {})

        # Save each inline instance and sync to metadata
        for instance in instances:
            instance.save()

            # Sync to subscription_metadata.modules
            if instance.module:
                module_name = instance.module.name
                saved_module = modules.get(module_name, {})
                modules[module_name] = {
                    **saved_module,
                    "quantity": instance.allocated,
                    "cost": instance.cost,
                    "is_unlimited": instance.is_unlimited,
                    "include_in_billing": instance.include_in_billing,
                }

        module_price = 0
        for module in modules.values():
            cost = module.get("cost", 0.0)
            quantity = module.get("quantity", 0)
            is_unlimited = module.get("is_unlimited", False)
            price_type = module.get("price_type", "fixed")
            tax_percentage = module.get("tax_percentage", 0.0)

            amount = (
                float(cost) * float(quantity)
                if price_type == "per_unit" or is_unlimited
                else float(cost)
            )
            tax_amount = amount * (float(tax_percentage) / 100)
            total_cost = amount + tax_amount
            module_price += total_cost

        # Update overall subscription price in metadata
        price = form.cleaned_data.get("price", 0.0)
        discount = form.cleaned_data.get("discount", 0.0)
        final_price = price

        if module_price > 0:
            active_subscription.subscription_metadata["subscription_details"][
                "price"
            ] = float(module_price)
            final_price = module_price
        else:
            active_subscription.subscription_metadata["subscription_details"][
                "price"
            ] = float(price)

        if discount:
            active_subscription.subscription_metadata["subscription_details"][
                "discount"
            ] = float(discount)
            final_price = max(0.0, module_price - float(discount))

        if final_price >= 0:
            active_subscription.subscription_metadata["subscription_details"][
                "final_price"
            ] = float(final_price)

        # Save the updated metadata
        active_subscription.save()


@admin.register(ActiveSubscriptionDetail)
class ActiveSubscriptionDetailModelAdmin(
    ImportExportActionModelAdmin, UnpodCustomModelAdmin
):
    list_display = [
        "act_subscription",
        "organization",
        "product_id",
        "module",
        "codename",
        "allocated",
        "consumed",
        "cost",
        "is_unlimited",
        "usage_percentage",
        "reset_date",
    ]
    list_filter = ["module", "act_subscription", "warning_threshold"]
    search_fields = [
        "module__name",
        "act_subscription__subscription__name",
        "organization__name",
        "organization__token",
    ]
    readonly_fields = ["usage_percentage"]

    def usage_percentage(self, obj):
        return f"{round(obj.usage_percentage, 2)}%"

    usage_percentage.short_description = "Usage %"


@admin.register(SubscriptionUsageHistory)
class SubscriptionUsageHistoryModelAdmin(
    ImportExportActionModelAdmin, UnpodCustomModelAdmin
):
    list_display = [
        "act_subscription",
        "organization",
        "product_id",
        "amount",
        "created_at",
    ]
    list_filter = ["product_id"]
    search_fields = [
        "act_subscription__subscription__name",
        "organization__name",
    ]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"


@admin.register(SubscriptionInvoice)
class SubscriptionInvoiceModelAdmin(
    ImportExportActionModelAdmin, UnpodCustomModelAdmin
):
    list_display = [
        "invoice_number",
        "amount",
        "status",
        "charge_type",
        "act_subscription",
        "organization",
        "product_id",
        "invoice_date",
        "due_date",
    ]
    list_filter = ["invoice_date", "due_date", "status", "charge_type"]
    search_fields = [
        "invoice_number",
        "notes",
        "act_subscription__subscription__name",
        "act_subscription__subscription__user__email",
        "organization__name",
    ]
    date_hierarchy = "invoice_date"
    list_editable = ["charge_type"]  # editable directly in list
