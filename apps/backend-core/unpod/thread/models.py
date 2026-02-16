from django.db import models
from model_utils.models import TimeStampedModel
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from datetime import datetime, timedelta
from unpod.common.enum import (
    ObjectType,
    PostContentType,
    PostExtraContentType,
    PostRelation,
    PostStatus,
    PostType,
    PrivacyType,
    ReactionType,
    RecordingVideoStatus,
    PostRepeatType,
)
from unpod.common.mixin import CreatedUpdatedMixin, SoftDeleteModelMixin
from unpod.common.query import get_model_unique_code
from unpod.space.models import Space
from unpod.roles.models import Roles


class ThreadTag(TimeStampedModel):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name


class ThreadPost(CreatedUpdatedMixin, SoftDeleteModelMixin):
    main_post = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="%(class)s_main_post",
        null=True,
        blank=True,
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.SET_NULL,
        related_name="%(class)s_space",
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="%(class)s_parent",
        null=True,
        blank=True,
        default=None,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=999, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=250, blank=True, null=True)

    seq_number = models.BigIntegerField(default=0)
    post_rel = models.CharField(
        max_length=20,
        default="main_post",
        choices=PostRelation.choices(),
        db_index=True,
    )
    post_type = models.CharField(
        max_length=50, blank=True, null=True, choices=PostType.choices(), db_index=True
    )
    content_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=PostContentType.choices(),
        db_index=True,
    )
    extra_content_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=PostExtraContentType.choices(),
        db_index=True,
    )

    cover_image = models.URLField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True, default="")

    privacy_type = models.CharField(
        max_length=99, choices=PrivacyType.choices(), default=PrivacyType.public.name
    )

    post_status = models.CharField(
        max_length=99, choices=PostStatus.choices(), default=PostStatus.draft.name
    )
    recording_status = models.CharField(max_length=50, blank=True, null=True)

    post_link = models.CharField(blank=True, null=True, max_length=999)

    content = models.TextField(blank=True, null=True)
    media = models.BooleanField(default=False)
    media_data = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    attachments = models.BooleanField(default=False)

    scheduled = models.BooleanField(default=False)
    schedule_datetime = models.DateTimeField(blank=True, null=True)

    # post_id = models.CharField(db_index=True, max_length=40)

    post_id = models.BigIntegerField(db_index=True, default=0)

    slug = models.CharField(db_index=True, max_length=499, blank=True, null=True)

    post_count = models.IntegerField(default=0, blank=True)
    reply_count = models.IntegerField(default=0, blank=True)

    view_count = models.BigIntegerField(default=0, blank=True)
    reaction_count = models.BigIntegerField(default=0, blank=True)

    is_live = models.BooleanField(default=False)
    live_id = models.IntegerField(blank=True, null=True)

    related_data = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    block = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )

    ref_doc_id = models.CharField(max_length=99, blank=True, null=True, db_index=True)
    ref_collection = models.CharField(
        max_length=99, blank=True, null=True, db_index=True
    )

    class Meta:
        indexes = [
            # Composite index for list queries (space + post_rel + post_status)
            models.Index(fields=['space', 'post_rel', 'post_status'], name='thread_list_idx'),
            # Ordering index for created timestamp queries
            models.Index(fields=['space', '-created'], name='thread_created_idx'),
            # User posts index
            models.Index(fields=['user', 'post_rel'], name='thread_user_idx'),
            # Active posts index (filtering by deletion status)
            models.Index(fields=['post_rel', 'is_deleted'], name='thread_active_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.post_id}... {self.pk}"


class ThreadPostPermission(CreatedUpdatedMixin):
    role = models.ForeignKey(
        Roles,
        on_delete=models.SET_NULL,
        related_name="%(class)s_role",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.SET_NULL,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    grant_by = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.post} - {self.user} - {self.role}"


class ThreadPostReaction(CreatedUpdatedMixin):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.SET_NULL,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    reaction_type = models.CharField(
        db_index=True, max_length=10, default="like", choices=ReactionType.choices()
    )
    object_type = models.CharField(
        max_length=20, default="post", choices=ObjectType.choices()
    )
    object_id = models.CharField(db_index=True, max_length=40, null=True, blank=True)
    reaction_at = models.DateTimeField(auto_now=True)
    reaction_count = models.IntegerField(default=1)

    def __str__(self):
        return self.reaction_type


class ThreadPostView(CreatedUpdatedMixin):
    user_id = models.CharField(max_length=40, blank=True, null=True)
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.CASCADE,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    view_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{str(self.post)}-{str(self.user_id)}"


class ThreadPostAccessRequest(CreatedUpdatedMixin):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.SET_NULL,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    role = models.ForeignKey(
        Roles,
        on_delete=models.SET_NULL,
        related_name="%(class)s_role",
        null=True,
        blank=True,
    )
    request_token = models.CharField(
        max_length=40, blank=True, null=True, db_index=True
    )
    valid_from = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    request_verified = models.BooleanField(default=False)
    request_verify_dt = models.DateTimeField(blank=True, null=True)
    is_joined = models.BooleanField(default=False)
    joined_dt = models.DateTimeField(blank=True, null=True)
    is_expired = models.BooleanField(default=False)

    def save(self, *args, **kwargs) -> None:
        if not self.request_token:
            self.request_token = get_model_unique_code(
                self.__class__, "request_token", N=16
            )
        return super().save(*args, **kwargs)


class PostInvite(CreatedUpdatedMixin):
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.SET_NULL,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    role = models.ForeignKey(
        Roles,
        on_delete=models.SET_NULL,
        related_name="%(class)s_role",
        null=True,
        blank=True,
    )
    invite_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_invite_by",
        null=True,
        blank=True,
    )
    invite_token = models.CharField(max_length=40, blank=True, null=True)
    valid_upto = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    user_email = models.EmailField(blank=True, null=True)
    invite_verified = models.BooleanField(default=False)
    invite_verify_dt = models.DateTimeField(blank=True, null=True)
    is_joined = models.BooleanField(default=False)
    joined_dt = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs) -> None:
        if not self.invite_token:
            self.invite_token = get_model_unique_code(
                self.__class__, "invite_token", N=20
            )
        return super().save(*args, **kwargs)


class PostReport(CreatedUpdatedMixin):
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.CASCADE,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    category = models.CharField(max_length=40)
    message = models.TextField(blank=True, null=True)


class PostBlockList(CreatedUpdatedMixin):
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.CASCADE,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    post_report = models.ForeignKey(
        PostReport,
        on_delete=models.CASCADE,
        related_name="%(class)s_post_report",
        null=True,
        blank=True,
    )


class PostCommunicationActivity(CreatedUpdatedMixin):
    post = models.ForeignKey(
        ThreadPost,
        on_delete=models.CASCADE,
        related_name="%(class)s_post",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    channel_name = models.CharField(max_length=199, blank=True, null=True)
    live_status = models.BooleanField(default=False)
    start_dt = models.DateTimeField(blank=True, null=True)
    end_dt = models.DateTimeField(blank=True, null=True)
    activity_config = models.JSONField(default=dict, encoder=DjangoJSONEncoder)

    def __str__(self) -> str:
        return f"{str(self.post)}-{str(self.channel_name)}"

    @property
    def hms_room_id(self):
        return self.activity_config.get("session_data", {}).get("id")


class PostSessionRecording(CreatedUpdatedMixin):
    session = models.ForeignKey(
        PostCommunicationActivity,
        on_delete=models.CASCADE,
        related_name="%(class)s_user",
        null=True,
        blank=True,
    )
    recording_status = models.BooleanField(default=False)
    agora_sid = models.CharField(max_length=500, default="", null=True, blank=True)
    agora_resource_id = models.TextField(default="", null=True, blank=True)
    agora_sids = models.CharField(max_length=1000, default="", null=True, blank=True)
    recording_reponse = models.JSONField(
        default=dict, blank=True, encoder=DjangoJSONEncoder
    )
    agora_recording_files = models.JSONField(
        default=dict, blank=True, encoder=DjangoJSONEncoder
    )
    aws_recording_files = models.JSONField(
        default=dict, blank=True, encoder=DjangoJSONEncoder
    )
    recording_video_status = models.CharField(
        max_length=20, default="not_processed", choices=RecordingVideoStatus.choices()
    )
    post_created = models.BooleanField(default=False)


class PostCreationCronModel(CreatedUpdatedMixin):
    user_id = models.IntegerField()
    space_token = models.CharField(max_length=40)
    title = models.CharField(max_length=999, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    privacy_type = models.CharField(
        max_length=99, choices=PrivacyType.choices(), default=PrivacyType.public.name
    )
    post_type = models.CharField(
        max_length=99, choices=PostType.choices(), default=PostType.ask.name
    )
    content_type = models.CharField(
        max_length=99,
        choices=PostContentType.choices(),
        default=PostContentType.text.name,
    )
    pilot = models.CharField(max_length=99, default="superpilot")
    post_id = models.BigIntegerField(db_index=True, default=0)
    post_created = models.BooleanField(default=False)
    retry = models.IntegerField(default=0)
    success = models.BooleanField(default=False)
    response = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    message = models.TextField(blank=True, null=True)
    extra_data = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    schedule_timestamp = models.IntegerField(null=True)
    repeat_schedule = models.BooleanField(default=True)
    repeat_type = models.CharField(
        max_length=99,
        choices=PostRepeatType.choices(),
        default=PostRepeatType.never.name,
    )

    def save(self, *args, **kwargs):
        # Set the default to 5 minutes from now only if the field is not provided
        if not self.schedule_timestamp:
            self.schedule_timestamp = (
                datetime.now() + timedelta(minutes=5)
            ).timestamp()
        super(PostCreationCronModel, self).save(*args, **kwargs)


class PostCronResultModel(CreatedUpdatedMixin):
    post_creation_cron = models.ForeignKey(
        PostCreationCronModel,
        on_delete=models.CASCADE,
        related_name="%(class)s_post_creation_cron",
        null=True,
        blank=True,
    )
    post_created = models.BooleanField(default=False)
    success = models.BooleanField(default=False)
    post_id = models.BigIntegerField(db_index=True, default=0)
    response = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    message = models.TextField(blank=True, null=True)
    extra_data = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
