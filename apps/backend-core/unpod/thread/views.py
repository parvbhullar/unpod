import time
import urllib.parse

import requests

from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    AllowAny,
)
from unpod.common.authentication import StaticAPITokenAuthentication
from rest_framework.response import Response
from django.db.models import F, Q, Prefetch
# from django.db.models.functions import Coalesce
from django.utils import timezone
from unpod.common.agora.services import AgoraUtil
from unpod.common.Hms.services import HMS

from unpod.common.exception import APIException206
from unpod.common.mixin import QueryOptimizationMixin, CacheInvalidationMixin
from unpod.common.pagination import UnpodCustomPagination, getPaginator
from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.enum import PostStatus, PrivacyType, PostRepeatType

from unpod.common.serializer import CommonSerializer
from unpod.common.sitemap_generator.schema import generate_post_schema
from unpod.common.throttling import UnpodRateThrottler
from unpod.core_components.services import create_event_trigger
from unpod.core_components.utils import get_user_data
from unpod.roles.constants import DEFAULT_POST_PERMISSION_ROLE
from unpod.roles.services import (
    getRole,
    processDeletePermission,
    processUpdatePermission,
    # getUserPermissionOnEntity
)
from unpod.space.constants import SPACE_ALL_TOKEN
from unpod.space.services import get_anonymous_space
from unpod.space.utils import (
    checkOrgAccess,
    checkPostSpaceAccess,
    checkSpaceOrg,
    get_space_by_query,
)
from unpod.thread.constants import (
    THREAD_LIST_FIELDS,
    THREAD_POST_LIST_FIELDS,
    THREAD_POST_REPLY_FIELDS,
)
from unpod.thread.models import (
    PostBlockList,
    PostCommunicationActivity,
    PostInvite,
    PostRelation,
    PostReport,
    PostSessionRecording,
    ThreadPost,
    ThreadPostAccessRequest,
    ThreadPostPermission,
    ThreadPostReaction,
    ThreadPostView,
    PostCreationCronModel,
)
from unpod.thread.serializers import (
    PostReactionCreate,
    PostReportCreateSerializer,
    PostUpdateSerializer,
    ThreadAccessRequestUpdateSerializer,
    ThreadAnonymousCreateSerializer,
    ThreadCreateSerializer,
    ThreadDetailSerializer,
    ThreadListSerializer,
    ThreadPostCreateSerializer,
    ThreadPostListOrgSerializer,
    ThreadPostListSerializer,
    ThreadPostReplyCreateSerializer,
    ThreadPostReplyListSerializer,
    ThreadPostReplySerializer,
    ThreadRolePermissionCreateSerializer,
    PublicThreadAnonymousCreateSerializer,
    PublicThreadUpdateSerializer,
)
from unpod.thread.services import (
    checkPostOperationAccess,
    checkThreadPostAccess,
    checkThreadPostSlug,
    createThreadPermission,
    getBlockedPost,
    getOrgBasedThread,
    getPostQuerySet,
    getPreviousQuerySet,
    makePostPrivateForPost,
    processSessionRecording,
    get_all_post_query,
    ThreadQueryService,
)
from unpod.thread.utils import addTaskToAgent, extractPostId


class ThreadViewSet(CacheInvalidationMixin, QueryOptimizationMixin, viewsets.GenericViewSet):
    """
    Phase 2.2: Refactored to use QueryOptimizationMixin for query optimization.
    Phase 3.2: Added CacheInvalidationMixin for automatic cache invalidation.
    """
    serializer_class = [CommonSerializer]
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]

    # Phase 3.2: Cache invalidation patterns for thread list caches
    cache_key_patterns = [
        'thread_list:*',  # Invalidate all thread list caches when threads change
    ]

    def get_permissions(self):
        if self.action == "delete":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]

    def list(self, request, *args, **kwargs):
        token = kwargs.get("token")

        # Generate cache key for this request
        page = request.GET.get("page", "1")
        page_size = request.GET.get("page_size", "20")
        post_type = request.GET.get("post_type", "")
        layout = request.GET.get("layout", "")
        search = request.GET.get("search", "")
        user_id = str(request.user.id) if request.user and request.user.is_authenticated else "anon"

        cache_key = (
            f"thread_list:{token}:{page}:{page_size}:{post_type}:{layout}:{search}:{user_id}"
        )

        # Try to get cached response
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response, status=200)

        if token == SPACE_ALL_TOKEN:
            data = getOrgBasedThread(request, token)
            response_data = {"data": data, "message": "Post List Fetch Successfully"}
            # Cache for 60 seconds
            cache.set(cache_key, response_data, 60)
            return Response(response_data, status=200)
        try:
            if layout == "sidebar":
                post_rel = PostRelation.main_post.name
            else:
                post_rel = [PostRelation.main_post.name, PostRelation.seq_post.name]
            thread_queryset = getPostQuerySet(request, token, post_rel)
        except APIException206 as ex:
            if str(ex.detail.get("message")) == "You Don't have Access to this Space":
                thread_queryset = ThreadPost.objects.none()
            else:
                raise ex
        # Phase 2.2: Use QueryOptimizationMixin for query optimization
        # Eliminates N+1 queries by eagerly loading related objects
        thread_queryset = self.optimize_thread_queryset(thread_queryset)
        # subquery = getPostQuery(request, token, None)
        # subquery = subquery & ~Q(threadpostview_post__user_id=str(request.user.id))
        # subquery = subquery & Q(Q(pk=OuterRef('pk')) | Q(main_post_id=OuterRef('pk')))
        # subquery = ThreadPost.objects.filter(subquery).prefetch_related('threadpostview_post')
        # subquery = subquery.filter(post_rel__in=[PostRelation.main_post.name, PostRelation.seq_post.name])
        # subquery = subquery.values('pk').annotate(unread_count=Coalesce(Count('pk', distinct=True), 0)).values('unread_count')[:1]
        # # thread_queryset = thread_queryset.annotate(unread_count = Coalesce(Count('id', distinct=True, filter=subquery), 0))
        # threads = thread_queryset.annotate(unread_count = Subquery(subquery)).values('unread_count')
        threads = thread_queryset.order_by("-id").only(*THREAD_LIST_FIELDS, "content")
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        response_data = {**threads, "message": "Post List Fetch Successfully"}
        # Cache the response for 60 seconds
        cache.set(cache_key, response_data, 60)
        return Response(response_data, status=200)

    def organisation_thread_list(self, request, *args, **kwargs):
        domain_handle = kwargs.get("domain_handle")
        org = checkSpaceOrg(domain_handle)
        org_role = checkOrgAccess(request.user, org, check_role=True)
        post_rel = [PostRelation.main_post.name, PostRelation.seq_post.name]
        thread_queryset = get_all_post_query(request, post_rel, org_role)
        thread_queryset = thread_queryset.filter(space__space_organization=org)
        # Phase 2.2: Use QueryOptimizationMixin for query optimization
        thread_queryset = self.optimize_thread_queryset(thread_queryset)
        threads = thread_queryset.order_by("-id").only(*THREAD_LIST_FIELDS, "content")
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response(
            {**threads, "message": "Post List Fetch Successfully"}, status=200
        )

    def pilot_thread_list(self, request, *args, **kwargs):
        pilot = kwargs.get("pilot")
        post_rel = [PostRelation.main_post.name, PostRelation.seq_post.name]
        thread_queryset = get_all_post_query(request, post_rel)
        thread_queryset = thread_queryset.filter(related_data__pilot=pilot)
        # Phase 2.2: Use QueryOptimizationMixin for query optimization
        thread_queryset = self.optimize_thread_queryset(thread_queryset)
        threads = thread_queryset.order_by("-id").only(*THREAD_LIST_FIELDS, "content")
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response(
            {**threads, "message": "Post List Fetch Successfully"}, status=200
        )

    def document_thread_list(self, request, *args, **kwargs):
        document_id = kwargs.get("document_id")
        post_rel = [PostRelation.main_post.name, PostRelation.seq_post.name]
        thread_queryset = get_all_post_query(request, post_rel)
        thread_queryset = thread_queryset.filter(ref_doc_id=document_id)
        # Phase 2.2: Use QueryOptimizationMixin for query optimization
        thread_queryset = self.optimize_thread_queryset(thread_queryset)
        threads = thread_queryset.order_by("-id").only(*THREAD_LIST_FIELDS, "content")
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response(
            {**threads, "message": "Post List Fetch Successfully"}, status=200
        )

    def create(self, request, *args, **kwargs):
        token = kwargs.get("token")
        post_type = request.data.get("post_type")
        from_request = "thread" if post_type in ["ask", "task"] else None
        space = checkPostSpaceAccess(
            request.user, token=token, check_op=True, from_request=from_request
        )
        context = {"request": request, "space": space}
        # TODO based on passed content, we need to create the title, tags from content using pilot.
        ser = ThreadCreateSerializer(data=request.data, context=context)
        if ser.is_valid():
            if "repeat_type" in request.data and request.data["repeat_type"]:
                date_str = request.data.get("date")  # e.g., '2024-09-18'
                time_str = request.data.get("time")  # e.g., '14:30'
                # Combine date and time and parse using strptime
                dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                # # Localize to IST using pytz
                # ist = pytz.timezone('Asia/Kolkata')
                # ist_time = ist.localize(dt)
                # # Convert to UTC and get the timestamp
                # utc_time = ist_time.astimezone(pytz.UTC)
                timestamp = dt.timestamp()
                post_cron = PostCreationCronModel.objects.create(
                    user_id=request.user.id,
                    space_token=space.token,
                    title=request.data.get("title"),
                    content=request.data.get("content"),
                    privacy_type=request.data.get("privacy_type"),
                    post_type=request.data.get("post_type"),
                    content_type=request.data.get("content_type"),
                    pilot=request.data.get("pilot"),
                    extra_data={
                        "knowledge_bases": request.data.get("knowledge_base", [])
                    },
                    repeat_type=request.data.get(
                        "repeat_type", PostRepeatType.once.name
                    ),
                    schedule_timestamp=timestamp,
                )
                return Response(
                    {
                        "data": {"post_id": post_cron.id},
                        "message": "Post Scheduled Successfully",
                    },
                    status=201,
                )
            else:
                instance = ser.save()
                if (
                    instance.post_type in ["task", "ask", "notebook"]
                    and instance.content_type != "voice"
                ):
                    addTaskToAgent(
                        instance.post_id,
                        instance.title,
                        instance.content,
                        request,
                        instance.post_type,
                        instance.space,
                    )
                create_event_trigger("send_post_email", instance)
                instance = ThreadDetailSerializer(
                    instance, context={"request": request}
                ).data
                return Response(
                    {"data": instance, "message": "Post Created Successfully"},
                    status=201,
                )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def retrieve(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post_id = extractPostId(post_slug)
        # print("Headers---> \n", request.headers, "\n\n post_slug---> ", post_slug)
        # Optimized: Full select_related and Prefetch with nested relations
        instance = (
            ThreadPost.objects.filter(post_id=post_id)
            .select_related(
                "main_post",
                "parent",
                "space",
                "space__space_organization",
                "space__space_organization__pilot",
                "user",
                "user__userbasicdetail_user",
            )
            .prefetch_related(
                "threadpost_parent",
                Prefetch(
                    "threadpostaccessrequest_post",
                    queryset=ThreadPostAccessRequest.objects.select_related("user", "role"),
                ),
                Prefetch(
                    "threadpostpermission_post",
                    queryset=ThreadPostPermission.objects.select_related(
                        "user", "user__userbasicdetail_user", "role"
                    ),
                ),
                Prefetch(
                    "postinvite_post",
                    queryset=PostInvite.objects.select_related("role"),
                ),
            )
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        try:
            instance, space = checkThreadPostAccess(
                request.user, instance.space, instance
            )
            # user_permissions = getUserPermissionOnEntity(request.user, instance, 'post')
        except APIException206 as ex:
            if (
                str(ex.detail.get("message"))
                == "You don't have access to do operation on this post."
                and instance.privacy_type != PrivacyType.private.value
            ):
                check_request = ThreadPostAccessRequest.objects.filter(
                    post=instance,
                    user_id=request.user.id,
                    is_joined=False,
                    is_expired=False,
                ).first()
                res = {**ex.detail}
                common_data = {
                    "slug": post_slug,
                    "title": instance.title,
                    "privacy_type": instance.privacy_type,
                    "space": get_user_data(
                        instance.space,
                        fields=["name", "token", "privacy_type", "space_type"],
                    ),
                    "user": get_user_data(
                        instance.user,
                        fields=[
                            "email",
                            "full_name",
                            "profile_color",
                            "profile_picture",
                        ],
                    ),
                    "subscribed": False,
                    "final_role": DEFAULT_POST_PERMISSION_ROLE,
                }
                res.update(common_data)
                res.update({"is_requested": check_request != None, "joined": False})
                if check_request:
                    res.update({"request_token": check_request.request_token})
                return Response(res, status=206)
            raise ex
        instance = ThreadDetailSerializer(instance, context={"request": request}).data
        instance["schema"] = generate_post_schema(instance)
        return Response(
            {"data": instance, "message": "Post Fetched Successfully"}, status=200
        )
        # return Response({"data": instance, "permissions": user_permissions, "message": "Post Fetched Successfully"}, status=200)

    def thread_previous(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        try:
            instance, space = checkThreadPostAccess(
                request.user, instance.space, instance
            )
            thread_queryset = getPostQuerySet(request, space.token)
        except APIException206 as ex:
            if str(ex.detail.get("message")) == "You Don't have Access to this Space":
                return Response(
                    {"data": [], "count": 0, "message": "Post List Fetch Successfully"}
                )
            raise ex

        thread_fields = [*THREAD_POST_LIST_FIELDS, "media", "media_data"]

        query = {
            "post_id__lt": instance.post_id,
            "space_id": space.id,
            "post_rel__in": [PostRelation.seq_post.name],
        }
        if instance.post_rel != "main_post":
            query.update(
                {
                    "post_rel__in": [
                        PostRelation.seq_post.name,
                        PostRelation.main_post.name,
                    ]
                }
            )

        thread_queryset = thread_queryset.filter(getPreviousQuerySet(instance))
        threads = (
            thread_queryset.filter(**query)
            .order_by("post_id")
            .only(*thread_fields)
            .prefetch_related(
                "threadpostpermission_post",
                "threadpostaccessrequest_post",
                "postinvite_post",
            )
        )
        # threads = UnpodCustomPagination(self.request, threads, ThreadPostListSerializer, kwargs={'context':{'request': request}})
        # threads = threads.get_paginated_response(return_dict=True)
        data = ThreadPostListSerializer(
            threads, many=True, context={"request": request}
        ).data
        threads = {"data": data, "count": threads.count()}
        return Response(
            {**threads, "message": "Post List Fetch Successfully"}, status=200
        )

    def thread_next(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel", "parent"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space", "parent")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)

        try:
            instance, space = checkThreadPostAccess(
                request.user, instance.space, instance
            )
            thread_queryset = getPostQuerySet(
                request, space.token, PostRelation.seq_post.name
            )
        except APIException206 as ex:
            if str(ex.detail.get("message")) == "You Don't have Access to this Space":
                return Response(
                    {"data": [], "count": 0, "message": "Post List Fetch Successfully"}
                )
            raise ex

        thread_fields = [*THREAD_POST_LIST_FIELDS, "media", "media_data"]

        query = {
            "post_id__gt": instance.post_id,
            "space_id": space.id,
            "post_rel": PostRelation.seq_post.name,
        }
        if instance.post_rel == PostRelation.main_post.name:
            query.update({"main_post_id": instance.id, "parent_id": instance.id})
        elif instance.post_rel == PostRelation.seq_post.name:
            query.update(
                {"main_post_id": instance.main_post_id, "parent_id": instance.parent.id}
            )

        threads = (
            thread_queryset.filter(**query)
            .order_by("post_id")
            .only(*thread_fields)
            .prefetch_related(
                "threadpostpermission_post",
                "threadpostaccessrequest_post",
                "postinvite_post",
            )
        )
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadPostListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response(
            {**threads, "message": "Post List Fetch Successfully"}, status=200
        )

    def update(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post_id = extractPostId(post_slug)
        instance_fields = ["main_post_id", "space", "post_rel"]
        make_private = False
        instance = (
            ThreadPost.objects.filter(post_id=post_id)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        if instance.post_rel == PostRelation.reply.name:
            return Response({"message": "Reply Can't be Update"})
        post, space = checkThreadPostAccess(request.user, instance.space, instance)
        checkPostOperationAccess(request.user, space, post)
        ser = PostUpdateSerializer(data=request.data)
        if ser.is_valid():
            instance, make_private = ser.update(instance, ser.validated_data, request)
            if make_private:
                makePostPrivateForPost(instance)
            instance = ThreadDetailSerializer(
                instance, context={"request": request}
            ).data
            return Response({"data": instance, "message": "Post Updated Successfully"})
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def delete(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post_type = self.request.query_params.get("post_type")
        if post_type == "block":
            headers = {"Authorization": request.headers.get("Authorization")}
            current_url = request._request.get_full_path_info()
            current_url = current_url.replace("/api/v1/", "")
            current_url = current_url.replace("threads", "conversation")
            current_url = current_url.replace("action", "block")
            hit = requests.delete(
                url=f"{settings.API_SERVICE_URL}/{current_url}", headers=headers, timeout=30
            )
            data = hit.json()
            status_code = 200 if hit.status_code == 200 else 206
            return Response(data, status=status_code)
        if not self.request.user or not self.request.user.is_authenticated:
            return Response(
                {"message": "Please First Login to Delete Post"}, status=206
            )
        instance_fields = ["main_post_id", "space", "post_rel"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        post, space = checkThreadPostAccess(request.user, instance.space, instance)
        checkPostOperationAccess(request.user, space, post)
        if instance.post_rel == "main_rel":
            sub_post = ThreadPost.objects.filter(
                main_post=instance, post_rel="seq_post"
            ).count()
            if sub_post:
                return Response(
                    {
                        "message": "Please First Remove All the SubPost, You can't delete Main Thread"
                    },
                    status=206,
                )
        instance.delete()
        return Response({"message": "Post Deleted Successfully"})

    def join_subscription(self, request, *args, **kwargs):
        if request.user and request.user.is_authenticated:
            post_slug = kwargs.get("post_slug")
            post = checkThreadPostSlug(post_slug)
            check_access = ThreadPostPermission.objects.filter(
                user=request.user, post=post
            ).first()
            if check_access:
                return Response(
                    {"message": "You Already have the Access to this Post"}, status=206
                )
            if post.privacy_type not in ["public", "link"]:
                return Response(
                    {"message": "You Only Subscribe to public Post"}, status=206
                )
            if post.post_rel == "reply":
                return Response({"message": "You can't subscribe to reply"}, status=206)
            role = getRole(role_code="viewer", role_type="post")
            obj = ThreadPostPermission.objects.create(
                post_id=post.id,
                role_id=role.id,
                user_id=request.user.id,
                grant_by=request.user.id,
            )
            data = ThreadDetailSerializer(post, context={"request": request}).data
            return Response({"message": "You subscribed the Post", "data": data})
        return Response({"message": "Please First Login to Add Request"}, status=206)

    def unsubscribe(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response({"message": "Please First Login"}, status=206)
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        check_access = ThreadPostPermission.objects.filter(
            user=request.user, post=post
        ).first()
        if not check_access:
            return Response(
                {"message": "You Don't have the Access to this Post"}, status=206
            )
        processDeletePermission(
            ThreadPostPermission,
            request.user.email,
            post=check_access.post,
        )
        return Response({"message": "Post Permission Removed Successfully"}, status=200)


class ThreadPostViewSet(viewsets.GenericViewSet):
    serializer_class = [CommonSerializer]
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        token = instance.space.token
        post, space = checkThreadPostAccess(request.user, instance.space, instance)
        thread_fields = [*THREAD_POST_LIST_FIELDS, "media", "media_data"]
        query = {"space_id": space.id, "post_rel": PostRelation.seq_post.name}

        if post.post_rel == PostRelation.main_post.name:
            query.update({"main_post_id": post.id, "parent_id": post.id})
        elif post.post_rel == PostRelation.seq_post.name:
            query.update({"main_post_id": post.main_post.id, "parent_id": post.id})
        else:
            raise APIException206({"message": "Invalid Post Id. Invalid Post Rel"})
        thread_queryset = getPostQuerySet(request, token, PostRelation.seq_post.name)
        threads = (
            thread_queryset.filter(**query)
            .order_by("seq_number")
            .only(*thread_fields)
            .prefetch_related(
                "threadpostpermission_post",
                "threadpostaccessrequest_post",
                "postinvite_post",
            )
        )
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadPostListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response(
            {**threads, "message": "Post List Fetch Successfully"}, status=200
        )

    def create(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        post, space = checkThreadPostAccess(request.user, instance.space, instance)
        checkPostOperationAccess(request.user, space, post)
        context = {"request": request, "space": space, "post": post}
        ser = ThreadPostCreateSerializer(data=request.data, context=context)
        if ser.is_valid():
            instance = ser.save()
            if (
                instance.post_type in ["task", "ask"]
                and instance.content_type != "voice"
            ):
                addTaskToAgent(
                    instance.post_id,
                    instance.title,
                    instance.content,
                    request,
                    instance.post_type,
                    instance.space,
                )
            instance = ThreadDetailSerializer(
                instance, context={"request": request}
            ).data
            return Response(
                {"data": instance, "message": "Post Created Successfully"}, status=201
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )


class ThreadPostReplyViewSet(viewsets.GenericViewSet):
    serializer_class = [CommonSerializer]
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        token = instance.space.token
        post, space = checkThreadPostAccess(request.user, instance.space, instance)
        query = {"space_id": space.id, "post_rel": PostRelation.reply.name}

        if post.post_rel == PostRelation.main_post.name:
            query.update({"main_post_id": post.id, "parent_id": post.id})
        else:
            query.update({"main_post_id": post.main_post.id, "parent_id": post.id})
        # else:
        #     raise APIException206({"message": "Invalid Post Id. Invalid Post Rel"})

        thread_queryset = getPostQuerySet(request, token, PostRelation.reply.name)
        threads = (
            thread_queryset.filter(**query)
            .prefetch_related("threadpost_parent", "threadpostpermission_post")
            .order_by("seq_number")
            .only(*THREAD_POST_REPLY_FIELDS)
        )
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadPostReplyListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response({**threads, "message": "Reply Fetch Successfully"}, status=200)

    def create(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        post, space = checkThreadPostAccess(request.user, instance.space, instance)
        context = {"request": request, "space": space, "post": post}
        ser = ThreadPostReplyCreateSerializer(data=request.data, context=context)
        if ser.is_valid():
            instance = ser.save()
            instance = ThreadPostReplySerializer(
                instance, context={"request": request}
            ).data
            return Response(
                {"data": instance, "message": "Reply Created Successfully"}, status=201
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def reply_next(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["main_post_id", "space", "post_rel", "parent"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug)
            .select_related("space", "parent")
            .only(*instance_fields)
            .first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        instance, space = checkThreadPostAccess(request.user, instance.space, instance)
        thread_queryset = getPostQuerySet(request, space.token, PostRelation.reply.name)

        query = {
            "post_id__gt": instance.post_id,
            "space_id": space.id,
            "post_rel": PostRelation.reply.name,
        }
        if instance.post_rel == PostRelation.main_post.name:
            query.update({"main_post_id": instance.id, "parent_id": instance.id})
        else:
            query.update(
                {"main_post_id": instance.main_post_id, "parent_id": instance.parent.id}
            )

        threads = (
            thread_queryset.filter(**query)
            .prefetch_related("threadpost_parent")
            .order_by("seq_number")
            .only(*THREAD_POST_REPLY_FIELDS)
        )
        threads = UnpodCustomPagination(
            self.request,
            threads,
            ThreadPostReplyListSerializer,
            kwargs={"context": {"request": request}},
        )
        threads = threads.get_paginated_response(return_dict=True)
        return Response({**threads, "message": "Reply Fetch Successfully"}, status=200)


class ThreadPostEventViewSet(viewsets.GenericViewSet):
    serializer_class = [CommonSerializer]
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def viewer(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["view_count", "post_id"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug).only(*instance_fields).first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        ThreadPostView.objects.create(user_id=str(request.user.id), post_id=instance.id)
        ThreadPost.objects.filter(id=instance.id).update(view_count=F("view_count") + 1)
        return Response({"message": "Post View Updated"}, status=200)

    def update_reaction(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post_type = self.request.query_params.get("post_type")
        if post_type == "block":
            ser = PostReactionCreate(data=request.data)
            if not ser.is_valid():
                return Response(
                    {"message": "There is some Validation error", "errors": ser.errors},
                    status=206,
                )
            headers = {"Authorization": request.headers.get("Authorization")}
            validated_data = ser.validated_data
            current_url = request._request.get_full_path_info()
            current_url = current_url.replace("/api/v1/", "")
            current_url = current_url.replace("threads", "conversation")
            hit = requests.post(
                url=f"{settings.API_SERVICE_URL}/{current_url}",
                json=validated_data,
                headers=headers,
                timeout=30,
            )
            data = hit.json()
            status_code = 200 if hit.status_code == 200 else 206
            return Response(data, status=status_code)
        instance_fields = ["post_id"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug).only(*instance_fields).first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        ser = PostReactionCreate(data=request.data)
        if ser.is_valid():
            validated_data = ser.validated_data
            reaction_count = validated_data.get("reaction_count")
            reactionObj = ThreadPostReaction.objects.create(
                user_id=request.user.id,
                post_id=instance.id,
                object_id=str(instance.post_id),
                object_type="post",
                reaction_count=reaction_count,
                reaction_type=validated_data["reaction_type"],
            )
            # reactionObj, created = ThreadPostReaction.objects.get_or_create(
            #     user_id = request.user.id, post_id = instance.id,
            #     object_id = str(instance.post_id), object_type = 'post'
            # )
            # ThreadPostReaction.objects.filter(id = reactionObj.id).update(reaction_type=validated_data['reaction_type'])
            # if created:
            ThreadPost.objects.filter(id=instance.id).update(
                reaction_count=F("reaction_count") + reaction_count
            )
            return Response(
                {
                    "message": "",
                    "data": {"reaction": True, "reaction_count": reaction_count},
                },
                status=200,
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def reaction_info(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        instance_fields = ["post_id"]
        instance = (
            ThreadPost.objects.filter(slug=post_slug).only(*instance_fields).first()
        )
        if not instance:
            return Response({"message": "Invalid Post Id"}, status=206)
        reactionObj = (
            ThreadPostReaction.objects.filter(
                user_id=request.user.id,
                post_id=instance.id,
                object_id=str(instance.post_id),
                object_type="post",
            )
            .values("reaction_type", "reaction_at")
            .first()
        )
        resData = {"reaction": reactionObj is not None, **(reactionObj or {})}
        return Response(
            {"message": "Reaction Info Fetch Successfully", "data": resData}, status=200
        )


class ThreadRolesViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def permission_add(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        checkPostOperationAccess(request.user, space, post)
        ser = ThreadRolePermissionCreateSerializer(data=request.data, many=True)
        if ser.is_valid():
            user_list = ser.validated_data
            success_list, error_list, invite_list = createThreadPermission(
                post, user_list, request, create_owner=False
            )
            success_list.extend(invite_list)
            if post.privacy_type == "private" and len(success_list):
                ThreadPost.objects.filter(id=post.id).update(privacy_type="shared")
            return Response(
                {
                    "message": "Post Permission Updated Successfully",
                    "data": {"failed_invite": error_list, "success_data": success_list},
                },
                status=200,
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def permission_update(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        checkPostOperationAccess(request.user, space, post)
        ser = ThreadRolePermissionCreateSerializer(data=request.data)
        if ser.is_valid():
            validated_data = ser.validated_data
            user_email = validated_data["email"]
            if user_email == request.user.email:
                raise APIException206(
                    {"message": "You Can't Update the Permission of Self"}
                )
            processUpdatePermission(
                ThreadPostPermission,
                validated_data["role_code"],
                validated_data["email"],
                post=post,
            )
            return Response(
                {"message": "Post Permission Updated Successfully"}, status=200
            )
        return Response(
            {"errors": ser.errors, "message": "Required Parameter Missing"}, status=206
        )

    def permission_delete(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        checkPostOperationAccess(request.user, space, post)
        user_email = request.GET.get("email")
        user_email = urllib.parse.quote_plus(user_email).replace("%40", "@")
        if not user_email:
            raise APIException206({"message": "Please Provide the Email"})
        if user_email == request.user.email:
            raise APIException206(
                {"message": "You Can't Delete the Permission of Self"}
            )
        processDeletePermission(ThreadPostPermission, user_email, post=post)
        return Response({"message": "Post Permission Delete Successfully"}, status=200)

    def ownership_transfer(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        thread_role = (
            ThreadPostPermission.objects.filter(
                user_id=request.user.id, post_id=post.id
            )
            .select_related("post", "user", "role")
            .first()
        )
        if thread_role.role.role_code != "owner":
            raise APIException206(
                {
                    "message": "You must have the permission of owner to transfer the ownership"
                }
            )
        user_email = request.GET.get("email")
        if not user_email:
            raise APIException206({"message": "Please Provide the Email"})
        # user_email = urllib.parse.quote_plus(user_email).replace("%40", "@")
        if user_email == request.user.email:
            raise APIException206(
                {"message": "You Can't Update the Permission of Self"}
            )
        processUpdatePermission(
            ThreadPostPermission,
            "owner",
            user_email,
            post=post,
        )
        post_rel = post.post_rel
        if post.post_rel == "seq_post":
            post_rel = "post"
        redis_key = f"user_roles_{user_email}_{post_rel}_{post.post_id}"
        role = getRole("editor", "post")
        thread_role.role = role
        thread_role.save()
        thread_role.refresh_from_db()
        cache.delete(redis_key)
        return Response({"message": "Post Permission Updated Successfully"}, status=200)


class ThreadAccessRequestViewSet(viewsets.GenericViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def request_add(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if post.privacy_type == "private":
            return Response(
                {"message": "You can't Request to Private Post"}, status=206
            )
        if request.user and request.user.is_authenticated:
            check_request = ThreadPostAccessRequest.objects.filter(
                user=request.user, post=post, is_joined=False, is_expired=False
            ).first()
            if check_request:
                return Response(
                    {"message": "You Already Requested for Access for this Post"},
                    status=206,
                )
            post_users = list(
                post.threadpostpermission_post.all().values_list(
                    "user__email", flat=True
                )
            )
            if request.user.email in post_users:
                return Response(
                    {"message": "You Already have access to this Post"}, status=206
                )
            role = getRole(role_code="viewer", role_type="post")
            access_data = {
                "user_id": request.user.id,
                "post_id": post.id,
                "role_id": role.id,
                "created_by": request.user.id,
                "updated_by": request.user.id,
            }
            check_request = ThreadPostAccessRequest.objects.create(**access_data)
            return Response(
                {
                    "message": "Your Access Request has been received",
                    "data": {"request_token": check_request.request_token},
                }
            )
        return Response({"message": "Please First Login to Add Request"}, status=206)

    def request_accpet(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        request_token = kwargs.get("request_token")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        checkPostOperationAccess(request.user, space, post)
        check_request = ThreadPostAccessRequest.objects.filter(
            post=post, request_token=request_token
        ).first()
        if check_request:
            if check_request.is_expired:
                return Response(
                    {"message": "This Access Request Is Expired"}, status=206
                )
            if check_request.is_joined:
                return Response(
                    {"message": "This Access Request Already Accepted"}, status=200
                )
            user_list = [
                {
                    "email": check_request.user.email,
                    "role_code": check_request.role.role_code,
                }
            ]
            success_list, error_list, invite_list = createThreadPermission(
                post, user_list, request, create_owner=False
            )
            if len(success_list):
                today = timezone.now()
                update_data = {
                    "request_verified": True,
                    "is_joined": True,
                    "request_verify_dt": today,
                    "joined_dt": today,
                    "updated_by": request.user.id,
                }
                ThreadPostAccessRequest.objects.filter(id=check_request.id).update(
                    **update_data
                )
            return Response(
                {
                    "message": "Post Permission Updated Successfully",
                    "data": {"failure": error_list, "success": success_list},
                },
                status=200,
            )
        return Response({"message": "Please Provide Valid Request"}, status=206)

    def request_update(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        request_token = kwargs.get("request_token")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        checkPostOperationAccess(request.user, space, post)
        check_request = ThreadPostAccessRequest.objects.filter(
            post=post, request_token=request_token
        ).first()
        if not check_request:
            return Response({"message": "Please Provide Valid Request"}, status=206)
        if check_request.is_expired:
            return Response({"message": "This Access Request Is Expired"}, status=206)
        ser = ThreadAccessRequestUpdateSerializer(data=request.data)
        if ser.is_valid():
            role = getRole(
                role_code=ser.validated_data.get("role_code"), role_type="post"
            )
            ThreadPostAccessRequest.objects.filter(id=check_request.id).update(
                role_id=role.id, updated_by=request.user.id
            )
            return Response({"message": "Access Request Has been Updated"})
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def request_delete(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        request_token = kwargs.get("request_token")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        checkPostOperationAccess(request.user, space, post)
        check_request = ThreadPostAccessRequest.objects.filter(
            post=post, request_token=request_token
        ).first()
        if not check_request:
            return Response({"message": "Please Provide Valid Request"}, status=206)
        if check_request.is_expired:
            return Response({"message": "This Access Request Is Expired"}, status=206)
        if check_request.is_joined:
            return Response(
                {
                    "message": "This Access Request Already Accepted, You can't delete this request"
                },
                status=200,
            )
        ThreadPostAccessRequest.objects.filter(id=check_request.id).update(
            is_expired=True, updated_by=request.user.id
        )
        return Response({"message": "Access request denied"})

    def request_resend(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        request_token = kwargs.get("request_token")
        post = checkThreadPostSlug(post_slug)
        if request.user and request.user.is_authenticated:
            check_request = ThreadPostAccessRequest.objects.filter(
                post=post, request_token=request_token, user=request.user
            ).first()
            if not check_request:
                return Response({"message": "Please Provide Valid Request"}, status=206)
            if check_request.is_expired:
                return Response(
                    {"message": "This Access Request Is Expired"}, status=206
                )
            if check_request.is_joined:
                return Response(
                    {
                        "message": "This Access Request Already Accepted, You can't delete this request"
                    },
                    status=206,
                )
            ThreadPostAccessRequest.objects.filter(id=check_request.id).update(
                is_expired=True, updated_by=request.user.id
            )
            access_data = {
                "user_id": check_request.user.id,
                "post_id": check_request.post.id,
                "role_id": check_request.role.id,
                "created_by": request.user.id,
                "updated_by": request.user.id,
            }
            check_request = ThreadPostAccessRequest.objects.create(**access_data)
            return Response(
                {
                    "message": "Your Request Access has been resend",
                    "data": {"request_token": check_request.request_token},
                }
            )
        return Response({"message": "Please First Login to Add Request"}, status=206)


class ThreadSharedViewSet(viewsets.GenericViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def list(self, request, *args, **kwargs):
        query = Q()
        query.add(Q(user=request.user), Q.AND)
        query.add(Q(post__isnull=False), Q.AND)
        query.add(Q(post__post_rel__in=["main_post", "seq_post"]), Q.AND)
        query.add(~Q(role__role_code__in=["owner"]), Q.AND)
        search = request.GET.get("search")
        blocked_post = getBlockedPost(request, None)
        blocked_post = blocked_post.values_list("post_id", flat=True)
        query.add(~Q(id__in=list(blocked_post)), Q.AND)
        private_post = ThreadPostPermission.objects.filter(query).order_by("-created")
        paginator, page, page_size = getPaginator(private_post, request)
        page_data = paginator.page(page)
        private_post = page_data.object_list.values_list("post_id", flat=True)
        thread_queryset = ThreadPost.objects.filter(
            id__in=list(private_post), post_status=PostStatus.published.name
        ).select_related(
            "user", "user__userbasicdetail_user", "space", "space__space_organization"
        )
        # thread_queryset = thread_queryset.prefetch_related(
        #     Prefetch('threadpostaccessrequest_post',
        #              queryset=ThreadPostAccessRequest.objects.filter(is_joined=False, request_verified=False, is_expired=False).select_related(
        #                  'user', 'role', 'user__userbasicdetail_user').order_by(
        # '-id').only('user__email', 'user__first_name', 'user__last_name', 'role__role_code', 'request_token', 'created', 'is_expired', 'user__userbasicdetail_user__profile_color')))
        if search and search != "":
            thread_queryset = thread_queryset.filter(title__icontains=search)
        thread_fields = [*THREAD_POST_LIST_FIELDS, "media", "media_data"]
        threads = thread_queryset.order_by("-id").only(*thread_fields)
        threads = ThreadPostListOrgSerializer(
            threads, many=True, context={"request": request}
        ).data
        return Response(
            {
                "data": threads,
                "count": page_data.paginator.count,
                "message": "Shared Post List Fetch Successfully",
            },
            status=200,
        )


class ThreadPostReportViewSet(viewsets.GenericViewSet):
    serializer_class = [CommonSerializer]
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        ser = PostReportCreateSerializer(data=request.data)
        if ser.is_valid():
            if post.user.id == request.user.id:
                return Response(
                    {"message": "You Can't Report this post, As you are the owner"},
                    status=206,
                )
            check_report = PostReport.objects.filter(
                post_id=post.id, user_id=request.user.id
            ).first()
            message = ser.validated_data.get("message")
            category = ser.validated_data.get("category")
            other = ser.validated_data.get("other", "")
            if category == "other":
                category = f"other - {other}"
            if not check_report:
                check_report = PostReport.objects.create(
                    post_id=post.id,
                    user_id=request.user.id,
                    created_by=request.user.id,
                    updated_by=request.user.id,
                    message=message,
                    category=category,
                )
                PostBlockList.objects.create(
                    post_id=post.id,
                    user_id=request.user.id,
                    post_report_id=check_report.id,
                    created_by=request.user.id,
                    updated_by=request.user.id,
                )
                return Response(
                    {
                        "message": "Post Reported Successfully, we will review your report and do appropriate action"
                    }
                )
            return Response({"message": "You Already Reported this Post"}, status=206)
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )


class ThreadExploreViewSet(viewsets.GenericViewSet):
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def list(self, request, *args, **kwargs):
        blocked_post = getBlockedPost(request, None)
        blocked_post = blocked_post.values_list("post_id", flat=True)
        search = request.GET.get("search")
        query = Q()
        if request.user and request.user.is_authenticated:
            query.add(~Q(user_id=request.user.id), Q.AND)
        query.add(~Q(id__in=list(blocked_post)), Q.AND)
        query.add(
            Q(privacy_type="public", post_rel__in=["main_post", "seq_post"]), Q.AND
        )
        query.add(Q(space__is_default=False), Q.AND)
        thread_queryset = ThreadPost.objects.filter(
            query, post_status=PostStatus.published.name
        ).select_related(
            "user", "user__userbasicdetail_user", "space", "space__space_organization"
        )
        thread_fields = [*THREAD_POST_LIST_FIELDS, "media", "media_data"]
        if search and search != "":
            thread_queryset = thread_queryset.filter(title__icontains=search)
        threads = thread_queryset.order_by("-modified").only(*thread_fields)
        page = 1
        page_size = 8
        threads = threads[(page - 1) * page_size : page * page_size]
        data = ThreadPostListOrgSerializer(
            threads, many=True, context={"request": request}
        ).data
        threads = {"data": data}
        # threads = threads.get_paginated_response(return_dict=True)
        return Response(
            {**threads, "message": "Trending Post Fetch Successfully"}, status=200
        )


class ThreadAgoraViewSet(viewsets.GenericViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def livesession_start(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        user = request.user
        if post.is_live:
            activityObj = PostCommunicationActivity.objects.filter(
                post_id=post.id, id=post.live_id, live_status=True
            ).last()
            token = AgoraUtil.generate_agora_token(
                request.user, activityObj.channel_name
            )
            data = {
                "token": token,
                "channel_name": activityObj.channel_name,
                "uid": user.id,
            }
            return Response(
                {"message": "Live session already started", "data": data}, status=200
            )
        channel_name = AgoraUtil.create_live_channel(post, user)
        live_id = PostCommunicationActivity.objects.create(
            post_id=post.id,
            user_id=user.id,
            created_by=user.id,
            updated_by=user.id,
            live_status=True,
            start_dt=timezone.now(),
            channel_name=channel_name,
        ).id
        token = AgoraUtil.generate_agora_token(user, channel_name)
        ThreadPost.objects.filter(id=post.id).update(is_live=True, live_id=live_id)
        return Response(
            {
                "message": "Live session started",
                "data": {"token": token, "channel_name": channel_name, "uid": user.id},
            },
            status=200,
        )

    def livesession_stop(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response({"message": "No live session"}, status=206)
        activityObj = PostCommunicationActivity.objects.filter(
            post_id=post.id, id=post.live_id, live_status=True
        ).last()
        if activityObj:
            PostCommunicationActivity.objects.filter(id=activityObj.id).update(
                live_status=False, end_dt=timezone.now()
            )
            recordingObj = PostSessionRecording.objects.filter(
                session_id=activityObj.id
            ).last()
            if recordingObj and recordingObj.recording_status:
                recordingObj, status = AgoraUtil.stop_live_recording(recordingObj)
                if status:
                    processSessionRecording(
                        recordingObj.id, request, post.post_id, AgoraUtil
                    )
        ThreadPost.objects.filter(id=post.id).update(is_live=False)
        return Response({"message": "Live session Stopped"}, status=200)

    def livesession_token(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response({"message": "No live session"}, status=206)
        user = request.user
        activityObj = PostCommunicationActivity.objects.filter(
            post_id=post.id, id=post.live_id, live_status=True
        ).last()
        if not activityObj:
            return Response({"message": "No live session history found"}, status=206)
        channel_name = activityObj.channel_name
        token = AgoraUtil.generate_agora_token(user, channel_name)
        return Response(
            {
                "message": "Live session token fetched",
                "data": {"token": token, "channel_name": channel_name, "uid": user.id},
            },
            status=200,
        )

    def recording_start(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response(
                {"message": "No live session, Please start the session first"},
                status=200,
            )
        live_id = post.live_id
        activityObj = PostCommunicationActivity.objects.filter(
            id=live_id, live_status=True
        ).last()
        if activityObj:
            recordingObj = PostSessionRecording.objects.filter(
                session_id=live_id
            ).last()
            if recordingObj and recordingObj.recording_status:
                return Response(
                    {"message": "Live session recording already started"}, status=200
                )
            recordingObj = PostSessionRecording.objects.create(session_id=live_id)
            recordingObj, status = AgoraUtil.start_live_recording(recordingObj)
            if status:
                time.sleep(2)
                recordingObj, status = AgoraUtil.check_live_recording(recordingObj)
                if status:
                    return Response(
                        {"message": "Live session recording started"}, status=200
                    )
                return Response(
                    {
                        "message": "Live session recording not started due to some error",
                        "errors": recordingObj,
                    },
                    status=206,
                )
            return Response(
                {
                    "message": "Live session recording not started due to some error",
                    "errors": recordingObj,
                },
                status=206,
            )
        else:
            return Response(
                {"message": "No live session, Please start the session first"},
                status=200,
            )

    def recording_stop(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response(
                {"message": "No live session, Please start the session first"},
                status=200,
            )
        live_id = post.live_id
        activityObj = PostCommunicationActivity.objects.filter(
            id=live_id, live_status=True
        ).last()
        if activityObj:
            recordingObj = PostSessionRecording.objects.filter(
                session_id=live_id
            ).last()
            if not recordingObj or not recordingObj.recording_status:
                return Response(
                    {"message": "Live session recording not started"}, status=200
                )
            recordingObj, status = AgoraUtil.stop_live_recording(recordingObj)
            if status:
                recordingObj, post_instances = processSessionRecording(
                    recordingObj.id, request, post.post_id, AgoraUtil
                )
                # TODO: what should be done here? i have retuned the request response as of now
                # post_data = ThreadPostListSerializer(post_instances, many=True, context={'request': request}).data
                return Response(
                    {
                        "message": "Live session recording stopped",
                        "data": post_instances,
                    },
                    status=200,
                )
            return Response(
                {
                    "message": "Live session recording not stopped due to some error",
                    "errors": recordingObj.recording_reponse,
                },
                status=206,
            )
        return Response(
            {"message": "No live session, Please start the session first"}, status=200
        )


class ThreadHMSViewSet(viewsets.GenericViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def get_data(self, activityObj, role):
        codes = [
            room_code
            for room_code in activityObj.activity_config.get("room_codes", [])
            if room_code.get("role") == role
        ]
        if not codes:
            raise APIException206(
                {"message": "Session Not Properly Started, Start a New Session."}
            )
        return {
            "room_id": activityObj.activity_config.get("session_data", {}).get("id"),
            "host_room_code": codes[0],
            "channel_name": activityObj.channel_name,
        }

    def livesession_start(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        user = request.user
        if post.is_live:
            activityObj = PostCommunicationActivity.objects.filter(
                post_id=post.id, id=post.live_id, live_status=True
            ).last()
            data = self.get_data(activityObj, "host")
            return Response(
                {"message": "Live session already started", "data": data}, status=200
            )
        hms = HMS()
        channel_name = hms.create_live_channel(post, user)
        data, status = hms.create_room(channel_name)
        if not status:
            return Response(
                {"message": "Live session not started", "errors": data}, status=206
            )

        codes, status = hms.create_room_codes(data.get("id"))
        if not status:
            return Response(
                {"message": "Live session not started", "errors": codes}, status=206
            )
        activityObj = PostCommunicationActivity.objects.create(
            post_id=post.id,
            user_id=user.id,
            created_by=user.id,
            updated_by=user.id,
            live_status=True,
            start_dt=timezone.now(),
            channel_name=channel_name,
            activity_config={
                "session_data": data,
                "room_codes": codes.get("data"),
            },
        )
        ThreadPost.objects.filter(id=post.id).update(
            is_live=True, live_id=activityObj.id
        )
        return Response(
            {
                "message": "Live session started",
                "data": self.get_data(activityObj, "host"),
            },
            status=200,
        )

    def livesession_stop(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response({"message": "No live session"}, status=206)
        activityObj = PostCommunicationActivity.objects.filter(
            post_id=post.id, id=post.live_id, live_status=True
        ).last()
        if activityObj:
            hms = HMS()
            hms.disable_room(
                activityObj.activity_config.get("session_data", {}).get("id")
            )
            PostCommunicationActivity.objects.filter(id=activityObj.id).update(
                live_status=False, end_dt=timezone.now()
            )
            recordingObj = PostSessionRecording.objects.filter(
                session_id=activityObj.id
            ).last()
            if recordingObj and recordingObj.recording_status:
                recordingObj, status = HMS.stop_live_recording(recordingObj)
                if status:
                    processSessionRecording(recordingObj.id, request, post.post_id, HMS)
        ThreadPost.objects.filter(id=post.id).update(is_live=False)
        return Response({"message": "Live session Stopped"}, status=200)

    def livesession_code(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response({"message": "No live session"}, status=206)
        user = request.user
        activityObj = PostCommunicationActivity.objects.filter(
            post_id=post.id, id=post.live_id, live_status=True
        ).last()
        if not activityObj:
            return Response({"message": "No live session history found"}, status=206)
        data = self.get_data(activityObj, "host")
        return Response({"message": "Live session data", "data": data}, status=200)

    def recording_start(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response(
                {"message": "No live session, Please start the session first"},
                status=200,
            )
        live_id = post.live_id
        activityObj = PostCommunicationActivity.objects.filter(
            id=live_id, live_status=True
        ).last()
        if activityObj:
            recordingObj = PostSessionRecording.objects.filter(
                session_id=live_id
            ).last()
            if recordingObj and recordingObj.recording_status:
                return Response(
                    {"message": "Live session recording already started"}, status=200
                )
            recordingObj = PostSessionRecording.objects.create(session_id=live_id)
            recordingObj, status = HMS.start_live_recording(recordingObj)
            if status:
                return Response(
                    {"message": "Live session recording started"}, status=200
                )
            return Response(
                {
                    "message": "Live session recording not started due to some error",
                    "errors": recordingObj,
                },
                status=206,
            )
        else:
            return Response(
                {"message": "No live session, Please start the session first"},
                status=200,
            )

    def recording_stop(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        if not post.is_live:
            return Response(
                {"message": "No live session, Please start the session first"},
                status=200,
            )
        live_id = post.live_id
        activityObj = PostCommunicationActivity.objects.filter(
            id=live_id, live_status=True
        ).last()
        if activityObj:
            recordingObj = PostSessionRecording.objects.filter(
                session_id=live_id
            ).last()
            if not recordingObj or not recordingObj.recording_status:
                return Response(
                    {"message": "Live session recording not started"}, status=200
                )
            recordingObj, status = HMS.stop_live_recording(recordingObj)
            if status:
                recordingObj, post_instances = processSessionRecording(
                    recordingObj.id, request, post.post_id, HMS
                )
                return Response(
                    {
                        "message": "Live session recording stopped",
                        "data": post_instances,
                    },
                    status=200,
                )
            return Response(
                {
                    "message": "Live session recording not stopped due to some error",
                    "errors": recordingObj.recording_reponse,
                },
                status=206,
            )
        return Response(
            {"message": "No live session, Please start the session first"}, status=200
        )


class ThreadWebhookViewSet(viewsets.GenericViewSet):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def post(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        if post_slug != "webhook_post":
            print(request.data)
            return Response({"message": "Invalid Webhook URL"}, status=200)
        auth_token = request.headers.get("X-Auth-100ms")
        if auth_token != settings.HMS.get("app_access_key"):
            return Response({"message": "Invalid Webhook URL"}, status=200)
        request_data = request.data
        event = request_data.get("type")
        event_data = request_data.get("data")
        if event == "beam.recording.success":
            room_name = event_data.get("room_name")
            recordingObj = PostSessionRecording.objects.filter(
                session__channel_name=room_name
            ).last()
            if recordingObj:
                if not recordingObj.post_created:
                    pass
        return Response({"message": "Webhook Received"}, status=200)


class ThreadAnonymousViewSet(viewsets.GenericViewSet):
    permission_classes = [
        AllowAny,
    ]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def throttled(self, request, wait):
        """
        If request is throttled, determine what kind of exception to raise.
        """
        raise APIException206(
            {
                "message": f"You are being rate limited, please wait for {int(wait)} seconds"
            }
        )

    def create(self, request, *args, **kwargs):
        throttler = UnpodRateThrottler()
        bypass_throttler = False
        if request.user.is_authenticated and request.user.email in [
            "loadtestuser1@example.com"
        ]:
            bypass_throttler = True
        check_throttler = throttler.allow_request(request, self, True)
        if not check_throttler and not bypass_throttler:
            return self.throttled(request, throttler.wait())
        space = get_anonymous_space()
        context = {"request": request, "space": space}
        ser = ThreadAnonymousCreateSerializer(data=request.data, context=context)
        if ser.is_valid():
            instance = ser.save()
            if (
                instance.post_type in ["task", "ask"]
                and instance.content_type != "voice"
            ):
                addTaskToAgent(
                    instance.post_id,
                    instance.title,
                    instance.content,
                    request,
                    instance.post_type,
                    instance.space,
                )
            instance = ThreadDetailSerializer(
                instance, context={"request": request}
            ).data
            if not bypass_throttler:
                throttler.throttle_success()
            return Response(
                {"data": instance, "message": "Post Created Successfully"}, status=201
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def public_thread_create(self, request, *args, **kwargs):
        space_token = request.data.get("space_token")
        space = get_space_by_query(token=space_token)
        if not space:
            return Response({"message": "Invalid Space Token"}, status=206)
        if space.privacy_type != "public":
            return Response({"message": "Space is not public"}, status=206)
        context = {"request": request, "space": space}
        ser = ThreadAnonymousCreateSerializer(data=request.data, context=context)
        if ser.is_valid():
            instance = ser.save()
            if (
                instance.post_type in ["task", "ask"]
                and instance.content_type != "voice"
            ):
                addTaskToAgent(
                    instance.post_id,
                    instance.title,
                    instance.content,
                    request,
                    instance.post_type,
                    instance.space,
                )
            instance = ThreadDetailSerializer(
                instance, context={"request": request}
            ).data
            return Response(
                {"data": instance, "message": "Post Created Successfully"}, status=201
            )
        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )


class HasValidAPIToken(BasePermission):
    def has_permission(self, request, view):
        return request.auth is not None


class PublicThreadViewSet(viewsets.ModelViewSet):
    authentication_classes = [StaticAPITokenAuthentication]
    permission_classes = [HasValidAPIToken]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def create_thread(self, request, *args, **kwargs):
        space_id = request.data.get("space_id")
        user_id = request.data.get("user_id")

        from unpod.space.models import Space

        space = Space.objects.filter(id=space_id).first()

        if not space:
            return Response({"message": "Invalid Space Token"}, status=206)

        if not user_id:
            return Response({"message": "Invalid User ID"}, status=206)

        context = {"request": request, "space": space}
        ser = PublicThreadAnonymousCreateSerializer(data=request.data, context=context)

        if ser.is_valid():
            instance = ser.save()

            instance = PublicThreadAnonymousCreateSerializer(
                instance, context={"request": request}
            ).data

            return Response(
                {"data": instance, "message": "Post Created Successfully"},
                status=201,
            )

        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )

    def update_thread(self, request, *args, **kwargs):
        post_id = kwargs.get("thread_id")

        if not post_id:
            return Response({"message": "Invalid Post ID"}, status=206)

        instance = ThreadPost.objects.filter(post_id=post_id).first()

        if not instance:
            return Response({"message": "Post not found"}, status=206)

        ser = PublicThreadUpdateSerializer(data=request.data)

        if ser.is_valid():
            updated_instance = ser.update(instance, ser.validated_data)
            return Response(
                {
                    "data": {
                        "post_id": str(updated_instance.post_id),
                        "content": updated_instance.content,
                        "tags": updated_instance.tags,
                    },
                    "message": "Post Updated Successfully",
                },
                status=200,
            )

        return Response(
            {"message": "There is some Validation error", "errors": ser.errors},
            status=206,
        )
