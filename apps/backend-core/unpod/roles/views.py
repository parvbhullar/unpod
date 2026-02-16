from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets
from rest_framework.response import Response
from unpod.common.exception import APIException206
from unpod.common.renderers import UnpodJSONRenderer

from unpod.common.serializer import CommonSerializer
from unpod.roles.constants import PERMISSION_DICT, ROLES_FILEDS, TAGS_DATA, TAGS_FILEDS
from unpod.roles.models import AccountTags, RoleTypeEnum, Roles
# Create your views here.


class RoleViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def list(self, request, *args, **kwargs):
        role_type = self.kwargs.get('role_type')
        if role_type not in RoleTypeEnum.values():
            raise APIException206({"message": "Invalid Role Type"})
        roles_obj = Roles.objects.filter(role_type=role_type, is_active=True).values(*ROLES_FILEDS)
        return Response({"data": roles_obj, "message": "Role Fetch Successfully"}, status=200)

    def list_permission(self, request, *args, **kwargs):
        role_type = self.kwargs.get('role_type')
        if role_type not in PERMISSION_DICT.keys():
            raise APIException206({"message": "Invalid Role Type"})
        permission_list = PERMISSION_DICT[role_type]
        return Response({"data": permission_list, "message": "Permission Fetch Successfully"}, status=200)


class TagsViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def list(self, request, *args, **kwargs):
        tag_type = self.kwargs.get('tag_type')
        search = self.request.GET.get('search')
        if tag_type not in TAGS_DATA.keys():
            raise APIException206({"message": "Invalid Tag Type"})
        query = {
            "tag_type":tag_type,
            "is_active": True
        }
        if search and search != "":
            query.update({"name__icontains": search})
        roles_obj = AccountTags.objects.filter(**query).values(*TAGS_FILEDS)
        return Response({"data": roles_obj, "message": "Tags Fetch Successfully"}, status=200)