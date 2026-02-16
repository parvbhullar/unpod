from django.db import models
from unpod.common.mixin import CreatedUpdatedMixin
from unpod.common.string import get_random_string
from unpod.common.uuid import generate_uuid

# Create your models here.
class Notification(CreatedUpdatedMixin):
    title = models.CharField(max_length=999, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    user_from = models.CharField(max_length=250, blank=True, null=True, db_index=True)
    user_to = models.CharField(max_length=250, blank=True, null=True, db_index=True)
    read = models.BooleanField(default=False, db_index=True)
    object_type = models.CharField(max_length=40, blank=True, null=True, db_index=True)
    object_id = models.CharField(max_length=40, blank=True, null=True)
    event = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    event_data = models.JSONField(blank=True, null=True, default=dict)
    token = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    expired = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs) -> None:
        if not self.token:
            self.token = (get_random_string(None, length=4) + generate_uuid()[:12]).upper()
        return super().save(*args, **kwargs)
