from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder

from unpod.common.query import unique_slugify
from unpod.dynamic_forms.models import DynamicFormValues

from unpod.common.enum import (
    TriggerEventTypes,
    FileStorage,
    MediaPrivacyType,
    MediaType,
    MediaUploadStatus,
    ObjectType,
    MediaObjectRelation,
    PilotTypes,
    PluginTypes,
    PrivacyType,
    PilotState,
    RelevantTagLinkType,
    KnowledgeBaseContentType,
    VoiceQualityChoices,
    VoiceGenderChoices,
    Regions,
    ModelBasicStatus,
    RequiredInfoOptions, ProviderType, ProvidersModelTypes, TelephonyNumberState, OwnerType, NumberType, SpaceType,
)
from unpod.common.mixin import CreatedUpdatedMixin, TimeStampedModel
from unpod.common.storage_backends import PrivateMediaStorage
from django.utils.text import slugify

from unpod.users.models import User

import uuid


class Provider(models.Model):
    name = models.CharField(
        max_length=100,
    )
    type = models.CharField(max_length=50, choices=ProviderType.choices())
    model_type = models.CharField(
        'Model Type (Deprecated)',
        max_length=50, choices=ProvidersModelTypes.choices(), blank=True, null=True
    )
    model_types = ArrayField(
        models.CharField(max_length=50, choices=ProvidersModelTypes.choices()),
        blank=True,
        default=list,
    )
    url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    icon = models.FileField(
        upload_to="private/channels",
        null=True,
        blank=True,
        storage=PrivateMediaStorage(file_overwrite=True),
    )
    form = models.ForeignKey(
        'dynamic_forms.DynamicForm', on_delete=models.SET_NULL, null=True, blank=True, related_name='providers'
    )
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
    )

    class Meta:
        db_table = "core_components_provider"
        verbose_name = "Provider"
        verbose_name_plural = "Providers"

    def __str__(self):
        return f"{self.name} ({self.type}) ({self.model_type})"


class TelephonyNumber(models.Model):
    provider = models.ForeignKey(
        Provider, on_delete=models.SET_NULL, null=True, blank=True
    )
    organization = models.ForeignKey(
        'space.SpaceOrganization', on_delete=models.SET_NULL, null=True, blank=True, related_name='telephony_numbers'
    )
    number = models.CharField(max_length=20, unique=True)
    country = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(
        "Country Code",
        max_length=10,
        blank=True,
    )
    region = models.CharField(
        max_length=50, choices=Regions.choices(), default=Regions.IN.name
    )
    active = models.BooleanField(default=True)
    state = models.CharField(max_length=50, choices=TelephonyNumberState.choices())
    agent_number = models.BooleanField(default=False)
    owner_type = models.CharField(
        max_length=50, choices=OwnerType.choices(), null=True, blank=True
    )

    number_type = models.CharField(
        max_length=50, choices=NumberType.choices(), null=True, blank=True
    )
    association = models.JSONField(default=dict, null=True, blank=True)

    class Meta:
        db_table = "core_components_telephony_number"
        verbose_name = "Telephony Number"
        verbose_name_plural = "Telephony Numbers"

    def __str__(self):
        return self.number


# fmt: off
class MediaResource(CreatedUpdatedMixin):
    sequence_number = models.IntegerField(default=0)
    object_type = models.CharField(max_length=20, default='post', choices=ObjectType.choices())
    object_id = models.CharField(db_index=True, max_length=40, null=True, blank=True)

    public_id = models.CharField(max_length=2000, default='', null=True, blank=True)
    name = models.CharField(max_length=200, default='', null=True, blank=True)
    description = models.CharField(max_length=5000, default='', null=True, blank=True)
    url = models.CharField(max_length=2000, default='', null=True, blank=True)
    media_url = models.CharField(max_length=2000, default='', null=True, blank=True)
    device_media_url = models.CharField(max_length=2000, default='', null=True, blank=True)

    file_storage_url = models.FileField(upload_to='private', null=True, blank=True, storage=PrivateMediaStorage())
    privacy_type = models.CharField(max_length=20, default='private', choices=MediaPrivacyType.choices())
    media_type = models.CharField(max_length=20, default='image', choices=MediaType.choices())
    media_relation = models.CharField(max_length=20, blank=True, null=True, choices=MediaObjectRelation.choices())
    media_metadata = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)

    lat = models.DecimalField(default=0, max_digits=8, decimal_places=4)
    lng = models.DecimalField(default=0, max_digits=8, decimal_places=4)
    is_default = models.BooleanField(default=False)
    size = models.BigIntegerField(default=0)

    media_id = models.CharField(db_index=True, max_length=40)

    storage_type = models.CharField(max_length=20, blank=True, null=True, choices=FileStorage.choices())
    storage_data = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)
    media_status = models.CharField(max_length=20, choices=MediaUploadStatus.choices(),
                                    default=MediaUploadStatus.uploaded.name)

    def __str__(self):
        return str(self.object_type) + " - " + str(self.object_id) + " - " + str(
            self.public_id)


class MediaUploadRequest(CreatedUpdatedMixin):
    file_name = models.CharField(max_length=200)
    storage_type = models.CharField(max_length=20, blank=True, null=True, choices=FileStorage.choices())
    upload_id = models.CharField(db_index=True, max_length=40)
    file_key = models.CharField(max_length=300)
    storage_response = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)
    status = models.CharField(max_length=20, choices=MediaUploadStatus.choices(),
                              default=MediaUploadStatus.created.name)
    privacy_type = models.CharField(max_length=20, default='private', choices=MediaPrivacyType.choices())

    def __str__(self) -> str:
        return f"{str(self.name)} - {self.upload_id} - {self.file_key}"


class ProfileRoles(TimeStampedModel):
    role_name = models.CharField(max_length=99)
    role_code = models.CharField(max_length=99)
    parent_role = models.CharField(max_length=99, blank=True, null=True)
    department = models.CharField(max_length=99, blank=True, null=True)

    def __str__(self) -> str:
        return f"{str(self.role_name)} - {self.department}"


class Tag(CreatedUpdatedMixin):
    name = models.CharField("Name", max_length=99)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_default = models.BooleanField("Is Default", default=False)

    def __str__(self) -> str:
        return self.name

    def _get_unique_slug(self):
        slug = slugify(self.name)
        unique_slug = slug
        num = 1
        while Tag.objects.filter(slug=unique_slug).exists():
            unique_slug = '{}-{}'.format(slug, num)
            num += 1
        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._get_unique_slug()
        self.name = self.name.title()
        super().save(*args, **kwargs)


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True, default='en')
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    status = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Voice(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    status = models.BooleanField(default=True)
    provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voices',
    )
    language = models.ManyToManyField('Language', related_name='voices')
    latency = models.CharField(max_length=50, null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Cost per minute in USD")
    realtime_sts = models.BooleanField("Realtime (STS)", default=False)
    inference = models.BooleanField("Inference", default=False)

    created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.provider.name if self.provider else ''})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            num = 1
            while Voice.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{num}"
                num += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ModelType(CreatedUpdatedMixin):
    """Model to store different types of models (LLM, Transcriber, Voice, etc.)"""
    name = models.CharField("Name", max_length=50, unique=True)
    code = models.CharField("Code", max_length=50, unique=True)

    class Meta:
        verbose_name = "Model Type"
        verbose_name_plural = "Model Types"

    def __str__(self):
        return self.name


class Model(CreatedUpdatedMixin):
    name = models.CharField("Name", max_length=99)
    description = models.TextField("Description", blank=True)
    url = models.URLField("URL", blank=True)
    languages = models.ManyToManyField('Language', related_name='core_models', verbose_name="Languages", blank=True)
    voice = models.ManyToManyField('Voice', blank=True, related_name='core_models', verbose_name="Voice")
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    codename = models.CharField("Codename", max_length=99, blank=True)
    tags = models.ManyToManyField(Tag, related_name='models')
    provider = models.ForeignKey(Provider, on_delete=models.SET_NULL, null=True, blank=True, related_name='core_models')
    token_limit = models.IntegerField(null=True, blank=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0.0,
    )
    tool_calling = models.BooleanField(
        "Supports Tool Calling",
        default=False,
        help_text="Whether this LLM model supports tool/function calling functionality"
    )
    realtime_sts = models.BooleanField("Realtime (STS)", default=False)
    inference = models.BooleanField("Inference", default=False)

    model_types = models.ManyToManyField(
        'ModelType',
        related_name='models',
        verbose_name="Model Types",
        blank=True,
        help_text="Types of the model (LLM, Transcriber, Voice, etc.)"
    )
    logo = models.FileField(upload_to='private/model', null=True, blank=True,
                            storage=PrivateMediaStorage(file_overwrite=True))
    config = models.JSONField("Config", default=dict, encoder=DjangoJSONEncoder, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Order of the model")

    def __str__(self) -> str:
        return f"{self.name} {self.provider}"

    class Meta:
        ordering = ["sort_order"]  # 👈 default order

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)

        if not self.codename:
            self.codename = self.name

        super().save(*args, **kwargs)


class Plugin(CreatedUpdatedMixin):
    owner = models.ForeignKey('space.SpaceOrganization', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='%(class)s_plugins')
    name = models.CharField("Name", max_length=99)
    description = models.TextField("Description", blank=True)
    url = models.URLField("URL", blank=True)
    functions = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)
    type = models.CharField("Type", choices=PluginTypes.choices(), max_length=99, blank=True)
    default_config = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    privacy_type = models.CharField("Privacy Type", choices=PrivacyType.choices(), default=PrivacyType.public.name,
                                    max_length=99)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    pilots = GenericRelation('core_components.PilotLink', related_query_name='plugins')
    logo = models.FileField(upload_to='private/plugin', null=True, blank=True,
                            storage=PrivateMediaStorage(file_overwrite=True))

    # tags = models.TextField("Tags", blank=True) # many to may with core comonent

    def __str__(self) -> str:
        return f"{str(self.name)} - {str(self.type)}"

    def _get_unique_slug(self):
        slug = slugify(self.name)
        unique_slug = slug
        num = 1
        while Plugin.objects.filter(slug=unique_slug).exists():
            unique_slug = '{}-{}'.format(slug, num)
            num += 1
        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._get_unique_slug()
        super().save(*args, **kwargs)


class PilotTemplateCategory(models.TextChoices):
    HR = 'hr', 'HR & Recruitment'
    SALES = 'sales', 'Sales & Lead Generation'
    SUPPORT = 'support', 'Customer Support'
    LOGISTICS = 'logistics', 'Logistics & E-commerce'
    OPERATIONS = 'operations', 'Operations & Front Desk'
    CUSTOM = 'custom', 'Custom'


class PilotTemplate(CreatedUpdatedMixin):
    """
    Predefined templates for creating Pilot agents.
    Users can select a template to quickly create a pilot with pre-configured settings.
    """
    name = models.CharField("Template Name", max_length=255)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    category = models.CharField(
        "Category",
        max_length=50,
        choices=PilotTemplateCategory.choices,
        default=PilotTemplateCategory.CUSTOM
    )
    description = models.TextField("Description", blank=True)
    thumbnail = models.FileField(
        upload_to='private/pilot_templates',
        null=True,
        blank=True,
        storage=PrivateMediaStorage(file_overwrite=True)
    )

    # Template content - maps to Pilot fields
    system_prompt = models.TextField("System Prompt", blank=True)
    ai_persona = models.TextField("AI Persona", blank=True)
    greeting_message = models.CharField("Greeting Message", max_length=500, blank=True)

    # Knowledge base schema - placeholder structure users need to fill
    knowledge_base_schema = models.JSONField(
        "Knowledge Base Schema",
        default=dict,
        encoder=DjangoJSONEncoder,
        blank=True,
        help_text="JSON schema defining the knowledge base fields user needs to fill"
    )

    # Default configurations
    config = models.JSONField(
        "Config",
        default=dict,
        encoder=DjangoJSONEncoder,
        blank=True
    )
    telephony_config = models.JSONField(
        "Telephony Config",
        default=dict,
        encoder=DjangoJSONEncoder,
        blank=True
    )

    # Template metadata
    is_active = models.BooleanField("Is Active", default=True)
    display_order = models.IntegerField("Display Order", default=0)
    use_count = models.IntegerField("Use Count", default=0)

    class Meta:
        ordering = ['display_order', '-created']
        verbose_name = "Pilot Template"
        verbose_name_plural = "Pilot Templates"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category})"


class UseCases(CreatedUpdatedMixin):
    name = models.CharField("Name", max_length=99)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField("Description", blank=True)
    icon = models.FileField(upload_to='private/use_cases', null=True, blank=True,
                            storage=PrivateMediaStorage(file_overwrite=True))
    prompt = models.TextField("Prompt", blank=True)
    skills = models.TextField("Skills", blank=True)
    required_info = ArrayField(
        models.CharField(max_length=50, choices=RequiredInfoOptions.choices()),
        blank=True,
        default=list,
    )
    # Store the full CSS gradient string
    background_gradient = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='CSS gradient value (e.g., linear-gradient(to right, #FF6B6B, #4ECDC4))'
    )

    svg_icon = models.TextField(
        blank=True,
        null=True,
        help_text='SVG icon code'
    )
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Order of the record")

    class Meta:
        ordering = ['sort_order', '-created']
        verbose_name = "Use Case"
        verbose_name_plural = "Use Cases"


    def __str__(self) -> str:
        return f"{str(self.name)}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)



class Pilot(CreatedUpdatedMixin):
    owner = models.ForeignKey('space.SpaceOrganization', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='%(class)s_pilots')
    is_root_identity = models.BooleanField("Is Root Identity", default=False)
    space = models.ForeignKey('space.Space', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='%(class)s_spaces')
    name = models.CharField("Name", max_length=99, blank=True)
    handle = models.CharField("Handle", max_length=99, blank=True)
    template = models.ForeignKey(PilotTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='pilots')
    privacy_type = models.CharField("Privacy Type", choices=PrivacyType.choices(), default=PrivacyType.public.name,
                                    max_length=99)
    description = models.TextField("Description", blank=True)
    purpose = models.CharField("Purpose", max_length=100, blank=True)
    conversation_tone = models.CharField("Conversation Tone", max_length=100, blank=True)
    type = models.CharField("Type", choices=PilotTypes.choices(), default=PilotTypes.Pilot.name, max_length=99)
    logo = models.FileField(upload_to='private/pilot', null=True, blank=True,
                            storage=PrivateMediaStorage(file_overwrite=True))
    ai_persona = models.TextField("AI Persona", blank=True)
    llm_model = models.ForeignKey(Model, null=True, blank=True, on_delete=models.SET_NULL, related_name='llm')
    embedding_model = models.ForeignKey(Model, null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='embedding')
    temperature = models.FloatField("Temperature", default=0.3)
    config = models.JSONField(blank=True, default=dict, encoder=DjangoJSONEncoder)
    state = models.CharField(choices=PilotState.choices(), default=PilotState.draft.name, max_length=99)
    ai_persona_config = models.JSONField(default=list, encoder=DjangoJSONEncoder, blank=True)
    questions = models.JSONField(default=list, encoder=DjangoJSONEncoder, blank=True)
    response_prompt = models.TextField("Response Prompt", blank=True)
    allow_user_to_change = models.BooleanField("Allow User To Change", default=False)
    tags = models.ManyToManyField(Tag, related_name='pilots')
    reaction_count = models.BigIntegerField(default=0, blank=True)
    greeting_message = models.CharField("Greeting Message", max_length=500, blank=True)
    system_prompt = models.TextField("System Prompt", blank=True)
    token = models.IntegerField("Token", default=0)
    telephony_enabled = models.BooleanField("Telephony Enabled", default=False)
    workflow_enabled = models.BooleanField("Workflow Enabled", default=False)
    telephony_config = models.JSONField("Telephony Config", default=dict, encoder=DjangoJSONEncoder, blank=True)
    numbers = models.ManyToManyField(
        TelephonyNumber,
        related_name='pilots',
        limit_choices_to={'active': True, 'state': 'NOT_ASSIGNED', 'agent_number': True},
        blank=True,
    )
    enable_memory = models.BooleanField(
        "Enable Memory",
        default=False,
        help_text="Assistant will use previous conversation memories to understand user context."
    )
    enable_followup = models.BooleanField(
        "Enable Followup",
        default=False,
    )
    followup_prompt = models.TextField("Followup Prompt", blank=True)
    enable_callback = models.BooleanField(
        "Enable Callback",
        default=False,
        help_text="If user request to callback after some time"
    )
    notify_via_sms = models.BooleanField(
        "Notify Via SMS",
        default=False,
        help_text="If assistant aren't able to connect to user via call, it will inform user via the SMS."
    )
    enable_handover = models.BooleanField(
        "Enable Handover",
        default=False,
        help_text="Enable Handover to human agent during the call"
    )
    instant_handover = models.BooleanField(
        "Instant Handover",
        default=False,
        help_text="Enable Instant Handover to human agent without any prompt during the call"
    )
    handover_number_cc = models.CharField(
        "Handover Country Code",
        max_length=10,
        blank=True,
        help_text="Country code in case of agent wants to handover the call to human"
    )
    handover_number = models.CharField(
        "Handover Number",
        max_length=150,
        blank=True,
        help_text="Incase of agent wants to handover the call to human"
    )
    handover_person_name = models.CharField(
        "Handover Person Name",
        max_length=50,
        blank=True,
        help_text="Incase of agent wants to handover the call to human"
    )
    handover_person_role = models.CharField(
        "Handover Person Role",
        max_length=50,
        blank=True,
        help_text="Incase of agent wants to handover the call to human"
    )
    handover_prompt = models.TextField("Handover Prompt", blank=True)
    region = models.CharField(max_length=50, choices=Regions.choices(), default=Regions.IN.name)

    DAYS_OPTIONS = (
        ("Mon", "Mon"),
        ("Tue", "Tue"),
        ("Wed", "Wed"),
        ("Thu", "Thu"),
        ("Fri", "Fri"),
        ("Sat", "Sat"),
        ("Sun", "Sun"),
    )
    calling_days = models.JSONField('Calling Days', default=list,null=True,blank=True)
    calling_time_ranges = models.JSONField("Calling Time Ranges", default=list,null=True,blank=True)

    # stop  speaking plan
    number_of_words = models.IntegerField("Number of Words", default=4)
    voice_seconds = models.FloatField("Voice Seconds", default=0.2)
    back_off_seconds = models.IntegerField("Back Off Seconds", default=1)
    voice_temperature = models.FloatField("Voice Temperature", default=1.1)
    voice_speed = models.FloatField("Voice Speed", default=1.0)
    voice_prompt = models.TextField("Voice Prompt", blank=True)
    realtime_evals = models.BooleanField("Realtime Evaluations", default=False)
    eval_kn_bases = models.ManyToManyField(
        'space.Space',
        related_name='eval_kb_pilots',
        limit_choices_to={'space_type': SpaceType.knowledge_base.name},
        blank=True,
    )

    class Meta:
        indexes = [
            # Organization's pilots by state (list/filter queries)
            models.Index(fields=['owner', 'state'], name='pilot_owner_state_idx'),
            # Public/private pilots by state
            models.Index(fields=['privacy_type', 'state'], name='pilot_privacy_state_idx'),
            # Filter by pilot type
            models.Index(fields=['type'], name='pilot_type_idx'),
            # Handle lookups (unique identifier)
            models.Index(fields=['handle'], name='pilot_handle_idx'),
        ]

    def __str__(self) -> str:
        return f"{str(self.name)} - {str(self.type)}"

    def save(self, *args, **kwargs):
        # Removed slug generation
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        DynamicFormValues.objects.filter(parent_id=self.handle, parent_type="agent").delete()

        super().delete(using=using, keep_parents=keep_parents)

    @property
    def link_qs(self):
        return PilotLink.objects.filter(pilot=self)


class PilotLink(CreatedUpdatedMixin):
    pilot = models.ForeignKey(Pilot, on_delete=models.CASCADE, related_name='pilot_links', null=True, blank=True)
    # space, organization, knowledgebase, plugin
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    link_config = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    slug = models.SlugField(max_length=140, unique=True, null=True)

    def __str__(self) -> str:
        return f"{self.pilot} - {self.content_object}"

    def _get_unique_slug(self):
        slug = slugify(self.pilot.name)
        unique_slug = slug
        num = 1
        while PilotLink.objects.filter(slug=unique_slug).exists():
            unique_slug = '{}-{}'.format(slug, num)
            num += 1
        return unique_slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._get_unique_slug()
        super().save(*args, **kwargs)

    def role_code(self):
        return self.link_config.get('role_code', '')

    def email(self):
        user = self.user()
        if user:
            return user.email
        return ''

    def full_name(self):
        user = self.user()
        if user:
            return user.full_name
        return ''

    def invite_by(self):
        if User.objects.filter(id=self.created_by).exists():
            return User.objects.get(id=self.created_by).full_name
        return ''

    def user(self):
        if self.content_type == ContentType.objects.get_for_model(User):
            return self.content_object
        return None


class EventsTriggerManager(CreatedUpdatedMixin):
    event_name = models.CharField(max_length=99)
    event_description = models.TextField(blank=True)
    event_type = models.CharField(max_length=99, choices=TriggerEventTypes.choices())
    event_execution = models.CharField(max_length=99)
    event_config = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)
    status = models.BooleanField(default=False)
    retry = models.IntegerField(default=0)
    message = models.TextField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.event_name} - {self.event_type}"


class RelevantTag(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "relevant_tag"
        verbose_name = "Relevant Tag"
        verbose_name_plural = "Relevant Tags"


class RelevantTagLink(models.Model):
    tag = models.ForeignKey(RelevantTag, on_delete=models.CASCADE, related_name="tag_links")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=RelevantTagLinkType.choices())
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "relevant_tag_link"
        verbose_name = "Relevant Tag Link"
        verbose_name_plural = "Relevant Tag Links"
        unique_together = ('tag', 'content_type', 'object_id', 'type')


class DefaultRelevantTag(models.Model):
    tag = models.ForeignKey(RelevantTag, on_delete=models.CASCADE, related_name="default_tag_links")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    space_content_type = models.CharField(choices=KnowledgeBaseContentType.choices(), null=True, max_length=20)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "default_relevant_tag"
        verbose_name = "Default Relevant Tag"
        verbose_name_plural = "Default Relevant Tags"

    def __str__(self):
        return f"{self.tag.name} - {self.content_type.name}"


class GlobalSystemConfig(models.Model):
    key = models.CharField(max_length=255,unique=True)
    value = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.key}"


class VoiceProfiles(models.Model):
    agent_profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    llm_provider =models.ForeignKey(Provider, on_delete=models.SET_NULL,blank=True,null=True,related_name="llm_provider",limit_choices_to={"model_type": "LLM"})
    llm_model = models.ForeignKey(Model, on_delete=models.SET_NULL,blank=True,null=True,related_name="llm_model",limit_choices_to={'provider__model_type': 'LLM'})

    stt_provider = models.ForeignKey(Provider, on_delete=models.SET_NULL,blank=True,null=True,related_name="stt_provider",limit_choices_to={"model_type": "TRANSCRIBER"})
    stt_model = models.ForeignKey(Model, on_delete=models.SET_NULL,blank=True,null=True,related_name="stt_model",limit_choices_to={'provider__model_type': 'TRANSCRIBER'})
    stt_language = models.ManyToManyField(Language, blank=True, related_name="stt_voice_profiles")

    tts_provider = models.ForeignKey(Provider, on_delete=models.SET_NULL,blank=True,null=True,related_name="tts_provider",limit_choices_to={"model_type": "VOICE"})
    tts_model = models.ForeignKey(Model, on_delete=models.SET_NULL,blank=True,null=True,related_name="tts_model",limit_choices_to={'provider__model_type': 'VOICE'})
    tts_voice = models.ForeignKey(Voice, on_delete=models.SET_NULL,blank=True,null=True,related_name="tts_voice")
    voice_temperature = models.FloatField("Voice Temperature", default=1.1)
    voice_speed = models.FloatField("Voice Speed", default=1.0)
    tts_language = models.ManyToManyField(Language, blank=True, related_name="voice_profiles")
    greeting_message = models.TextField(max_length=2000, blank=True)
    temperature = models.FloatField("Temperature", default=0.3)
    gender = models.TextField(max_length=1, choices=VoiceGenderChoices.choices(), default=VoiceGenderChoices.F.name)
    quality = models.TextField(max_length=20, choices=VoiceQualityChoices.choices())
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Cost per minute in USD"
    )
    latency = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(max_length=200)
    voice_prompt = models.TextField("Voice Prompt", blank=True)
    status = models.CharField(
        max_length=20,
        choices=ModelBasicStatus.choices(),
        default=ModelBasicStatus.active.name,
    )
    sort_order = models.PositiveIntegerField(default=0, help_text="Order of the profile")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Voice Profile"
        verbose_name_plural = "Voice Profiles"
        ordering = ["sort_order"]  # 👈 default order


class SampleFile(CreatedUpdatedMixin):
    file_name = models.CharField(max_length=255)
    file_slug = models.SlugField(max_length=255, unique=True)
    file_url = models.FileField(upload_to='private/sample-files', storage=PrivateMediaStorage(file_overwrite=True))
    file_type = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.file_slug:
            self.file_slug = slugify(self.file_name)
        if not self.file_type:
            self.file_type = self.file_url.name.split('.')[-1]
        if not self.file_size:
            self.file_size = self.file_url.size
        super().save(*args, **kwargs)
