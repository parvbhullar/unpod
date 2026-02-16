import json

from django.core.cache import cache

from unpod.common.exception import APIException206
from unpod.common.helpers.global_helper import get_current_user
from unpod.notification.services import createNotification
from unpod.roles.constants import ROLE_BASED_INDEX
from unpod.roles.models import Roles
from unpod.roles.permissions_manager import PermissionManager, UserPermission, Entity


def getRole(role_code, role_type):
    role = Roles.objects.filter(
        role_code=role_code, role_type=role_type, is_active=True
    ).first()
    if not role:
        raise APIException206({"message": "Invalid Role Code"})
    return role


def getAllRoleDict(role_type) -> dict:
    roles = Roles.objects.filter(role_type=role_type, is_active=True)
    role_dict = {}
    for role in roles:
        role_dict[role.role_code] = role
    return role_dict


def createPermission(
    access_model, role_code, user_id, space=None, post=None, org=None, grant_by=None
):
    query = {"user_id": user_id}
    if space:
        role_type = "space"
        query.update({"space_id": space.id})
    elif post:
        role_type = "post"
        query.update({"post_id": post.id})
    elif org:
        role_type = "organization"
        query.update({"organization_id": org.id})
    if not grant_by:
        grant_by = user_id
    role = getRole(role_code, role_type)
    per_role, created = access_model.objects.get_or_create(
        **query,
        role=role,
        defaults={role_type: space or post or org, "grant_by": grant_by},
    )
    if created:
        print("Permission Created", role_type, user_id, role_code)
    return per_role


def processUpdatePermission(
    access_model,
    role_code,
    user_email,
    space=None,
    post=None,
    org=None,
):
    currentUser = get_current_user()
    role_type = "space"
    name = ""
    query = {"user__email": user_email}
    if space:
        name = space.name
        query.update({"space_id": space.id})
        redis_key = f"user_roles_{user_email}_space_{space.id}"
    elif post:
        name = post.title
        role_type = "post"
        query.update({"post_id": post.id})
        post_rel = post.post_rel
        if post_rel == "seq_post":
            post_rel = "post"
        role_type = "post"
        redis_key = f"user_roles_{user_email}_{post_rel}_{post.post_id}"
    elif org:
        name = org.name
        role_type = "organization"
        query.update({"organization_id": org.id})
        redis_key = f"user_roles_{user_email}_organization_{org.id}"
    role_obj = access_model.objects.filter(**query).first()
    if not role_obj:
        raise APIException206(
            {"message": "This User doesn't have Any Permission Assigned"}
        )
    if role_obj.role.role_code == "owner":
        raise APIException206({"message": "Permission of Owner Can't be Change"})
    role = getRole(role_code, role_type)

    notify_data = {
        "event": "permission_updated",
        "object_type": role_type,
        "user_from": currentUser.id,
        "user_to": role_obj.user.id,
        "event_data": {
            "new_role": role.role_code,
            "previous_role": role_obj.role.role_code,
        },
        "title": "Permission Updated",
        "body": f"Your permission has been updated to {role.role_name} for  the {role_type} {name}.",
    }

    role_obj.role = role
    role_obj.save()
    role_obj.refresh_from_db()
    cache.delete(redis_key)

    createNotification(**notify_data)
    return role_obj


def processDeletePermission(access_model, user_email, space=None, post=None, org=None):
    currentUser = get_current_user()
    query = {"user__email": user_email}
    query2 = {}
    name = ""
    object_id = None
    if space:
        name = space.name
        object_id = space.slug
        redis_key = f"user_roles_{user_email}_space_{space.id}"
        query.update({"space_id": space.id})
        query2.update({"space_id": space.id})
    elif post:
        name = post.title
        object_id = post.slug
        post_rel = post.post_rel
        if post_rel == "seq_post":
            post_rel = "post"
        redis_key = f"user_roles_{user_email}_{post_rel}_{post.post_id}"
        query.update({"post_id": post.id})
        query2.update({"post_id": post.id})
    elif org:
        name = org.name
        object_id = org.domain_handle
        redis_key = f"user_roles_{user_email}_organization_{org.id}"
        query.update({"organization_id": org.id})
        query2.update({"organization_id": org.id})
    role_obj = access_model.objects.filter(**query)
    if not role_obj:
        raise APIException206(
            {"message": "This User doesn't have any permission assigned."}
        )
    role_first = role_obj.first()
    if role_first.role.role_code == "owner":
        raise APIException206({"message": "Permission of owner can't be deleted"})

    notify_data = {
        "event": "permission_deleted",
        "object_type": role_first.role.role_type,
        "object_id": object_id,
        "user_from": currentUser.id,
        "user_to": role_first.user.id,
        "event_data": {
            "previous_role": role_first.role.role_code,
        },
        "title": "Access Removed",
        "body": f"You have been removed from the {role_first.role.role_type} {name}.",
    }
    role_obj.delete()
    cache.delete(redis_key)

    if currentUser.id == role_first.user.id:
        query2.update({"role__role_code__in": ["owner", "editor"]})
        users = list(
            access_model.objects.filter(**query2).values_list("user__id", flat=True)
        )
        for user_id in users:
            if user_id != currentUser.id:
                notify_data["user_to"] = user_id
                notify_data["title"] = "Member Left"
                notify_data["body"] = (
                    f"{currentUser.full_name} left the {role_first.role.role_type} {name}."
                )
                createNotification(**notify_data)
    else:
        createNotification(**notify_data)
    return True


def generateRefObject(role_type, obj):
    if role_type == "seq_post":
        role_type = "post"
    redis_key = f"ref_object_{role_type}_{obj.id}"
    redis_obj = cache.get(redis_key)
    if redis_obj:
        return json.loads(redis_obj)
    role_map_dict = {
        "space": {
            "space": getattr(obj, "id", None),
            "organization": getattr(obj, "space_organization_id", None),
        },
        "post": {
            "post": getattr(obj, "id", None),
            "main_post": getattr(obj, "main_post_id", None),
            "space": getattr(obj, "space_id", None),
            "organization": getattr(
                getattr(obj, "space", None), "space_organization_id", None
            ),
        },
        "main_post": {
            "post": getattr(obj, "id", None),
            "space": getattr(obj, "space_id", None),
            "organization": getattr(
                getattr(obj, "space", None), "space_organization_id", None
            ),
        },
    }
    redis_obj = role_map_dict[role_type]
    cache.set(redis_key, json.dumps(redis_obj), 60 * 60 * 24)
    return redis_obj


def getParentUserRole(user, access_model, model_key, ref_obj_value):
    query = {"user_id": user.id, model_key: ref_obj_value}
    role_obj = access_model.objects.filter(**query).first()
    # print("Role", role_obj)
    if role_obj and role_obj.role:
        return role_obj.role.role_code
    return None


def getUserPermissionOnEntity(user, entity, entity_type):
    redis_key = f"user_roles_{user.id}_{entity_type}_{entity.id}"
    cache_data = cache.get(redis_key + "sdsd")  # FIX KEY
    # if cache_data:
    #     return json.loads(cache_data)
    entities, permissions = get_entity_permissions(entity, entity_type, user)
    print(permissions, entities)

    permission_manager = PermissionManager(entities, permissions)
    permissions = permission_manager.get_permissions(user.id, entity.id)
    print(permissions)
    # cache.set(redis_key, json.dumps(all_roles), 60 * 60 * 24)
    return permissions


def get_entity_permissions(entity, entity_type, user, child_entity=None):
    from unpod.space.models import OrganizationMemberRoles, SpaceMemberRoles
    from unpod.thread.models import ThreadPostPermission

    # print("Entity Type", entity_type, entity)
    permission_models = {
        "post": {"model": ThreadPostPermission, "key": "post_id", "name": "post"},
        "space": {"model": SpaceMemberRoles, "key": "space_id", "name": "space"},
        "organization": {
            "model": OrganizationMemberRoles,
            "key": "organization_id",
            "name": "organization",
        },
    }
    permissions = []
    entities = []
    model = permission_models[entity_type]
    role_obj = get_entity_role(entity, model, user)
    print(role_obj)
    if role_obj and role_obj.role:
        permissions.append(
            UserPermission(
                role_obj.id, user.id, role_obj.role.role_code, entity.id, model["name"]
            ).to_dict()
        )

    # load parent entity permissions
    if entity_type == "post":
        if entity.main_post:
            lst1, lst2 = get_entity_permissions(entity.main_post, "post", user)
            entities.append(
                Entity(
                    entity.id,
                    entity_type,
                    entity.id,
                    entity.privacy_type,
                    "entity",
                    entity.main_post.id,
                ).to_dict(),
            )
        elif entity.space:
            lst1, lst2 = get_entity_permissions(entity.space, "space", user)
            entities.append(
                Entity(
                    entity.id,
                    entity_type,
                    entity.id,
                    entity.privacy_type,
                    "entity",
                    entity.space.id,
                ).to_dict(),
            )
        entities.extend(lst1)
        permissions.extend(lst2)

    if entity_type == "space":
        if entity.space_organization:
            lst1, lst2 = get_entity_permissions(
                entity.space_organization, "organization", user
            )
            entities.append(
                Entity(
                    entity.id,
                    entity_type,
                    entity.id,
                    entity.privacy_type,
                    "entity",
                    entity.space_organization.id,
                ).to_dict(),
            )

            entities.extend(lst1)
            permissions.extend(lst2)

    if entity_type == "organization":
        entities.append(
            Entity(
                entity.id, entity_type, entity.id, entity.privacy_type, "entity", 0
            ).to_dict(),
        )

    return entities, permissions


def get_entity_role(entity, model, user):
    # TODO enable cache
    query = {"user_id": user.id, model["key"]: getattr(entity, "id", 0)}
    print("Query", query, model["key"])
    role_obj = model["model"].objects.filter(**query).first()
    return role_obj


def getUserRolesByChild(user, role_type, ref_dict):
    from unpod.space.models import OrganizationMemberRoles, SpaceMemberRoles
    from unpod.thread.models import ThreadPostPermission

    if role_type == "seq_post":
        role_type = "post"

    redis_key = f"user_roles_{user.email}_{role_type}_{ref_dict['id']}"
    cache_data = cache.get(redis_key)
    if cache_data:
        return json.loads(cache_data)
    models_dict = {
        "space": [
            {"model": SpaceMemberRoles, "key": "space_id", "name": "space"},
            {
                "model": OrganizationMemberRoles,
                "key": "organization_id",
                "name": "organization",
            },
        ],
        "post": [
            {"model": ThreadPostPermission, "key": "post_id", "name": "post"},
            {"model": ThreadPostPermission, "key": "post_id", "name": "main_post"},
            {"model": SpaceMemberRoles, "key": "space_id", "name": "space"},
            {
                "model": OrganizationMemberRoles,
                "key": "organization_id",
                "name": "organization",
            },
        ],
        "main_post": [
            {"model": ThreadPostPermission, "key": "post_id", "name": "post"},
            {"model": SpaceMemberRoles, "key": "space_id", "name": "space"},
            {
                "model": OrganizationMemberRoles,
                "key": "organization_id",
                "name": "organization",
            },
        ],
    }
    all_roles = []
    for model_list in models_dict[role_type]:
        role_code = getParentUserRole(
            user, model_list["model"], model_list["key"], ref_dict[model_list["name"]]
        )
        if role_code:
            all_roles.append({"name": model_list["name"], "code": role_code})
    cache.set(redis_key, json.dumps(all_roles), 60 * 60 * 24)
    return all_roles


def getUserFinalRole(user, role_type, ref_dict):
    if not user.is_authenticated:
        return None
    all_roles = getUserRolesByChild(user, role_type, ref_dict)
    final_role = None
    for role in all_roles:
        current_role_index = ROLE_BASED_INDEX.get(role["code"], 5)
        if ROLE_BASED_INDEX.get(final_role, 8) <= current_role_index:
            final_role = role["code"]
            if current_role_index >= 10:
                break
    return final_role
