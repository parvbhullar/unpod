from django.db import transaction
from rest_framework import status, serializers
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Document
from .serializers import DocumentSerializer
from ..common.renderers import UnpodJSONRenderer
from ..space.models import SpaceOrganization


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]
    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        # Optional query params for filtering
        document_type = self.request.query_params.get("document_type")
        module_type = self.request.query_params.get("module_type")
        module_object_id = self.request.query_params.get("module_object_id")

        if document_type:
            queryset = queryset.filter(document_type=document_type)
        if module_type:
            queryset = queryset.filter(module_type=module_type)
        if module_object_id:
            queryset = queryset.filter(module_object_id=module_object_id)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "status_code": status.HTTP_200_OK,
            "message": "Documents retrieved successfully",
            "data": serializer.data,
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            "status_code": status.HTTP_200_OK,
            "message": "Document retrieved successfully",
            "data": serializer.data,
        })

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(
                {
                    "status_code": status.HTTP_201_CREATED,
                    "message": "Document created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED
            )

        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, 'args') and e.args else str(e),
                },
                status=status.HTTP_206_PARTIAL_CONTENT
            )

        except Exception as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, 'args') and e.args else str(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        with transaction.atomic():
            org_handle = self.request.headers.get("org-handle")

            if not org_handle:
                raise serializers.ValidationError("Missing 'org-handle' header")

            try:
                organization = SpaceOrganization.objects.get(domain_handle=org_handle)
                serializer.save(user_id=self.request.user.id, organization=organization)

            except SpaceOrganization.DoesNotExist:
                raise serializers.ValidationError(f"No organization found with domain handle '{org_handle}'")

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "message": "Document updated successfully",
                "data": serializer.data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response(
            {
                "status_code": status.HTTP_204_NO_CONTENT,
                "message": "Document deleted successfully",
                "data": None,
            },
            status=status.HTTP_204_NO_CONTENT
        )
