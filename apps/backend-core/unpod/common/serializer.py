from rest_framework import serializers
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class CommonSerializer(serializers.Serializer):
    pass


class RestrictedFileField(serializers.FileField):
    """
    Same as FileField, but you can specify:
    * content_types - list containing allowed content_types. Example: ['application/pdf', 'image/jpeg']
    * max_upload_size - a number indicating the maximum file size allowed for upload.
        2.5MB - 2621440
        5MB - 5242880
        10MB - 10485760
        20MB - 20971520
        50MB - 5242880
        100MB - 104857600
        250MB - 214958080
        500MB - 429916160
"""

    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop("content_types")
        self.max_upload_size = kwargs.pop("max_upload_size")

        super(RestrictedFileField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        file_object = super().to_internal_value(data)
        try:
            content_type = file_object.content_type
            if content_type in self.content_types:
                if file_object.size > self.max_upload_size:
                    raise ValidationError(_('Please keep filesize under %s. Current filesize %s') % (
                        filesizeformat(self.max_upload_size), filesizeformat(file_object._size)))
            else:
                raise ValidationError(_('Filetype not supported.'))
        except AttributeError:
            pass
        return data