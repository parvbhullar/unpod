from rest_framework import serializers
from .models import Document
from unpod.common.storage_backends import imagekitBackend


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id',
            'module_type',
            'module_object_id',
            'document_type',
            'file',
            'status',
            'version',
            'user_id',
            'organization',
            'uploaded_at',
        ]
        extra_kwargs = {
            'organization': {'read_only': True, 'required': False},
        }

    def get_file_url(self, obj):
        if obj.file:
            return imagekitBackend.generateURL(obj.file.name)
        return None
