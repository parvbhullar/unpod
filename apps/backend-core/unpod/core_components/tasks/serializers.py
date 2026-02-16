from rest_framework import serializers


class TaskRunSerializer(serializers.Serializer):
    pilot = serializers.CharField()
    context = serializers.CharField()
    documents = serializers.ListField(child=serializers.DictField())
    schedule = serializers.DictField(required=False)
    filters = serializers.DictField(required=False)
