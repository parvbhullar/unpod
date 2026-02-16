"""
Custom forms for subscription management in Django Admin
"""
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from unpod.subscription.models import (
    Subscription,
    SubscriptionModules,
    ActiveSubscription,
    ActiveSubscriptionDetail,
)

User = get_user_model()


class SubscriptionAdminForm(forms.ModelForm):
    """
    Custom admin form for Subscription model that allows:
    - Modifying plan price
    - Modifying plan discount
    - Editing description and custom data with better
    """

    final_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.01",
                "placeholder": "Final price",
                # "readonly": "readonly",
            }
        ),
        help_text="Calculated as Price - Discount (automatically updated).",
    )

    class Meta:
        model = Subscription
        fields = "__all__"
        widgets = {
            "price": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "step": "0.01",
                    "min": "0",
                    "default": 0.00,
                }
            ),
            "discount": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "step": "0.01",
                    "min": "0",
                    "default": 0.00,
                }
            ),
            "final_price": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "step": "0.01",
                    "min": "0",
                    # "readonly": "readonly",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "cols": 60,
                }
            ),
            "custom_data": forms.Textarea(
                attrs={
                    "rows": 6,
                    "cols": 60,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make name and product_id required
        self.fields["name"].required = True
        self.fields["tagline"].required = True
        self.fields["product_id"].required = True

        # Pre-populate final_price based on price and discount
        if self.instance:
            price = self.instance.price
            discount = self.instance.discount
            self.fields["final_price"].initial = price - discount

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get("price")
        discount = cleaned_data.get("discount")

        # Validate that discount is not greater than price
        if discount and price and discount > price:
            raise ValidationError("Discount cannot be greater than price.")

        return cleaned_data

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError("Price cannot be negative.")
        return price

    def clean_discount(self):
        discount = self.cleaned_data.get("discount")
        if discount is not None and discount < 0:
            raise ValidationError("Discount cannot be negative.")
        return discount


class SubscriptionModuleInlineForm(forms.ModelForm):
    """
    Custom inline form for SubscriptionModules that allows:
    - Modifying module allocation (quantity)
    - Modifying module cost
    - Setting tax percentage and tax code
    """

    class Meta:
        model = SubscriptionModules
        fields = "__all__"
        widgets = {
            "quantity": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "placeholder": "Enter quantity",
                    "min": "0",
                }
            ),
            "cost": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "tax_percentage": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "tax_code": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "placeholder": "TAX code",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make name and product_id required
        self.fields["display_name"].required = True

    def clean_cost(self):
        cost = self.cleaned_data.get("cost")
        if cost is not None and cost < 0:
            raise ValidationError("Cost cannot be negative.")
        return cost

    def clean_tax_percentage(self):
        tax_percentage = self.cleaned_data.get("tax_percentage")
        if tax_percentage is not None:
            if tax_percentage < 0:
                raise ValidationError("Tax percentage cannot be negative.")
            if tax_percentage > 100:
                raise ValidationError("Tax percentage cannot exceed 100%.")
        return tax_percentage

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        return quantity


class ActiveSubscriptionAdminForm(forms.ModelForm):
    """
    Custom admin form for ActiveSubscription model.
    This form allows modifying ActiveSubscription details including
    custom pricing via subscription_metadata.
    """

    price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.01",
                "default": 0.00,
                "placeholder": "Price",
            }
        ),
        help_text="Leave empty to use default price from the subscription plan.",
    )

    discount = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.01",
                "default": 0.00,
                "placeholder": "Discount",
            }
        ),
        help_text="Leave empty to use default discount from the subscription plan.",
    )

    final_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.01",
                "placeholder": "Final price",
                "readonly": "readonly",
            }
        ),
        help_text="Calculated as Price - Discount (automatically updated).",
    )

    class Meta:
        model = ActiveSubscription
        fields = [
            "user",
            "subscription",
            "organization",
            "product_id",
            "is_active",
            "billing_mode",
            "valid_from",
            "valid_to",
            "created_by",
            "updated_by",
            "subscription_metadata",
        ]
        widgets = {
            "user": forms.Select(attrs={"class": "vTextField"}),
            "subscription": forms.Select(attrs={"class": "vTextField"}),
            "organization": forms.Select(attrs={"class": "vTextField"}),
            "product_id": forms.TextInput(attrs={"class": "vTextField"}),
            "billing_mode": forms.Select(attrs={"class": "vTextField"}),
            # "valid_from": forms.DateTimeInput(
            #     attrs={"class": "vTextField", "type": "datetime-local"}
            # ),
            # "valid_to": forms.DateTimeInput(
            #     attrs={"class": "vTextField", "type": "datetime-local"}
            # ),
            "created_by": forms.NumberInput(attrs={"class": "vTextField"}),
            "updated_by": forms.NumberInput(attrs={"class": "vTextField"}),
            "subscription_metadata": forms.Textarea(
                attrs={"rows": 8, "cols": 60, "class": "vLargeTextField"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make organization and product_id required
        self.fields["user"].required = True
        self.fields["subscription"].required = True
        self.fields["organization"].required = True
        self.fields["product_id"].required = True

        # Pre-populate custom price from subscription_metadata.subscription_details.price
        if self.instance and self.instance.subscription_metadata:
            subscription_details = self.instance.subscription_metadata.get(
                "subscription_details", {}
            )
            price = round(subscription_details.get("price", 0.00), 2)
            discount = round(subscription_details.get("discount", 0.00), 2)
            final_price = round(subscription_details.get("final_price", 0.00), 2)

            self.fields["price"].initial = price
            self.fields["discount"].initial = discount
            self.fields["final_price"].initial = final_price

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")

        # Validate date range
        if valid_from and valid_to and valid_from >= valid_to:
            raise ValidationError("Valid from date must be before valid to date.")

        price = cleaned_data.get("price")
        discount = cleaned_data.get("discount")

        # Validate that discount is not greater than price
        if discount and price and discount > price:
            raise ValidationError("Discount cannot be greater than price.")

        return cleaned_data

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price < 0:
            raise ValidationError("Price cannot be negative.")
        return price

    def clean_discount(self):
        discount = self.cleaned_data.get("discount")
        if discount is not None and discount < 0:
            raise ValidationError("Discount cannot be negative.")
        return discount

    def clean_valid_from(self):
        valid_from = self.cleaned_data.get("valid_from")
        if valid_from is None:
            raise ValidationError("Valid from date is required.")
        return valid_from

    def clean_valid_to(self):
        valid_to = self.cleaned_data.get("valid_to")
        if valid_to is None:
            raise ValidationError("Valid to date is required.")
        return valid_to

    def save(self, commit=True):
        instance = super().save(commit=False)

        if commit:
            instance.save()

        return instance


class ActiveSubscriptionDetailInlineForm(forms.ModelForm):
    """
    Inline form for customizing module allocations and costs
    for a specific user's active subscription.
    Data entered here will be saved to both ActiveSubscriptionDetail
    and subscription_metadata.modules
    """

    class Meta:
        model = ActiveSubscriptionDetail
        fields = [
            "module",
            "display_name",
            "allocated",
            "price_type",
            "cost",
            "is_unlimited",
            "include_in_billing",
        ]
        widgets = {
            "module": forms.Select(attrs={"class": "vTextField"}),
            "display_name": forms.TextInput(
                attrs={
                    "class": "vTextField",
                    "placeholder": "Module display name",
                }
            ),
            "allocated": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "min": "0",
                    "placeholder": "Enter allocation amount",
                }
            ),
            "cost": forms.NumberInput(
                attrs={
                    "class": "vTextField",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Cost per unit",
                }
            ),
            "is_unlimited": forms.CheckboxInput(attrs={"class": "vCheckboxLabel"}),
            "include_in_billing": forms.CheckboxInput(
                attrs={"class": "vCheckboxLabel"}
            ),
        }

    def clean_allocated(self):
        allocated = self.cleaned_data.get("allocated")
        if allocated is not None and allocated < 0:
            raise ValidationError("Allocated amount cannot be negative.")
        return allocated

    def clean_cost(self):
        cost = self.cleaned_data.get("cost")
        if cost is not None and cost < 0:
            raise ValidationError("Cost cannot be negative.")
        return cost
