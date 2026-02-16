import os

from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.db import models

from unpod.common.enum import MediaType, DataObjectStatus, DataObjectSource, StatusEnum
from unpod.common.mixin import CreatedUpdatedMixin
from unpod.common.storage_backends import PrivateMediaStorage
from unpod.common.uuid import generate_uuid
from unpod.space import models as space_models
from model_utils.models import TimeStampedModel


def get_upload_path(instance, filename):
    """
    s3/{organization_id}/{space_slug}/{content_type}
    """
    return os.path.join(
        settings.AWS_PRIVATE_MEDIA_LOCATION,
        "knowledge-base",
        instance.knowledge_base.space_organization.domain_handle,
        instance.knowledge_base.slug,
        instance.knowledge_base.content_type,
        filename,
    )


class DataObjectFile(CreatedUpdatedMixin):
    knowledge_base = models.ForeignKey(
        space_models.Space,
        on_delete=models.SET_NULL,
        related_name="%(class)s_data",
        null=True,
    )
    name = models.CharField(max_length=99, db_index=True)
    file = models.FileField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
        storage=PrivateMediaStorage(),
        max_length=256,
    )
    token = models.CharField(max_length=100, db_index=True, default=generate_uuid)
    object_type = models.CharField(
        max_length=20, default=MediaType.file.name, choices=MediaType.choices()
    )
    content = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
    status = models.CharField(
        max_length=20,
        default=DataObjectStatus.ready.name,
        choices=DataObjectStatus.choices(),
    )
    source = models.CharField(
        max_length=20,
        default=DataObjectSource.imported.name,
        choices=DataObjectSource.choices(),
    )
    reference_url = models.URLField(blank=True, null=True)
    data_loader_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class KnowledgeBaseConfig(CreatedUpdatedMixin):
    knowledge_base = models.OneToOneField(
        space_models.Space,
        on_delete=models.CASCADE,
        related_name="%(class)s",
        null=True,
        blank=True,
    )
    schema = models.JSONField(default=dict, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.knowledge_base}"


class KnowledgeBaseEvals(TimeStampedModel):
    eval_name = models.CharField(max_length=100)
    eval_type = models.CharField(max_length=20)
    linked_handle = models.CharField(max_length=50)
    last_gen = models.DateTimeField(auto_now_add=True)
    gen_status = models.CharField(
        max_length=20, default="pending", choices=StatusEnum.choices()
    )
    eval_data = models.JSONField(
        default=dict, encoder=DjangoJSONEncoder, blank=True, null=True
    )
