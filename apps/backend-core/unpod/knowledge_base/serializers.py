import json

from rest_framework import serializers

from unpod.common.enum import MediaType
from unpod.common.exception import APIException206
from unpod.common.file import getFileType, getS3FileURLFromURL
from unpod.knowledge_base import models as knowledge_base_models
from unpod.knowledge_base.utils import check_file_extension, upload_store_file


class DataFileListSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(
            max_length=100000, allow_empty_file=False, use_url=False
        )
    )

    def create(self, validated_data):
        files = validated_data.pop("files")
        knowledge_base = self.context["knowledge_base"]
        data_objs = []
        for file in files:
            if not check_file_extension(file.name, knowledge_base.content_type):
                raise APIException206(
                    {
                        "message": f"Invalid file extension for this collection type - {knowledge_base.content_type}"
                    }
                )
            object_type = getFileType(file.name)
            content = {}
            if object_type == MediaType.json.name:
                content = json.load(file)
            data_objs.append(
                knowledge_base_models.DataObjectFile(
                    file=file,
                    name=file.name,
                    knowledge_base=knowledge_base,
                    object_type=object_type,
                    content=content,
                    **validated_data,
                )
            )
        if data_objs:
            knowledge_base_models.DataObjectFile.objects.bulk_create(data_objs)
        try:
            saved_data = []
            for index, data in enumerate(data_objs):
                res = upload_store_file(
                    knowledge_base, {"url": getS3FileURLFromURL(data.file.url)}
                )

                saved_data.append(res)

            return saved_data
        except Exception as ex:
            print(ex)

        return {}


class DataObjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = knowledge_base_models.DataObjectFile
        fields = [
            "name",
            "file",
            "object_type",
            "content",
            "status",
            "source",
            "reference_url",
            "data_loader_id",
            "token",
        ]
