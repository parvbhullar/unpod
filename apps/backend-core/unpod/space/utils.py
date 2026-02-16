from django.db.models import Q, Count, F
from django.db.models.functions import Coalesce
from unpod.common.constants import DATETIME_FORMAT
from unpod.common.enum import PrivacyType, SpaceType
from unpod.common.exception import APIException206
from unpod.common.mixin import UsableRequest
from unpod.common.storage_backends import imagekitBackend
from unpod.roles.services import generateRefObject, getRole, getUserFinalRole
from unpod.space.models import (
    OrganizationMemberRoles,
    Space,
    SpaceMemberRoles,
    SpaceOrganization,
)
from unpod.users.utils import get_name


def generateSpaceRole(space, user, role_code):
    space_role = UsableRequest()
    space_role.space = space
    space.user = user
    space_role.role = getRole(role_code, "space")
    return space_role


def checkSpaceAccess(
    user, space=None, token=None, check_role=False, custom_message=None
):
    query = {}
    space_obj = None
    if user.is_authenticated:
        query.update({"user_id": user.id})
    if space:
        if space.privacy_type == PrivacyType.public.name and not check_role:
            space_role = generateSpaceRole(space, user, "viewer")
            return space_role
        query.update({"space_id": space.id})
    elif token:
        space_obj = Space.objects.filter(token=token).first()
        if not space_obj:
            raise APIException206({"message": "Invalid Space Token"})
        if (
            space_obj
            and space_obj.privacy_type == PrivacyType.public.name
            and not check_role
        ):
            space_role = generateSpaceRole(space_obj, user, "viewer")
            return space_role
        query.update({"space__token": token})
    if not user.is_authenticated:
        raise APIException206(
            {"message": "You Don't have Access to this Space OR Not Logged In"}
        )
    space = space or space_obj
    ref_dict = generateRefObject("space", space)
    ref_dict["id"] = space.id
    final_role = getUserFinalRole(user, "space", ref_dict)
    space_role = (
        SpaceMemberRoles.objects.filter(**query)
        .select_related("space", "user", "role")
        .first()
    )
    if final_role == "owner":
        if space_role:
            space_role.role = getRole("owner", "space")
        else:
            space_role = generateSpaceRole(space, user, final_role)
    if not space_role:
        raise APIException206(
            {"message": custom_message or "You Don't have Access to this Space"}
        )
    return space_role


def checkSpaceOperationAccess(user, space_role):
    if not user.is_authenticated:
        raise APIException206(
            {
                "message": "You Don't have Access to do operation to this Space OR Not Logged In"
            }
        )
    if not space_role:
        raise APIException206(
            {"message": f"You Don't have Access to do operation to this Space"}
        )
    if (
        space_role.space.privacy_type == PrivacyType.public.name
        and space_role.role.role_code not in ["owner", "editor"]
    ):
        raise APIException206(
            {"message": f"You Don't have Access to do operation to this Space"}
        )

    if space_role.role.role_code not in ["owner", "editor"]:
        raise APIException206(
            {"message": f"You Don't have Access to do operation to this Space"}
        )

    return space_role


def checkSpaceMemberAccess(user, space_role):
    if not user.is_authenticated:
        raise APIException206(
            {"message": "You Don't have Access to this Organization OR Not Logged In"}
        )

    if not space_role:
        raise APIException206({"message": "You Don't have Access to this Organization"})

    if (
        space_role.space.privacy_type == PrivacyType.public.name
        and space_role.role.role_code not in ["viewer", "editor"]
    ):
        raise APIException206(
            {"message": "You Don't have Access to do operation to this Organization"}
        )

    if space_role.role.role_code not in ["viewer", "editor"]:
        raise APIException206(
            {"message": "You Don't request to change role in this Organization"}
        )

    return space_role


def checkPostSpaceAccess(
    user, space=None, token=None, check_op=False, from_request=None
):
    if space and space.privacy_type == PrivacyType.public.name:
        if check_op:
            if from_request == "thread":
                return space
            space_role = checkSpaceAccess(
                user,
                space=space,
                check_role=True,
                custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
            )
            checkSpaceOperationAccess(user, space_role)
        return space
    if token:
        space_obj = Space.objects.filter(token=token).first()
        if not space_obj:
            raise APIException206({"message": "Invalid Space Token"})
        if space_obj and space_obj.privacy_type == PrivacyType.public.name:
            if check_op:
                if from_request == "thread":
                    return space_obj
                space_role = checkSpaceAccess(
                    user,
                    space=space_obj,
                    check_role=True,
                    custom_message="You Don't have Access to this Space, You can't do any operation to this Space",
                )
                checkSpaceOperationAccess(user, space_role)
            return space_obj
    query = {"user_id": user.id}
    space = space or space_obj
    query.update({"space_id": space.id})
    ref_dict = generateRefObject("space", space)
    ref_dict["id"] = space.id
    final_role = getUserFinalRole(user, "space", ref_dict)
    space_role = (
        SpaceMemberRoles.objects.filter(**query)
        .select_related("space", "user", "role")
        .first()
    )
    if final_role == "owner":
        space_role = generateSpaceRole(space, user, final_role)
    if final_role and not space_role and not check_op:
        space_role = generateSpaceRole(space, user, "viewer")
    if not space_role:
        raise APIException206({"message": "You Don't have Access to this Space"})
    return space_role.space


def getAllSpaceQuery(request, space_type, case=None):
    query = Q(space_type=space_type)
    if request.user.is_authenticated:
        if case:
            if case in ["all", "home"]:
                space_query = Q(
                    user=request.user,
                    space__privacy_type__in=["shared", "link", "public"],
                    role__role_code__in=["viewer", "editor", "owner"],
                )
                space_query = space_query | Q(
                    user=request.user,
                    space__privacy_type="private",
                    role__role_code="owner",
                )
            elif case == "shared":
                space_query = Q(
                    user=request.user,
                    space__privacy_type__in=["shared", "link"],
                    role__role_code__in=["viewer", "editor"],
                )
        else:
            space_query = Q(
                user=request.user,
                space__privacy_type__in=["shared", "link", "public"],
                role__role_code__in=["viewer", "editor", "owner"],
            )
            space_query = space_query | Q(
                user=request.user,
                space__privacy_type="private",
                role__role_code="owner",
            )
        space_objs = (
            SpaceMemberRoles.objects.filter(space__space_type=space_type)
            .filter(space_query)
            .values_list("space_id", flat=True)
        )
        query.add(Q(id__in=space_objs), Q.OR)
        if case in ["all", "home"] or not case:
            query.add(
                Q(privacy_type=PrivacyType.public.name, space_type=space_type), Q.OR
            )
    else:
        query.add(Q(privacy_type=PrivacyType.public.name, space_type=space_type), Q.OR)
    # query.add(Q(privacy_type=PrivacyType.public.name), Q.OR)
    return query


def getAllSpaceQuerySet(
    request, bypass_org=False, case=None, space_type=SpaceType.general.name
):
    domain_handle = request.headers.get("Org-Handle", None)
    print("domain_handle", domain_handle)
    if (not domain_handle or domain_handle == "") and not bypass_org:
        print("raise Ex", "No Ex", domain_handle)
        raise APIException206({"message": "Please provide Organization handle"})
    org_check = None
    if request.user.is_authenticated:
        org_check = (
            OrganizationMemberRoles.objects.filter(
                user=request.user, organization__domain_handle=domain_handle
            )
            .select_related("organization")
            .first()
        )
    if org_check and org_check.role.role_code == "owner":
        query = Q(space_type=space_type)
    elif org_check and org_check.role.role_code == "editor":
        query = Q(
            privacy_type__in=[PrivacyType.public.name, PrivacyType.shared.name],
            space_type=space_type,
        )
    else:
        query = getAllSpaceQuery(request, space_type=space_type, case=case)
    spaceOrg = None
    if not bypass_org:
        spaceOrg = checkSpaceOrg(domain_handle)
    if (
        request.user.is_authenticated
        and not bypass_org
        and spaceOrg
        and spaceOrg.privacy_type != PrivacyType.public.name
    ):
        if not org_check:
            raise APIException206(
                {"message": "You don't have the access to this Organization"}
            )
        space_set = Space.objects.filter(
            query, space_organization_id=org_check.organization.id, status="active"
        ).prefetch_related("threadpost_space", "threadpost_space__threadpostview_post")
        return space_set
    if not bypass_org:
        query = query & Q(space_organization__domain_handle=domain_handle)
    if case == "home":
        if request.user.is_authenticated:
            ord_ids = OrganizationMemberRoles.objects.filter(
                user=request.user
            ).values_list("organization_id", flat=True)
            query = query & Q(space_organization_id__in=list(ord_ids))
        else:
            query = query & Q(space_organization_id__in=[])
    space_set = Space.objects.filter(query, status="active").prefetch_related(
        "threadpost_space", "threadpost_space__threadpostview_post"
    )
    return space_set


def checkSpaceSlug(space_slug):
    space_obj = (
        Space.objects.filter(slug=space_slug, status="active")
        .select_related("space_organization")
        .prefetch_related("spacememberroles_space", "spaceinvite_space")
        .first()
    )
    if not space_obj:
        raise APIException206({"message": "Invalid Space Token"})
    return space_obj


def get_space_by_query(**query):
    space = Space.objects.filter(**query).select_related("space_organization").first()
    return space


def get_space_access_request(obj):
    members_emails = list(
        obj.spacememberroles_space.all().values_list("user__email", flat=True)
    )

    users = (
        obj.spaceaccessrequest_space.filter(
            is_joined=False, request_verified=False, is_expired=False
        )
        .order_by("-id")
        .values(
            "user__email",
            "user__first_name",
            "user__last_name",
            "role__role_code",
            "request_token",
            "created",
            "is_expired",
        )
    )
    users_data = []
    for user in users:
        users_data.append(
            {
                "email": user["user__email"],
                "full_name": get_name(
                    user["user__first_name"], user["user__last_name"]
                ),
                "role": user["role__role_code"],
                "joined": False,
                "is_member": user["user__email"] in members_emails,
                "request_token": user["request_token"],
                "request_date": user["created"].strftime(DATETIME_FORMAT),
                "expired": user["is_expired"],
            }
        )
    return users_data


def get_organization_access_request(obj):
    members_emails = list(
        obj.organizationmemberroles_organization.all().values_list(
            "user__email", flat=True
        )
    )

    users = (
        obj.organizationaccessrequest_organization.filter(
            is_joined=False, request_verified=False, is_expired=False
        )
        .order_by("-id")
        .values(
            "user__email",
            "user__first_name",
            "user__last_name",
            "role__role_code",
            "request_token",
            "created",
            "is_expired",
        )
    )
    users_data = []
    for user in users:
        users_data.append(
            {
                "email": user["user__email"],
                "full_name": get_name(
                    user["user__first_name"], user["user__last_name"]
                ),
                "role": user["role__role_code"],
                "joined": False,
                "is_member": user["user__email"] in members_emails,
                "request_token": user["request_token"],
                "request_date": user["created"].strftime(DATETIME_FORMAT),
                "expired": user["is_expired"],
            }
        )
    return users_data


def get_space_annotate_query(space_querset, request):
    space_querset = space_querset.annotate(
        public_read_count=Coalesce(
            Count(
                "threadpost_space__id",
                distinct=True,
                filter=(
                    ~Q(threadpost_space__postblocklist_post__user_id=request.user.id)
                    & Q(
                        threadpost_space__post_rel__in=["main_post", "seq_post"],
                        threadpost_space__is_deleted=False,
                        threadpost_space__privacy_type="public",
                        threadpost_space__threadpostview_post__user_id=str(
                            request.user.id
                        ),
                    )
                ),
            ),
            0,
        ),
        public_total_post=Coalesce(
            Count(
                "threadpost_space__id",
                distinct=True,
                filter=(
                    Q(
                        threadpost_space__post_rel__in=["main_post", "seq_post"],
                        threadpost_space__is_deleted=False,
                        threadpost_space__privacy_type="public",
                    )
                ),
            ),
            0,
        ),
        private_read_count=Coalesce(
            Count(
                "threadpost_space__id",
                distinct=True,
                filter=(
                    ~Q(threadpost_space__postblocklist_post__user_id=request.user.id)
                    & Q(
                        threadpost_space__post_rel__in=["main_post", "seq_post"],
                        threadpost_space__is_deleted=False,
                        threadpost_space__privacy_type__in=[
                            "private",
                            "shared",
                            "link",
                        ],
                        threadpost_space__threadpostpermission_post__user_id=request.user.id,
                        threadpost_space__threadpostview_post__user_id=str(
                            request.user.id
                        ),
                    )
                ),
            ),
            0,
        ),
        private_total_post=Coalesce(
            Count(
                "threadpost_space__id",
                distinct=True,
                filter=(
                    Q(
                        threadpost_space__post_rel__in=["main_post", "seq_post"],
                        threadpost_space__is_deleted=False,
                        threadpost_space__privacy_type__in=[
                            "private",
                            "shared",
                            "link",
                        ],
                        threadpost_space__threadpostpermission_post__user_id=request.user.id,
                    )
                ),
            ),
            0,
        ),
        blocked_post=Coalesce(
            Count(
                "threadpost_space__postblocklist_post__id",
                distinct=True,
                filter=Q(
                    threadpost_space__postblocklist_post__user_id=request.user.id,
                    threadpost_space__is_deleted=False,
                ),
            ),
            0,
        ),
        unread_count=Coalesce(
            (
                F("public_total_post")
                + F("private_total_post")
                - F("public_read_count")
                - F("blocked_post")
                - F("private_read_count")
            ),
            0,
        ),
        total_post=Coalesce(F("public_total_post") + F("private_total_post"), 0),
    )
    return space_querset


def get_last_thread(private_slug, public_slug):
    if private_slug is None and public_slug is None:
        return None
    if not all([private_slug, public_slug]):
        return private_slug or public_slug
    else:
        private_id = int(private_slug.split("-")[-1])
        public_id = int(public_slug.split("-")[-1])
        return private_slug if private_id > public_id else public_slug


def checkSpaceOrg(domain_handle):
    org_check = SpaceOrganization.objects.filter(
        domain_handle=domain_handle, status="active"
    ).first()
    if not org_check:
        raise APIException206({"message": "Invalid Domain Handle"})
    return org_check


def checkOrgAccess(user, org, check_role=False):
    query = {}
    if org.privacy_type == PrivacyType.public.name and not check_role:
        return org
    if user.is_authenticated:
        query.update({"user_id": user.id})
    query.update({"organization_id": org.id})
    if not user.is_authenticated:
        raise APIException206(
            {"message": "You Don't have Access to this Organization OR Not Logged In"}
        )
    org_role = (
        OrganizationMemberRoles.objects.filter(**query)
        .select_related("organization", "user", "role")
        .first()
    )
    if not org_role and not org_role:
        raise APIException206({"message": "You Don't have Access to this Organization"})
    return org_role


def checkOrgOperationAccess(user, org_role):
    if not user.is_authenticated:
        raise APIException206(
            {
                "message": "You Don't have Access to do operation to this Organization OR Not Logged In"
            }
        )
    if not org_role:
        raise APIException206(
            {"message": "You Don't have Access to do operation to this Organization"}
        )
    if (
        org_role.organization.privacy_type == PrivacyType.public.name
        and org_role.role.role_code not in ["owner", "editor"]
    ):
        raise APIException206(
            {
                "message": f"You Don't have Access to do operation to this public Organization"
            }
        )
    if org_role.role.role_code not in ["owner", "editor"]:
        raise APIException206(
            {"message": f"You Don't have Access to do operation to this Organization"}
        )
    return org_role


def checkOrgMemberAccess(user, org_role):
    if not user.is_authenticated:
        raise APIException206(
            {"message": "You Don't have Access to this Organization OR Not Logged In"}
        )

    if not org_role:
        raise APIException206({"message": "You Don't have Access to this Organization"})

    if (
        org_role.organization.privacy_type == PrivacyType.public.name
        and org_role.role.role_code not in ["viewer", "editor"]
    ):
        raise APIException206(
            {"message": "You Don't have Access to do operation to this Organization"}
        )

    if org_role.role.role_code not in ["viewer", "editor"]:
        raise APIException206(
            {"message": "You Don't request to change role in this Organization"}
        )

    return org_role


def get_space_users(space_obj, user):
    if not user or not user.is_authenticated:
        return []
    users = space_obj.spacememberroles_space.all().select_related(
        "user", "role", "user__userbasicdetail_user"
    )
    users_data = []
    for user in users:
        user_data = {
            "email": user.user.email,
            "full_name": user.user.full_name,
            "role": user.role.role_code,
            "join_date": user.created.strftime(DATETIME_FORMAT),
            "joined": True,
        }
        if hasattr(user.user, "userbasicdetail_user"):
            user_data["profile_color"] = user.user.userbasicdetail_user.profile_color
        if hasattr(user.user, "userbasicdetail_user"):
            if user.user.userbasicdetail_user.profile_picture:
                user_data["profile_picture"] = imagekitBackend.generateURL(
                    user.user.userbasicdetail_user.profile_picture.name
                )
        users_data.append(user_data)
    return users_data
