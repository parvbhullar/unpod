import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from unpod.common.enum import DocumentType, DocumentStatus
from unpod.common.storage_backends import PrivateMediaStorage
from unpod.space.models import SpaceOrganization


def validate_file_size(file):
    max_size_mb = 5
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Max file size is {max_size_mb}MB")


def validate_file_extension(file):
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}")


def get_upload_path(instance, filename):
    """
    s3/{organization_id}/{space_slug}/{content_type}
    """
    print("inst", instance, filename)
    return os.path.join(
        settings.AWS_PRIVATE_MEDIA_LOCATION,
        "documents",
        instance.module_type,
        str(instance.module_object_id),
        instance.document_type,
        filename,
    )


class Document(models.Model):
    module_type = models.CharField(
        max_length=255,
        help_text="Type of module this document is linked to"
    )
    module_object_id = models.CharField(
        max_length=255,
        help_text="Object ID of the module instance"
    )

    document_type = models.CharField(
        max_length=100,
        choices=DocumentType.choices()
    )
    other_document_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the document"
    )

    file = models.FileField(
        upload_to=get_upload_path,
        null=True,
        blank=True,
        storage=PrivateMediaStorage(),
        max_length=256,
    )
    status = models.CharField(
        max_length=50,
        choices=DocumentStatus.choices(),
        default=DocumentStatus.review.name
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    user_id = models.BigIntegerField(
        blank=True,
        null=True,
        help_text="User who uploaded the document"
    )
    organization = models.ForeignKey(
        SpaceOrganization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.module_type} - {self.document_type} - {self.other_document_name or 'No Name'}"

    def save(self, *args, **kwargs) -> None:
        if not self.file:
            raise ValidationError("File field cannot be empty")

        validate_file_size(self.file)
        validate_file_extension(self.file)

        if not self.module_type or not self.module_object_id:
            raise ValidationError("Module type and object ID must be provided")

        if self.document_type == DocumentType.OTHER.name and not self.other_document_name:
            raise ValidationError("Other document name must be provided when document type is 'OTHER'")

        super().save(*args, **kwargs)
