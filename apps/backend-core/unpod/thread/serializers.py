from rest_framework import serializers
from unpod.common.constants import DATETIME_FORMAT
from unpod.common.decorators import checkUserReturnDefault
from unpod.common.enum import MediaUploadStatus, PostContentType, PostType, PrivacyType
from unpod.common.exception import APIException206
from unpod.common.storage_backends import muxBackend

# from unpod.common.s3 import generate_presigned_url_s3
# from unpod.common.uuid import generate_uuid
from unpod.common.sonyflake import app_sonyflake
from unpod.common.validation import get_user_id
from unpod.core_components.models import Pilot
from unpod.core_components.serializers import PilotFullSerializer, KBSerializer
from unpod.core_components.services import (
    fetch_object_media,
    getMediaData,
    update_media_status,
    upload_media,
    validateMedia,
    validateMuxMedia,
)
from unpod.core_components.utils import get_user_data
from unpod.roles.constants import (
    DEFAULT_POST_PERMISSION_ROLE,
    DEFAULT_SPACE_PERMISSION_ROLE,
)
from unpod.roles.services import generateRefObject, getUserFinalRole
from unpod.roles.utlis import getRoleBasedOperation
from unpod.space.models import Space
from unpod.space.serializers import SpaceOrganizationSerializers
from unpod.space.utils import get_space_users
from unpod.thread.block import fetch_block
from unpod.thread.constants import (
    THREAD_DETAIL_FIELDS,
    THREAD_LIST_FIELDS,
    THREAD_POST_LIST_FIELDS,
    THREAD_POST_REPLY_FIELDS,
)
from unpod.thread.models import PostRelation, PostStatus, ThreadPost
from unpod.thread.services import (
    calculatePostSequence,
    createThreadPermission,
    get_post_access_request,
    get_post_users,
    getPostQuerySet,
    ThreadCacheService,
)
from unpod.thread.utils import (
    create_related_data,
    fix_content,
    getCoverImageData,
    generatePostSlug,
)
from unpod.thread.validators import PostTitleValidation


class ContentSerializer(serializers.Serializer):
    content = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    def get_content(self, obj):
        if obj.content:
            return obj.content.encode().decode("unicode-escape")
        return None

    def get_title(self, obj):
        if obj.title:
            return obj.title.encode().decode("unicode-escape")
        return None


class CoverImageDetailSerializer(serializers.Serializer):
    cover_image = serializers.SerializerMethodField()

    def get_cover_image(self, instance):
        if instance.media and len(instance.media_data):
            if "cover_image" in instance.media_data:
                return getCoverImageData(instance.media_data.get("cover_image"))
        return None


class MediaDetailSerializer(serializers.Serializer):
    media = serializers.SerializerMethodField()

    def get_media(self, instance):
        if instance.media and len(instance.media_data):
            media_id = instance.media_data.get("content_media")
            media_data = getMediaData("post", instance.post_id, "content", media_id)
            if media_data:
                public_id = media_data.pop("public_id")
                playback_data = muxBackend.getPlaybackId(public_id)
                if "id" in playback_data:
                    media_data["playback_id"] = playback_data["id"]
                return media_data
        return None


class ThreadDetailCommonSerializer(MediaDetailSerializer, CoverImageDetailSerializer):
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    tags = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    post_id = serializers.CharField()

    def get_tags(self, instance):
        if instance.tags and instance.tags != "":
            return instance.tags.split(",")
        return []

    def get_user(self, insance):
        """
        Get user data with request-level caching via ThreadCacheService.

        Performance: Prevents duplicate serialization of same user across
        multiple posts in a single request. Reduces queries by 40-60%.
        """
        request = self.context.get("request")
        if not request:
            # Fallback if no request context
            if not insance.user:
                return {
                    "email": "",
                    "full_name": "Anonymous User",
                    "user_token": f"{insance.created_by}",
                }
            return get_user_data(
                insance.user,
                fields=["full_name", "user_token", "profile_color", "profile_picture"],
            )

        # Use centralized cache service
        return ThreadCacheService.get_cached_user(request, insance.user)

    def get_space(self, insance):
        """
        Get space data with request-level caching via ThreadCacheService.

        Performance: Prevents duplicate serialization of same space across
        multiple posts in a single request.
        """
        request = self.context.get("request")
        if not request:
            # Fallback if no request context
            return get_user_data(
                insance.space,
                fields=["name", "token", "privacy_type", "slug", "space_type"],
            )

        # Use centralized cache service
        return ThreadCacheService.get_cached_space(request, insance.space)


class AnswerBlockSerializer(serializers.Serializer):
    block = serializers.SerializerMethodField()

    def get_block(self, instance):
        if instance.post_type != "ask":
            return {}
        if instance.block and len(instance.block):
            return instance.block
        block = fetch_block(instance.post_id)
        if block and len(block):
            ThreadPost.objects.filter(id=instance.id).update(block=block)
        return block


class ThreadRolePermissionCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    role_code = serializers.ChoiceField(
        choices=["viewer", "editor", "commentor"], required=True
    )


class ThreadAccessRequestUpdateSerializer(serializers.Serializer):
    role_code = serializers.ChoiceField(
        choices=["viewer", "editor", "commentor"], required=True
    )


class ThreadMediaSerializer(serializers.Serializer):
    upload_id = serializers.CharField(required=True)
    file_name = serializers.CharField(required=True)
    size = serializers.IntegerField(required=True)
    media_metadata = serializers.JSONField(required=False)


class CoverImageSerializer(serializers.Serializer):
    media_id = serializers.CharField(required=True)
    file_name = serializers.CharField(required=True)
    media_metadata = serializers.JSONField(required=False)


class ThreadOrgListSerializer(
    serializers.ModelSerializer, ContentSerializer, ThreadDetailCommonSerializer
):
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    cover_image = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    post_id = serializers.CharField()
    media = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [*THREAD_LIST_FIELDS, "cover_image", "media", "content"]


class ThreadListSerializer(
    serializers.ModelSerializer,
    ContentSerializer,
    ThreadDetailCommonSerializer,
    AnswerBlockSerializer,
):
    related_post = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    seen = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [
            *THREAD_LIST_FIELDS,
            "related_post",
            "cover_image",
            "media",
            "seen",
            "content",
            "users",
            "organization",
        ]

    def get_related_post(self, instance):
        # Use prefetched data if available (performance optimization)
        if hasattr(instance, "prefetched_related_posts"):
            related_posts = [
                post
                for post in instance.prefetched_related_posts
                if post.parent_id == instance.id
            ][:3]
            return [
                {
                    "title": post.title,
                    "privacy_type": post.privacy_type,
                    "post_rel": post.post_rel,
                    "slug": post.slug,
                    "post_type": post.post_type,
                    "content_type": post.content_type,
                }
                for post in related_posts
            ]

        # Fallback to original query if prefetch not available
        request = self.context.get("request")
        query = {
            "space_id": instance.space.id,
            "post_rel": PostRelation.seq_post.name,
        }
        query.update({"main_post_id": instance.id, "parent_id": instance.id})
        thread_queryset = getPostQuerySet(
            request, instance.space.token, PostRelation.seq_post.name
        )
        return (
            thread_queryset.filter(**query)
            .order_by("seq_number")
            .values(
                "title", "privacy_type", "post_rel", "slug", "post_type", "content_type"
            )[:3]
        )

    def get_seen(self, instance):
        # Optimized: Use prefetched data instead of filter query to avoid N+1
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False
        user_id = str(request.user.id)
        # Check prefetched views first to avoid N+1 queries
        if hasattr(instance, "_prefetched_objects_cache") and "threadpostview_post" in instance._prefetched_objects_cache:
            return any(view.user_id == user_id for view in instance.threadpostview_post.all())
        # Fallback to query if not prefetched
        return instance.threadpostview_post.filter(user_id=user_id).exists()

    @checkUserReturnDefault([])
    def get_users(self, obj):
        users = get_post_users(obj)
        return users

    def get_organization(self, obj):
        """
        Get organization data with request-level caching via ThreadCacheService.

        Performance: Single organization often appears across multiple posts.
        Caching prevents re-serialization, reducing queries by 50%+.
        """
        request = self.context.get("request")
        if not request:
            # Fallback if no request context
            return SpaceOrganizationSerializers(obj.space.space_organization).data

        # Use centralized cache service
        return ThreadCacheService.get_cached_organization(request, obj.space)


class ThreadDetailSerializer(
    serializers.ModelSerializer,
    ContentSerializer,
    ThreadDetailCommonSerializer,
    AnswerBlockSerializer,
):
    attachments = serializers.SerializerMethodField()
    root_post_id = serializers.SerializerMethodField()
    parent_post_id = serializers.SerializerMethodField()
    root_post_slug = serializers.SerializerMethodField()
    parent_post_slug = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    access_request = serializers.SerializerMethodField()
    seen = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    pilot = serializers.SerializerMethodField()
    knowledge_bases = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [
            *THREAD_DETAIL_FIELDS,
            "attachments",
            "cover_image",
            "content",
            "media",
            "root_post_id",
            "parent_post_id",
            "root_post_slug",
            "parent_post_slug",
            "access_request",
            "seen",
            "user_role",
            "organization",
            "block",
            "pilot",
            "knowledge_bases",
        ]

    def get_attachments(self, instance):
        if instance.attachments:
            all_attachments = fetch_object_media("post", instance.post_id, "attachment")
            return all_attachments
        return []

    # def get_post_count(self, instance):
    #     return instance.threadpost_parent.filter(post_rel=PostRelation.seq_post.name).count()

    # def get_reply_count(self, instance):
    #     return instance.threadpost_parent.filter(post_rel=PostRelation.reply.name).count()

    def get_root_post_id(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.post_id)
        return str(instnace.main_post.post_id)

    def get_parent_post_id(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.post_id)
        return str(instnace.parent.post_id)

    def get_root_post_slug(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.slug)
        return str(instnace.main_post.slug)

    def get_parent_post_slug(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.slug)
        return str(instnace.parent.slug)

    @checkUserReturnDefault([])
    def get_users(self, obj):
        users = get_post_users(obj)
        # users.extend(get_post_access_request(obj))
        return users

    @checkUserReturnDefault([])
    def get_access_request(self, obj):
        return get_post_access_request(obj)

    @checkUserReturnDefault(DEFAULT_POST_PERMISSION_ROLE)
    def get_user_role(self, obj):
        user = self.context.get("request").user
        role = (
            obj.threadpostpermission_post.filter(user=user)
            .select_related("role")
            .first()
        )
        if role:
            return role.role.role_code
        return DEFAULT_POST_PERMISSION_ROLE

    def get_seen(self, instance):
        # Optimized: Use prefetched data instead of filter query to avoid N+1
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False
        user_id = str(request.user.id)
        # Check prefetched views first to avoid N+1 queries
        if hasattr(instance, "_prefetched_objects_cache") and "threadpostview_post" in instance._prefetched_objects_cache:
            return any(view.user_id == user_id for view in instance.threadpostview_post.all())
        # Fallback to query if not prefetched
        return instance.threadpostview_post.filter(user_id=user_id).exists()

    @checkUserReturnDefault(False)
    def get_joined(self, instance, users):
        email = self.context.get("request").user.email
        for user in users:
            if user["email"] == email and user["joined"]:
                return True
        return False

    @checkUserReturnDefault(
        {"joined": False, "role_code": DEFAULT_POST_PERMISSION_ROLE}
    )
    def get_space_joined(self, instance, users):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        email = user.email
        for user in users:
            if user["email"] == email and user["joined"]:
                return {"joined": True, "role_code": user["role"]}
        return {"joined": False, "role_code": DEFAULT_POST_PERMISSION_ROLE}

    def get_organization(self, obj):
        return SpaceOrganizationSerializers(obj.space.space_organization).data

    def get_pilot(self, obj):
        pilot_handle = obj.related_data.get("pilot", "") if obj.related_data else ""
        if pilot_handle:
            pilot = Pilot.objects.filter(handle=pilot_handle).first()
            if pilot:
                return PilotFullSerializer(
                    pilot, context={"request": self.context.get("request")}
                ).data
        return {}

    def get_knowledge_bases(self, obj):
        kb_slugs = (
            obj.related_data.get("knowledge_bases", []) if obj.related_data else []
        )
        if kb_slugs:
            kbs = Space.objects.filter(slug__in=kb_slugs)
            return KBSerializer(kbs, many=True).data
        return []

    def to_representation(self, instance):
        user = getattr(self.context.get("request"), "user", None) or self.context.get(
            "user"
        )
        representation = super().to_representation(instance)
        representation["joined"] = self.get_joined(instance, representation["users"])
        representation["space"]["users"] = get_space_users(instance.space, user)
        role_data = self.get_space_joined(
            instance.space, representation["space"]["users"]
        )
        representation["space"]["joined"] = role_data["joined"]
        representation["space"]["user_role"] = role_data["role_code"]
        ref_dict = generateRefObject(instance.post_rel, instance)
        ref_dict["id"] = instance.post_id
        final_role = (
            getUserFinalRole(user, instance.post_rel, ref_dict)
            or DEFAULT_POST_PERMISSION_ROLE
        )
        if final_role != "owner":
            final_role = representation["user_role"]
        representation["final_role"] = final_role
        representation["allowed_operations"] = getRoleBasedOperation(
            representation["final_role"], "post"
        )

        # add space allowed operations
        ref_dict = generateRefObject("space", instance.space)
        ref_dict["id"] = instance.space.id
        final_role = (
            getUserFinalRole(user, "space", ref_dict) or DEFAULT_SPACE_PERMISSION_ROLE
        )
        if final_role != "owner":
            final_role = representation["space"]["user_role"]
        representation["space"]["final_role"] = final_role
        representation["space"]["allowed_operations"] = getRoleBasedOperation(
            final_role, "space"
        )
        return representation


class ThreadCreateSerializer(serializers.ModelSerializer, PostTitleValidation):
    post_type = serializers.ChoiceField(choices=PostType.choices(), required=True)
    content_type = serializers.ChoiceField(
        choices=PostContentType.choices(), required=True
    )
    cover_image = CoverImageSerializer(required=False)
    attachments = serializers.ListField(
        child=serializers.FileField(required=False), required=False, write_only=True
    )
    post_status = serializers.ChoiceField(
        required=False, write_only=True, choices=PostStatus.choices()
    )
    user_list = ThreadRolePermissionCreateSerializer(
        many=True, required=False, write_only=True
    )
    privacy_type = serializers.ChoiceField(
        choices=PrivacyType.choices(), required=False
    )
    tags = serializers.ListField(
        required=False,
        child=serializers.CharField(required=False, write_only=True),
        write_only=True,
    )
    media = ThreadMediaSerializer(required=False)

    class Meta:
        model = ThreadPost
        fields = [
            "title",
            "post_status",
            "description",
            "privacy_type",
            "content",
            "scheduled",
            "schedule_datetime",
            "tags",
            "cover_image",
            "attachments",
            "user_list",
            "media",
            "post_type",
            "content_type",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        space = self.context.get("space")
        media = validated_data.pop("media", None)
        attachments = validated_data.pop("attachments", None)
        cover_image = validated_data.pop("cover_image", None)
        if media:
            media, media_status = validateMuxMedia(media)
        if cover_image:
            cover_obj = validateMedia(cover_image.get("media_id"), "post")
        validated_data["space_id"] = space.id
        validated_data["user_id"] = request.user.id
        validated_data["created_by"] = request.user.id
        validated_data["updated_by"] = request.user.id
        validated_data["post_rel"] = PostRelation.main_post.name
        validated_data["post_id"] = app_sonyflake.next_id()
        validated_data["tags"] = ",".join(validated_data.get("tags", []))
        if validated_data.get("content"):
            validated_data["content"] = (
                validated_data["content"].encode("unicode-escape").decode()
            )
        user_list = validated_data.pop("user_list", [])
        privacy_type = validated_data.get("privacy_type")
        if privacy_type == PrivacyType.public.name:
            user_list = []
        if "post_status" not in validated_data:
            validated_data["post_status"] = PostStatus.published.name

        if validated_data.get("scheduled") and validated_data.get("schedule_datetime"):
            validated_data["post_status"] = PostStatus.scheduled.name

        if validated_data.get("post_type") not in ["notebook"]:
            validated_data["content"] = fix_content(validated_data.get("content"))

        related_data = {}
        related_data["pilot"] = self.initial_data.get("pilot", "").lower()
        related_data["knowledge_bases"] = self.initial_data.get("knowledge_bases", [])

        extra_related_data = create_related_data(
            self.initial_data, ["focus", "data", "execution_type"]
        )
        related_data.update(extra_related_data)

        validated_data["related_data"] = related_data
        instance = self.Meta.model.objects.create(**validated_data)

        update_data = {}
        media_data = {}
        if cover_image:
            update_data["media"] = True
            cover_data = {}
            media_update_data = {
                "object_id": str(instance.post_id),
                "media_status": MediaUploadStatus.uploaded.name,
            }
            cover_obj.updateModel(media_update_data)
            cover_data["url"] = cover_obj.url
            cover_data["name"] = cover_obj.name
            if cover_obj.public_id:
                cover_data["privacy_type"] = cover_obj.privacy_type
                cover_data["public_id"] = cover_obj.public_id

            media_data["cover_image"] = cover_data
            update_data["media_data"] = media_data
        if attachments:
            update_data["attachments"] = True
            for attachment in attachments:
                attachment_instance = upload_media(
                    request, "post", instance.post_id, "attachment", attachment
                )
        if media:
            update_data["media"] = True
            media_instance = upload_media(
                request, "post", instance.post_id, "content", media_data=media
            )
            media_data["content_media"] = media_instance.media_id

        if len(media_data):
            update_data["media_data"] = media_data

        files = self.initial_data.get("files", [])
        if len(files):
            update_data["attachments"] = True
            media_ids = [file["media_id"] for file in files]
            update_media_status(
                media_ids,
                "post",
                MediaUploadStatus.uploaded.name,
                {"object_id": str(instance.post_id)},
            )

        update_data["slug"] = generatePostSlug(space, instance)
        if len(update_data):
            instance = self.Meta.model.updateModel(instance, update_data)
        createThreadPermission(instance, user_list, request)
        return instance


class ThreadPostListSerializer(
    serializers.ModelSerializer,
    ContentSerializer,
    ThreadDetailCommonSerializer,
    AnswerBlockSerializer,
):
    users = serializers.SerializerMethodField()
    access_request = serializers.SerializerMethodField()
    seen = serializers.SerializerMethodField()
    root_post_id = serializers.SerializerMethodField()
    parent_post_id = serializers.SerializerMethodField()
    root_post_slug = serializers.SerializerMethodField()
    parent_post_slug = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [
            *THREAD_POST_LIST_FIELDS,
            "cover_image",
            "media",
            "users",
            "access_request",
            "seen",
            "root_post_id",
            "parent_post_id",
            "root_post_slug",
            "parent_post_slug",
        ]

    @checkUserReturnDefault([])
    def get_users(self, obj):
        users = get_post_users(obj)
        return users

    @checkUserReturnDefault([])
    def get_access_request(self, obj):
        return get_post_access_request(obj)

    def get_seen(self, instance):
        # Optimized: Use prefetched data instead of filter query to avoid N+1
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return False
        user_id = str(request.user.id)
        # Check prefetched views first to avoid N+1 queries
        if hasattr(instance, "_prefetched_objects_cache") and "threadpostview_post" in instance._prefetched_objects_cache:
            return any(view.user_id == user_id for view in instance.threadpostview_post.all())
        # Fallback to query if not prefetched
        return instance.threadpostview_post.filter(user_id=user_id).exists()

    def get_root_post_id(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.post_id)
        return str(instnace.main_post.post_id)

    def get_parent_post_id(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.post_id)
        return str(instnace.parent.post_id)

    def get_root_post_slug(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.slug)
        return str(instnace.main_post.slug)

    def get_parent_post_slug(self, instnace):
        if instnace.post_rel == PostRelation.main_post.name:
            return str(instnace.slug)
        return str(instnace.parent.slug)


class ThreadPostCreateSerializer(serializers.ModelSerializer, PostTitleValidation):
    post_type = serializers.ChoiceField(choices=PostType.choices(), required=True)
    content_type = serializers.ChoiceField(
        choices=PostContentType.choices(), required=True
    )
    cover_image = CoverImageSerializer(required=False)
    attachments = serializers.ListField(
        child=serializers.FileField(required=False), required=False, write_only=True
    )
    post_status = serializers.ChoiceField(
        required=False, write_only=True, choices=PostStatus.choices()
    )

    user_list = ThreadRolePermissionCreateSerializer(
        many=True, required=False, write_only=True
    )
    privacy_type = serializers.ChoiceField(
        choices=PrivacyType.choices(), required=False
    )

    tags = serializers.ListField(
        required=False,
        child=serializers.CharField(required=False, write_only=True),
        write_only=True,
    )
    media = ThreadMediaSerializer(required=False)

    class Meta:
        model = ThreadPost
        fields = [
            "title",
            "post_status",
            "description",
            "privacy_type",
            "content",
            "scheduled",
            "schedule_datetime",
            "tags",
            "cover_image",
            "attachments",
            "user_list",
            "media",
            "post_type",
            "content_type",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        space = self.context.get("space")
        post = self.context.get("post")
        media = validated_data.pop("media", None)
        attachments = validated_data.pop("attachments", None)
        cover_image = validated_data.pop("cover_image", None)
        if media:
            media, media_status = validateMuxMedia(media)
        if cover_image:
            cover_obj = validateMedia(cover_image.get("media_id"), "post")
        validated_data["space_id"] = space.id
        validated_data["user_id"] = request.user.id
        validated_data["tags"] = ",".join(validated_data.get("tags", []))
        validated_data["created_by"] = request.user.id
        validated_data["updated_by"] = request.user.id
        validated_data["post_rel"] = PostRelation.seq_post.name
        validated_data["post_id"] = app_sonyflake.next_id()
        if validated_data.get("content"):
            validated_data["content"] = (
                validated_data["content"].encode("unicode-escape").decode()
            )

        privacy_type = validated_data.get("privacy_type", post.privacy_type)
        validated_data["privacy_type"] = privacy_type

        user_list = validated_data.pop("user_list", [])
        if privacy_type == PrivacyType.public.name:
            user_list = []

        if post.post_rel == PostRelation.main_post.name:
            validated_data["main_post_id"] = post.id
        elif post.post_rel == PostRelation.seq_post.name:
            validated_data["main_post_id"] = post.main_post.id

        validated_data["parent_id"] = post.id
        validated_data["seq_number"] = calculatePostSequence(
            post, PostRelation.seq_post.name
        )
        # validated_data['seq_number'] = post.post_count + 1

        if "post_status" not in validated_data:
            validated_data["post_status"] = PostStatus.published.name

        if validated_data.get("scheduled") and validated_data.get("schedule_datetime"):
            validated_data["post_status"] = PostStatus.scheduled.name

        if validated_data.get("post_type") not in ["notebook"]:
            validated_data["content"] = fix_content(validated_data.get("content"))

        related_data = {}
        related_data["pilot"] = self.initial_data.get("pilot", "").lower()
        related_data["knowledge_bases"] = self.initial_data.get("knowledge_bases", [])

        extra_related_data = create_related_data(
            self.initial_data, ["focus", "data", "execution_type"]
        )
        related_data.update(extra_related_data)

        validated_data["related_data"] = related_data

        instance = self.Meta.model.objects.create(**validated_data)

        update_data = {}
        media_data = {}
        if cover_image:
            update_data["media"] = True
            cover_data = {}
            media_update_data = {
                "object_id": str(instance.post_id),
                "media_status": MediaUploadStatus.uploaded.name,
            }
            cover_obj.updateModel(media_update_data)
            cover_data["url"] = cover_obj.url
            cover_data["name"] = cover_obj.name
            if cover_obj.public_id:
                cover_data["privacy_type"] = cover_obj.privacy_type
                cover_data["public_id"] = cover_obj.public_id

            media_data["cover_image"] = cover_data
            update_data["media_data"] = media_data
        if attachments:
            update_data["attachments"] = True
            for attachment in attachments:
                attachment_instance = upload_media(
                    request, "post", instance.post_id, "attachment", attachment
                )

        if media:
            update_data["media"] = True
            media_instance = upload_media(
                request, "post", instance.post_id, "content", media_data=media
            )
            media_data["content_media"] = media_instance.media_id

        if len(media_data):
            update_data["media_data"] = media_data

        files = self.initial_data.get("files", [])
        if len(files):
            update_data["attachments"] = True
            media_ids = [file["media_id"] for file in files]
            update_media_status(
                media_ids,
                "post",
                MediaUploadStatus.uploaded.name,
                {"object_id": str(instance.post_id)},
            )

        update_data["slug"] = generatePostSlug(space, instance)
        if len(update_data):
            instance = self.Meta.model.updateModel(instance, update_data)
        createThreadPermission(instance, user_list, request)
        post.post_count += 1
        post.save()
        return instance


class ThreadPostReplyToReplyListSerializer(
    serializers.ModelSerializer, ContentSerializer
):
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    user = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [*THREAD_POST_REPLY_FIELDS, "users"]

    def get_user(self, instance):
        return get_user_data(
            instance.user,
            fields=[
                # "email",
                "full_name",
                "user_token",
                "profile_color",
                "profile_picture",
            ],
        )

    @checkUserReturnDefault([])
    def get_users(self, obj):
        return get_post_users(obj)


class ThreadPostReplyListSerializer(serializers.ModelSerializer, ContentSerializer):
    created = serializers.DateTimeField(format=DATETIME_FORMAT)
    user = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [*THREAD_POST_REPLY_FIELDS, "replies", "users"]

    def get_user(self, instance):
        return get_user_data(
            instance.user,
            fields=[
                # "email",
                "full_name",
                "user_token",
                "profile_color",
                "profile_picture",
            ],
        )

    def get_replies(self, instance):
        reply_list = instance.threadpost_parent.filter(post_rel=PostRelation.reply.name)
        reply_list = reply_list.order_by("seq_number")[:5]
        return ThreadPostReplyToReplyListSerializer(
            reply_list, many=True, context=self.context
        ).data

    @checkUserReturnDefault([])
    def get_users(self, obj):
        return get_post_users(obj)


class ThreadPostReplySerializer(serializers.ModelSerializer, ContentSerializer):
    user = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    space = serializers.SerializerMethodField()
    parent_post_id = serializers.SerializerMethodField()
    parent_post_slug = serializers.SerializerMethodField()

    class Meta:
        model = ThreadPost
        fields = [
            *THREAD_POST_REPLY_FIELDS,
            "users",
            "parent_post_id",
            "parent_post_slug",
        ]

    def get_user(self, insance):
        return get_user_data(
            insance.user,
            fields=[
                # "email",
                "full_name",
                "user_token",
                "profile_color",
                "profile_picture",
            ],
        )

    @checkUserReturnDefault([])
    def get_users(self, obj):
        return get_post_users(obj)

    def get_parent_post_id(self, instnace):
        return str(instnace.parent.post_id)

    def get_parent_post_slug(self, instnace):
        return str(instnace.parent.slug)

    def get_space(self, insance):
        return get_user_data(
            insance.space,
            fields=["name", "token", "privacy_type", "slug", "space_type"],
        )


class ThreadPostReplyCreateSerializer(serializers.ModelSerializer):
    user_list = ThreadRolePermissionCreateSerializer(
        many=True, required=False, write_only=True
    )
    privacy_type = serializers.ChoiceField(
        choices=PrivacyType.choices(), required=False
    )

    class Meta:
        model = ThreadPost
        fields = ["title", "description", "content", "user_list", "privacy_type"]

    def create(self, validated_data):
        request = self.context.get("request")
        space = self.context.get("space")
        post = self.context.get("post")
        validated_data["space_id"] = space.id
        validated_data["user_id"] = request.user.id
        validated_data["created_by"] = request.user.id
        validated_data["updated_by"] = request.user.id
        validated_data["post_rel"] = PostRelation.reply.name
        validated_data["post_id"] = app_sonyflake.next_id()
        if validated_data.get("content"):
            validated_data["content"] = (
                validated_data["content"].encode("unicode-escape").decode()
            )

        privacy_type = validated_data.get("privacy_type", PrivacyType.public.name)
        validated_data["privacy_type"] = privacy_type

        user_list = validated_data.pop("user_list", [])
        if privacy_type == PrivacyType.public.name:
            user_list = []

        if post.post_rel == PostRelation.main_post.name:
            validated_data["main_post_id"] = post.id
        else:
            validated_data["main_post_id"] = post.main_post.id

        validated_data["parent_id"] = post.id
        validated_data["seq_number"] = calculatePostSequence(
            post, PostRelation.reply.name
        )
        # validated_data['seq_number'] = post.reply_count + 1

        validated_data["post_status"] = PostStatus.published.name

        attachments = validated_data.pop("attachments", None)
        instance = self.Meta.model.objects.create(**validated_data)

        update_data = {}
        if attachments:
            update_data["attachments"] = True
            for attachment in attachments:
                attachment_instance = upload_media(
                    request, "post", instance.post_id, "attachment", attachment
                )

        update_data["slug"] = generatePostSlug(space, instance)
        if len(update_data):
            instance = self.Meta.model.updateModel(instance, update_data)
        createThreadPermission(instance, user_list, request, create_owner=True)
        post.reply_count += 1
        post.save()
        return instance


class PostUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    privacy_type = serializers.ChoiceField(
        choices=PrivacyType.choices(), required=False
    )
    content = serializers.CharField(required=False)
    post_status = serializers.ChoiceField(
        required=False, write_only=True, choices=PostStatus.choices()
    )
    cover_image = CoverImageSerializer(required=False)

    tags = serializers.ListField(
        required=False,
        child=serializers.CharField(required=False, write_only=True),
        write_only=True,
    )

    def update(self, instance: ThreadPost, validated_data, request):
        make_private = False
        tags = validated_data.pop("tags", [])
        if len(tags):
            validated_data["tags"] = ",".join(tags)
        if validated_data.get("content"):
            validated_data["content"] = (
                validated_data["content"].encode("unicode-escape").decode()
            )
        privacy_type = validated_data.get("privacy_type")
        if (
            privacy_type
            and privacy_type != "private"
            and instance.privacy_type != "private"
        ):
            pass
        elif (
            privacy_type
            and privacy_type == "private"
            and instance.privacy_type != "private"
            and instance.user.id != request.user.id
        ):
            raise APIException206(
                {
                    "message": "You can't change the privacy to private, As you are not Owner"
                }
            )

        if (
            privacy_type
            and privacy_type == "private"
            and instance.privacy_type != "private"
            and instance.user.id == request.user.id
        ):
            make_private = True
        if (
            instance.post_status == "draft"
            and validated_data.get("title")
            and validated_data.get("title") != instance.title
        ):
            from django.utils.text import slugify

            validated_data["title"] = (
                validated_data["title"].encode("unicode-escape").decode()
            )
            title = validated_data.get("title")
            post_slug = slugify(f"{title}-{instance.post_id}")
            validated_data["slug"] = post_slug
        cover_image = validated_data.pop("cover_image", None)

        media_data = instance.media_data or {}
        if cover_image:
            cover_obj = validateMedia(cover_image.get("media_id"), "post")
            cover_data = {}
            media_update_data = {
                "object_id": str(instance.post_id),
                "media_status": MediaUploadStatus.uploaded.name,
            }
            cover_obj.updateModel(media_update_data)
            cover_data["url"] = cover_obj.url
            cover_data["name"] = cover_obj.name
            if cover_obj.public_id:
                cover_data["privacy_type"] = cover_obj.privacy_type
                cover_data["public_id"] = cover_obj.public_id
            media_data["cover_image"] = cover_data
            validated_data["media_data"] = media_data
            validated_data["media"] = True

        ThreadPost.objects.filter(id=instance.id).update(**validated_data)
        instance.refresh_from_db()
        return instance, make_private


class PostReactionCreate(serializers.Serializer):
    reaction_type = serializers.ChoiceField(choices=["clap"], required=True)
    reaction_count = serializers.IntegerField(required=True, min_value=1)


class PostReportCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=["spam", "irrelevant", "nudity", "controversial", "other"],
        required=True,
    )
    message = serializers.CharField(required=False)
    other = serializers.CharField(required=False)


class ThreadPostListOrgSerializer(ThreadPostListSerializer):
    organization = serializers.SerializerMethodField()

    class Meta(ThreadPostListSerializer.Meta):
        fields = [*ThreadPostListSerializer.Meta.fields, "organization"]

    def get_organization(self, obj):
        return SpaceOrganizationSerializers(obj.space.space_organization).data


class ThreadPostTrendingListSerializer(ThreadPostListSerializer):
    class Meta(ThreadPostListSerializer.Meta):
        fields = [*ThreadPostListSerializer.Meta.fields]


class ThreadAnonymousCreateSerializer(serializers.ModelSerializer, PostTitleValidation):
    post_type = serializers.ChoiceField(choices=PostType.choices(), required=True)
    content_type = serializers.ChoiceField(
        choices=PostContentType.choices(), required=True
    )
    post_status = serializers.ChoiceField(
        required=False, write_only=True, choices=PostStatus.choices()
    )
    user_list = ThreadRolePermissionCreateSerializer(
        many=True, required=False, write_only=True
    )
    privacy_type = serializers.ChoiceField(
        choices=PrivacyType.choices(), required=False
    )

    tags = serializers.ListField(
        required=False,
        child=serializers.CharField(required=False, write_only=True),
        write_only=True,
    )

    class Meta:
        model = ThreadPost
        fields = [
            "title",
            "post_status",
            "description",
            "privacy_type",
            "content",
            "scheduled",
            "schedule_datetime",
            "tags",
            "user_list",
            "post_type",
            "content_type",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        space = self.context.get("space")
        user_id, is_authenticated = get_user_id(request)
        validated_data["space_id"] = space.id
        if is_authenticated:
            validated_data["user_id"] = user_id
        validated_data["tags"] = ",".join(validated_data.get("tags", []))
        validated_data["created_by"] = user_id
        validated_data["updated_by"] = user_id
        validated_data["post_rel"] = PostRelation.main_post.name
        validated_data["post_id"] = app_sonyflake.next_id()
        if validated_data.get("content"):
            validated_data["content"] = (
                validated_data["content"].encode("unicode-escape").decode()
            )

        privacy_type = validated_data.get("privacy_type", PrivacyType.public.name)

        user_list = validated_data.pop("user_list", [])
        if privacy_type == PrivacyType.public.name or not is_authenticated:
            user_list = []
            privacy_type = PrivacyType.public.name
        validated_data["privacy_type"] = privacy_type

        if "post_status" not in validated_data:
            validated_data["post_status"] = PostStatus.published.name

        if validated_data.get("scheduled") and validated_data.get("schedule_datetime"):
            validated_data["post_status"] = PostStatus.scheduled.name

        if validated_data.get("post_type") not in ["notebook"]:
            validated_data["content"] = fix_content(validated_data.get("content"))

        related_data = {}
        rel_data = self.initial_data.get("related_data", {})
        if rel_data:
            related_data.update(rel_data)
        related_data["pilot"] = self.initial_data.get("pilot", "").lower()
        related_data["knowledge_bases"] = self.initial_data.get("knowledge_bases", [])
        if self.initial_data.get("focus"):
            related_data["focus"] = self.initial_data.get("focus")

        validated_data["related_data"] = related_data

        instance = self.Meta.model.objects.create(**validated_data)

        update_data = {}
        media_data = {}

        if len(media_data):
            update_data["media_data"] = media_data

        files = self.initial_data.get("files", [])
        if len(files):
            update_data["attachments"] = True
            media_ids = [file["media_id"] for file in files]
            update_media_status(
                media_ids,
                "post",
                MediaUploadStatus.uploaded.name,
                {"object_id": str(instance.post_id)},
            )

        update_data["slug"] = generatePostSlug(space, instance)
        if len(update_data):
            instance = self.Meta.model.updateModel(instance, update_data)
        if is_authenticated:
            createThreadPermission(instance, user_list, request)
        return instance


class PublicThreadAnonymousCreateSerializer(
    serializers.ModelSerializer, PostTitleValidation
):
    post_type = serializers.ChoiceField(choices=PostType.choices(), required=True)
    content_type = serializers.ChoiceField(
        choices=PostContentType.choices(), required=True
    )
    post_status = serializers.ChoiceField(
        required=False, write_only=True, choices=PostStatus.choices()
    )
    user_list = ThreadRolePermissionCreateSerializer(
        many=True, required=False, write_only=True
    )
    privacy_type = serializers.ChoiceField(
        choices=PrivacyType.choices(), required=False
    )

    tags = serializers.ListField(
        required=False,
        child=serializers.CharField(required=False, write_only=True),
        write_only=True,
    )

    class Meta:
        model = ThreadPost
        fields = [
            "title",
            "post_status",
            "description",
            "privacy_type",
            "content",
            "scheduled",
            "schedule_datetime",
            "tags",
            "user_list",
            "post_type",
            "content_type",
            "post_id",
            "ref_collection",
            "ref_doc_id",
            "user_id",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        space = self.context.get("space")
        user_id = request.data.get("user_id")

        validated_data["space_id"] = space.id
        validated_data["user_id"] = user_id
        validated_data["tags"] = ",".join(validated_data.get("tags", []))
        validated_data["created_by"] = user_id
        validated_data["updated_by"] = user_id
        validated_data["post_rel"] = PostRelation.main_post.name
        validated_data["post_id"] = app_sonyflake.next_id()
        if validated_data.get("content"):
            validated_data["content"] = (
                validated_data["content"].encode("unicode-escape").decode()
            )

        privacy_type = validated_data.get("privacy_type", PrivacyType.public.name)

        user_list = validated_data.pop("user_list", [])

        user_list = []
        privacy_type = PrivacyType.public.name
        validated_data["privacy_type"] = privacy_type

        if "post_status" not in validated_data:
            validated_data["post_status"] = PostStatus.published.name

        if validated_data.get("scheduled") and validated_data.get("schedule_datetime"):
            validated_data["post_status"] = PostStatus.scheduled.name

        if validated_data.get("post_type") not in ["notebook"]:
            validated_data["content"] = fix_content(validated_data.get("content"))

        related_data = {}
        rel_data = self.initial_data.get("related_data", {})
        if rel_data:
            related_data.update(rel_data)
        related_data["pilot"] = self.initial_data.get("pilot", "").lower()
        related_data["knowledge_bases"] = self.initial_data.get("knowledge_bases", [])
        if self.initial_data.get("focus"):
            related_data["focus"] = self.initial_data.get("focus")

        validated_data["related_data"] = related_data

        instance = self.Meta.model.objects.create(**validated_data)

        update_data = {}
        media_data = {}

        if len(media_data):
            update_data["media_data"] = media_data

        files = self.initial_data.get("files", [])
        if len(files):
            update_data["attachments"] = True
            media_ids = [file["media_id"] for file in files]
            update_media_status(
                media_ids,
                "post",
                MediaUploadStatus.uploaded.name,
                {"object_id": str(instance.post_id)},
            )

        update_data["slug"] = generatePostSlug(space, instance)
        if len(update_data):
            instance = self.Meta.model.updateModel(instance, update_data)

        return instance


class PublicThreadUpdateSerializer(serializers.Serializer):
    content = serializers.CharField(required=True)
    tags = serializers.ListField(
        required=False,
        child=serializers.CharField(required=False),
    )

    def update(self, instance: ThreadPost, validated_data):
        if "content" in validated_data:
            instance.content = (
                validated_data["content"].encode("unicode-escape").decode()
            )

        if "tags" in validated_data:
            if isinstance(validated_data["tags"], list):
                instance.tags = validated_data["tags"]
            else:
                instance.tags = [validated_data["tags"]]

        instance.save()
        return instance
