from django.http import Http404
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DynamicForm
from .serializers import DynamicFormSerializer
from ..common.enum import ModelBasicStatus
from ..common.renderers import UnpodJSONRenderer


class DynamicFormViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = DynamicForm.objects.all()
    serializer_class = DynamicFormSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]
    lookup_field = "slug"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(status=ModelBasicStatus.active.name)

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)

            return Response({"data": serializer.data, "message": "Dynamic Forms fetched successfully."}, status=200)

        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to fetch data.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)

            return Response({"data": serializer.data, "message": "Dynamic Form fetched successfully."}, status=200)

        except Http404 as e:
            return Response(
                {
                    "status_code": 404,
                    "message": "Dynamic Form not found.",
                    "error": str(e),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {
                    "status_code": 400,
                    "message": "Failed to fetch data.",
                    "error": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
