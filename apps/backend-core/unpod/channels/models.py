from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.text import slugify

from unpod.common.mixin import CreatedUpdatedMixin, SoftDeleteModelMixin
from unpod.common.storage_backends import PrivateMediaStorage

# fmt:off


class App(CreatedUpdatedMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    icon = models.FileField(upload_to='private/channels', null=True, blank=True, storage=PrivateMediaStorage(file_overwrite=True))
    is_active = models.BooleanField(default=True)
    slug = models.CharField(db_index=True, max_length=199, blank=True, null=True)
    config = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "App Definition"
        verbose_name_plural = "App Definitions"


class AppConnectorConfig(CreatedUpdatedMixin, SoftDeleteModelMixin):
    organization = models.ForeignKey('space.SpaceOrganization', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_app_configs')
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='%(class)s_app_configs')
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    configuration = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)
    state = models.CharField(blank=True, null=True, max_length=255, default='active')

    def __str__(self):
        return f"AppConnectorConfig for {self.app.name}"

    class Meta:
        verbose_name = "App Connector Configuration"
        verbose_name_plural = "App Connector Configurations"


class AppConnectRequest(CreatedUpdatedMixin):
    request_id = models.CharField(max_length=255, unique=True)
    app = models.ForeignKey(App, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    config = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True, null=True)
    status = models.CharField(max_length=255, default='pending')

    def __str__(self):
        return f"AppConnectRequest for {self.app.name}"

    class Meta:
        verbose_name = "App Connect Request"
        verbose_name_plural = "App Connect Requests"


class AppConfigLink(CreatedUpdatedMixin):
    app_config = models.ForeignKey(AppConnectorConfig, on_delete=models.CASCADE, related_name='app_config_links', null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    # space, knowledgebase
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    link_config = models.JSONField(default=dict, encoder=DjangoJSONEncoder, blank=True)

    def __str__(self) -> str:
        return f"{self.app_config} - {self.content_object}"
