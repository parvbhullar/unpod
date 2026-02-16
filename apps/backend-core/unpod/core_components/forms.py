from django import forms
from django.conf import settings

from unpod.common.enum import RequiredInfoOptions, ProvidersModelTypes
from unpod.core_components.models import UseCases, VoiceProfiles, Pilot, Provider
from unpod.space.models import SpaceOrganization
from unpod.users.models import User

class ProviderAdminForm(forms.ModelForm):
    model_types = forms.MultipleChoiceField(
        choices=ProvidersModelTypes.choices(),
        widget=forms.SelectMultiple,
        required=False,
    )

    class Meta:
        model = Provider
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the initial value from the instance's ArrayField
        if self.instance and self.instance.pk:
            self.fields["model_types"].initial = self.instance.model_types or []

class UseCasesAdminForm(forms.ModelForm):
    required_info = forms.MultipleChoiceField(
        choices=RequiredInfoOptions.choices(),
        widget=forms.SelectMultiple,
        # or forms.CheckboxSelectMultiple
        required=False,
    )

    class Meta:
        model = UseCases
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial value from the instance's ArrayField
        if self.instance and self.instance.pk:
            self.fields["required_info"].initial = self.instance.required_info or []


class VoiceProfileAdminForm(forms.ModelForm):
    voice_temperature = forms.DecimalField(
        required=False,
        min_value=0.7,
        max_value=1.5,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.1",
                "placeholder": "Voice Temperature",
            }
        ),
    )

    voice_speed = forms.DecimalField(
        required=False,
        min_value=0.5,
        max_value=1.5,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.05",
                "placeholder": "Voice Speed",
            }
        ),
    )

    class Meta:
        model = VoiceProfiles
        fields = "__all__"


class PilotAdminForm(forms.ModelForm):
    voice_temperature = forms.DecimalField(
        required=False,
        min_value=0.7,
        max_value=1.5,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.1",
                "placeholder": "Voice Temperature",
            }
        ),
    )

    voice_speed = forms.DecimalField(
        required=False,
        min_value=0.5,
        max_value=1.5,
        widget=forms.NumberInput(
            attrs={
                "class": "vTextField",
                "step": "0.05",
                "placeholder": "Voice Speed",
            }
        ),
    )

    class Meta:
        model = Pilot
        fields = "__all__"


class ImportPilotForm(forms.Form):
    pilot_handle = forms.CharField(max_length=100, required=True, label="Pilot Handle")
    organization = forms.ModelChoiceField(
        queryset=SpaceOrganization.objects.all().order_by("-id"),
        required=True,
        label="Organization",
        widget=forms.Select(
            attrs={
                "class": "select2-field",
                "data-placeholder": "Search Organization...",
            }
        ),
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("-id"),
        required=True,
        widget=forms.Select(
            attrs={"class": "select2-field", "data-placeholder": "Search User..."}
        ),
    )
    DOMAIN_CHOICES = [
        ("qa", "QA Environment"),
        ("production", "Production Environment"),
    ]

    """Add Local Environment option if in local environment"""
    if getattr(settings, "ENV_NAME", "Prod").lower() == "local":
        DOMAIN_CHOICES += [
            ("local", "Local Environment"),
        ]

    import_from = forms.ChoiceField(
        choices=DOMAIN_CHOICES,
        required=True,
        label="Import From",
    )
    jwt_token = forms.CharField(widget=forms.Textarea, required=True, label="JWT Token")
