import json
from django.conf import settings
import requests
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response


from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.serializer import CommonSerializer
from unpod.knowledge_base import (
    models as knowledge_base_models,
    serializers as knowledge_base_serializers,
)
from unpod.knowledge_base.utils import get_collection_type, get_document_tasks
from unpod.space.utils import checkPostSpaceAccess, checkSpaceAccess


class DataView(CreateAPIView):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    def create(self, request, *args, **kwargs):
        token = kwargs.get("token")
        space = checkPostSpaceAccess(request.user, token=token, check_op=True)
        context = {"request": request, "knowledge_base": space}
        serializer = knowledge_base_serializers.DataFileListSerializer(
            data=request.data, context=context
        )
        if serializer.is_valid():
            instance = serializer.save()
            return Response(
                {"data": instance, "message": "Files Saved Successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"message": "There is some Validation error", "errors": serializer.errors},
            status=206,
        )


class DataListView(ListAPIView):
    serializer_class = knowledge_base_serializers.DataObjectFileSerializer
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (
        MultiPartParser,
        FormParser,
    )
    http_method_names = ("get",)

    def get_queryset(self):
        token = self.kwargs.get("token")
        try:
            knowledge_role = checkSpaceAccess(
                self.request.user,
                token=token,
                custom_message="You Don't have Access to this Knowledge Base",
            )
        except Exception as ex:
            if (
                str(ex.detail.get("message"))
                == "You Don't have Access to this Knowledge Base"
            ):
                return knowledge_base_models.DataObjectFile.objects.none()
        return knowledge_base_models.DataObjectFile.objects.filter(
            knowledge_base=knowledge_role.space
        )


class DataIndexView(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]
    http_method_names = ("get",)

    def index(self, request, *args, **kwargs):
        token = kwargs.get("token")
        object_token = self.request.GET.get("token")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        params = {"brain_id": knowledge_base.slug, "token": object_token}
        headers = {"Authorization": request.headers.get("Authorization")}
        current_url_api = f"memory/index/"
        hit = requests.get(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}",
            headers=headers,
            params=params,
            timeout=30,
        )
        data = json.loads(hit.content)
        return Response(data)


class StoreServiceView(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def get_collection_data(self, request, *args, **kwargs):
        token = kwargs.get("token")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        # headers = {"Authorization": request.headers.get("Authorization")}
        current_url_api = f"store/collection-data/{token}/"
        query_params = request.query_params.dict()
        hit = requests.get(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}",
            params=query_params,
            timeout=30,
        )

        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data)

    def upload_status(self, request, *args, **kwargs):
        token = kwargs.get("token")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        # headers = {"Authorization": request.headers.get("Authorization")}
        current_url_api = f"store/upload-status/{token}/"
        hit = requests.get(url=f"{settings.API_SERVICE_URL}/{current_url_api}", timeout=30)
        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data)

    def get_connector_data(self, request, *args, **kwargs):
        token = kwargs.get("token")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        # headers = {"Authorization": request.headers.get("Authorization")}
        current_url_api = f"store/collection-connector-data/{token}/"
        query_params = request.query_params.dict()
        hit = requests.get(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}",
            params=query_params,
            timeout=30,
        )

        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data)

    def get_doc_data(self, request, *args, **kwargs):
        token = kwargs.get("token")
        document_id = kwargs.get("document_id")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        # headers = {"Authorization": request.headers.get("Authorization")}
        current_url_api = f"store/collection-doc-data/{token}/{document_id}/"
        query_params = request.query_params.dict()
        hit = requests.get(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}",
            params=query_params,
            timeout=30,
        )

        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data)

    def update_doc_data(self, request, *args, **kwargs):
        token = kwargs.get("token")
        document_id = kwargs.get("document_id")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        current_url_api = f"store/collection-doc-data/{token}/{document_id}"
        hit = requests.post(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}",
            json=request.data,
            params=request.query_params.dict(),
            timeout=30,
        )

        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data)

    def delete_doc_data(self, request, *args, **kwargs):
        token = kwargs.get("token")
        document_id = kwargs.get("document_id")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        current_url_api = f"store/collection-doc-data/{token}/{document_id}"
        hit = requests.delete(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}",
            params=request.query_params.dict(),
            timeout=30,
        )

        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data)

    def create_doc_data(self, request, *args, **kwargs):
        token = kwargs.get("token")
        knowledge_base = checkPostSpaceAccess(
            self.request.user, token=token, check_op=True
        )
        current_url_api = f"store/collection-doc-data/{token}"
        config_data = {
            "name": knowledge_base.name,
            "desc": knowledge_base.description or knowledge_base.name,
            "collection_type": get_collection_type(knowledge_base.content_type),
            "org_id": knowledge_base.space_organization.id,
            "token": knowledge_base.token,
            "fields": {},
        }
        json_data = request.data
        json_data["config"] = config_data
        hit = requests.post(
            url=f"{settings.API_SERVICE_URL}/{current_url_api}", json=json_data, timeout=30
        )

        hit.raise_for_status()
        data = json.loads(hit.content)
        return Response(data, status=status.HTTP_201_CREATED)

    def get_document_tasks(self, request, *args, **kwargs):
        token = kwargs.get("token")
        document_id = kwargs.get("document_id")
        checkPostSpaceAccess(self.request.user, token=token, check_op=True)

        count, data = get_document_tasks(document_id, request.query_params.dict())

        return Response(
            {
                "message": "Document Tasks fetched successfully",
                "count": count,
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
