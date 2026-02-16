from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from unpod.common.livekit_server.constants import CENTRAL_AGENT_NAME, ENGLISH_AGENT_NAME
from unpod.common.livekit_server.room import (
    delete_room_server,
    generate_room_token_server,
)
from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.string import get_random_string
from unpod.core_components.utils import get_user_data
from unpod.core_components.voices.utils import generate_public_post_by_voice
from unpod.space.utils import checkSpaceAccess
from unpod.thread.services import checkThreadPostAccess, checkThreadPostSlug
from unpod.space.models import Space


class LiveKitVoiceViewSet(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["room_livekit_token", "livekit_delete_room"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_livekit_token(self, request, *args, **kwargs):
        post_slug = kwargs.get("post_slug")
        post = checkThreadPostSlug(post_slug)
        post, space = checkThreadPostAccess(request.user, post.space, post)
        multimodality = request.query_params.get("multimodality", "text_audio")
        # Allow text content type when multimodality is text
        allowed_content_types = ["voice"]
        if multimodality == "text":
            allowed_content_types.append("text")
        if post.content_type not in allowed_content_types:
            return Response({"message": "Invalid Post Type"}, status=206)
        room_name = f"{post.slug}-{space.token}-{int(timezone.now().timestamp())}"
        user_data = get_user_data(request.user)
        room_metadata = {
            "token": space.token,
            "space_token": space.token,
            "space_name": space.name,
            "space_slug": space.slug,
            "post_slug": post_slug,
            "thread_id": post.post_id,
            "contact_name": request.user.full_name,
            "user": user_data,
        }
        room_metadata["multimodality"] = multimodality
        agent_name = ENGLISH_AGENT_NAME
        if self.request.query_params.get("source") == "superkik":
            agent_name = CENTRAL_AGENT_NAME
        # agent_name = "unpod-qa-general-agent"
        user_data = {
            "user_token": request.user.user_token,
            "full_name": request.user.full_name,
        }
        data = generate_room_token_server(
            room_name, agent_name, room_metadata, user_data
        )
        return Response({**data})

    def room_livekit_token(self, request, *args, **kwargs):
        contact_name = request.data.get("contact_name")
        contact_number = request.data.get("contact_number")
        space_token = request.data.get("space_token")
        agent_name = request.data.get("agent_name")
        agent_handle = request.data.get("agent_handle") or request.data.get("agent_id")

        if not space_token:
            return Response({"message": "Invalid data"}, status=206)
        space = Space.objects.filter(token=space_token).first()
        if not space:
            return Response({"message": "Invalid space token"}, status=206)
        if space.privacy_type != "public":
            if not request.user.is_authenticated:
                return Response({"message": "Space is not public"}, status=206)
            space_role = checkSpaceAccess(request.user, space, check_role=True)
        post = generate_public_post_by_voice(request, space)
        if not post:
            room_name = f"{get_random_string('room-', length=10)}-{space_token}-{int(timezone.now().timestamp())}"
        else:
            room_name = f"{post.slug}-{space_token}-{int(timezone.now().timestamp())}"
        agent_name = ENGLISH_AGENT_NAME
        if self.request.data.get("source") == "superkik":
            agent_name = CENTRAL_AGENT_NAME
        if contact_number:
            contact_number = contact_number.strip()

        room_metadata = {
            "token": space_token,
            "space_token": space_token,
            "space_name": space.name,
            "space_slug": space.slug,
        }
        room_metadata["multimodality"] = request.data.get("multimodality", "text_audio")
        if post:
            room_metadata["thread_id"] = post.post_id
            room_metadata["post_slug"] = post.slug
        if contact_name:
            room_metadata["contact_name"] = contact_name.strip()
        if contact_number:
            room_metadata["contact_number"] = contact_number
        if request.user.is_authenticated:
            user_data = {
                "user_token": request.user.user_token,
                "full_name": request.user.full_name,
                "id": request.user.id,
            }
        else:
            user_data = {}
            if contact_name:
                user_data["full_name"] = contact_name.strip()
                user_data["user_token"] = f"Guest-{contact_name.strip()}"
            else:
                user_data["full_name"] = "Anonymous"
                user_data["user_token"] = (
                    f"Guest-{get_random_string('guest-', length=10)}"
                )
            user_data["id"] = user_data["user_token"]
        room_metadata["user"] = user_data
        room_metadata["agent_handle"] = agent_handle
        data = generate_room_token_server(
            room_name, agent_name, room_metadata, user_data
        )
        return Response({**data})

    def livekit_delete_room(self, request, *args, **kwargs):
        room_name = kwargs.get("room_name")
        if not room_name:
            return Response({"message": "Invalid data"}, status=206)
        data = delete_room_server(room_name)
        return Response({**data})
