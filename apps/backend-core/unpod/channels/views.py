import logging
import os
import json
import traceback
import uuid
import time
import base64

import jwt
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.text import slugify

from google_auth_oauthlib.flow import Flow
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from unpod.channels.models import (
    App,
    AppConnectorConfig,
    AppConnectRequest,
    AppConfigLink,
)
from datetime import timedelta, datetime
from unpod.channels.utils import AppCredUtility
from unpod.common.enum import SpaceType
from unpod.common.renderers import UnpodJSONRenderer
from unpod.space.models import Space
from unpod.space.utils import checkSpaceAccess
from unpod.users.models import User
from unpod.common.storage_backends import imagekitBackend
from msal import ConfidentialClientApplication
import requests

logger = logging.getLogger(__name__)


class GoogleAppConnector(GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]

    def get_permissions(self):
        if self.action == "google_auth_callback":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_redirect_uri(self, request, app):
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        redirect_url = reverse(f"channels:{app.config['redirection_url']}")
        redirect_url = f"{settings.BASE_URL}{redirect_url}"
        return redirect_url

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def google_auth(self, request, *args, **kwargs):
        try:
            data = request.data
            app_slug = slugify(data.get("name"))
            app = App.objects.get(slug=app_slug)
            config_path = app.config["client_secret"]
            # Path to your client_secrets.json file
            CLIENT_SECRET_FILE = os.path.join(settings.ROOT_DIR, config_path)

            # Get the dynamic redirect URI
            redirect_uri = self.get_redirect_uri(request, app)

            # Set up the flow
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=app.config["scopes"],
                redirect_uri=redirect_uri,
            )

            # Capture the current user ID and route
            user_id = request.user.id
            redirect_route = data.get("redirect_route", None)
            kb = data.get("kb", None)
            space = data.get("space", None)

            if kb:
                knowledge_base = Space.objects.get(
                    slug=kb, space_type=SpaceType.knowledge_base.name
                )
                checkSpaceAccess(request.user, space=knowledge_base, check_role=True)

                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    spaces__id=knowledge_base.id,
                ).exists()

                if already_connected:
                    return Response(
                        {"error": "App Already Connected to this Knowledge Base"},
                        status=status.HTTP_206_PARTIAL_CONTENT,
                    )

            if space:
                gmail_space = Space.objects.get(
                    slug=space, space_type=SpaceType.general.name
                )
                checkSpaceAccess(request.user, space=gmail_space, check_role=True)

                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    spaces__id=gmail_space.id,
                ).exists()

                if already_connected:
                    return Response(
                        {"error": "App Already Connected to this Space"},
                        status=status.HTTP_206_PARTIAL_CONTENT,
                    )

            # Pass data securely using the state parameter
            request_state = AppConnectRequest.objects.create(
                request_id=uuid.uuid1().hex,
                app=app,
                user=request.user,
                config={
                    "user_id": user_id,
                    "redirect_route": redirect_route,
                    "name": app.name,
                    "app_slug": app_slug,
                    "kb": kb,
                    "space": space,
                },
            )

            authorization_url, _ = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                state=json.dumps(request_state.request_id),
                prompt="consent",
            )

            # send a redirect
            return Response(
                {"redirect_url": authorization_url},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("Error during Google Auth: %s", e)
            traceback.print_exc()
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def google_auth_callback(self, request, *args, **kwargs):
        try:
            # Path to your client_secrets.json file
            CLIENT_SECRET_FILE = os.path.join(settings.ROOT_DIR, "client_secrets.json")
            # Retrieve and parse the state parameter
            state = request.GET.get("state")
            code = request.GET.get("code")
            if not state:
                return redirect(f"{settings.BASE_FRONTEND_URL}?error=Invalid Request")

            try:
                state_data = json.loads(state)
                request_state = AppConnectRequest.objects.get(request_id=state_data)
                request_state.status = "completed"
                request_state.save()
                state_data = request_state.config
                user_id = state_data["user_id"]
                redirect_route = state_data["redirect_route"]
                app_slug = state_data["app_slug"]
                kb = state_data.get("kb")
                space = state_data.get("space")
            except (KeyError, json.JSONDecodeError):
                return redirect(
                    f"{settings.BASE_FRONTEND_URL}?error=Invalid Request State"
                )

            app = App.objects.get(slug=app_slug)
            user = User.objects.get(id=int(user_id))
            knowledge_base = None
            if kb:
                knowledge_base = Space.objects.get(
                    slug=kb, space_type=SpaceType.knowledge_base.name
                )
                checkSpaceAccess(user, space=knowledge_base, check_role=True)

                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    spaces__id=knowledge_base.id,
                ).exists()

                if already_connected:
                    return redirect(
                        f"{redirect_route}?error=App Already Connected to this Knowledge Base"
                    )

            gmail_space = None
            if space:
                gmail_space = Space.objects.get(
                    slug=space, space_type=SpaceType.general.name
                )
                checkSpaceAccess(user, space=gmail_space, check_role=True)

                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    spaces__id=gmail_space.id,
                ).exists()

                if already_connected:
                    return redirect(
                        f"{redirect_route}?error=App Already Connected to this Space"
                    )

            if not app or not user:
                # TODO: instead of ?, & can be used to handle FE query params
                return redirect(
                    f"{redirect_route}?error=Invalid Request,Valid State not found"
                )

            # Get the dynamic redirect URI
            redirect_uri = self.get_redirect_uri(request, app)

            # Set up the flow
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                scopes=app.config["scopes"],
                redirect_uri=redirect_uri,
            )
            url = request.build_absolute_uri()
            print("url", url)
            flow.fetch_token(code=code)

            # Get the credentials
            credentials = flow.credentials

            id_token = credentials.id_token
            decoded_id_token = jwt.decode(
                id_token, options={"verify_signature": False, "verify_aud": False}
            )

            email = decoded_id_token.get("email")

            # Save the credentials for the user
            # TODO, Currently each user can individually link same gmail id, maybe keep email config at organization level
            app_config, created = AppConnectorConfig.objects.update_or_create(
                organization=user.organization,
                user=user,
                app=app,
                configuration__email=email,
                defaults={
                    "state": "active",
                    "configuration": {
                        "id_token": credentials.id_token,
                        "email": email,
                        "access_token": credentials.token,
                        "refresh_token": credentials.refresh_token,
                        "token_expiry": credentials.expiry.isoformat(),
                        "token_generated": int(time.time()),
                    },
                },
            )
            # request for testing superstore

            if knowledge_base:
                # Restriction for knowledge bases if a email is connected to any knowledge base across te organization, it can not connect another another kb
                # TODO: if required we can allow multiple users to lik same email in different kB since we have given  ability to connect at user level
                emai_already_linked_kb = AppConfigLink.objects.filter(
                    app_config__state="active",
                    app_config__organization=user.organization,
                    app_config__configuration__email=email,
                    app_config__app=app.id,
                    content_type=ContentType.objects.get_for_model(Space),
                    spaces__space_type=SpaceType.knowledge_base.name,
                ).first()
                if emai_already_linked_kb:
                    print("already linked")
                    if (
                        emai_already_linked_kb.content_object.slug
                        != knowledge_base.slug
                    ):
                        # Connected with some oter KB
                        return redirect(
                            f"{redirect_route}?error=This Account is already Liked to Different Knowledge Base"
                        )
                    print("creds revoked")
                    # else part not needed here it will come only if th creds got revoled and need to refresh creds and its already linked to right KB

                print("linking app")

                app_link, _ = AppConfigLink.objects.get_or_create(
                    app_config=app_config,
                    user=user,
                    content_type=ContentType.objects.get_for_model(Space),
                    object_id=knowledge_base.id,
                    link_config={"frequency": 86400},
                )

                res = requests.post(
                    f"{settings.API_SERVICE_URL}/connector/",
                    json.dumps(
                        {
                            "name": f"{app.name}-{app_link.content_type.model}-{app_link.id}",
                            "source": app.slug,
                            "input_type": "poll",
                            "connector_specific_config": {
                                "organization": user.organization.id,
                                "user": user.id,
                                "app": app.name,
                                "app_link_id": app_link.id,
                                "link_model": app_link.content_type.model,
                                "link_type": "knowledge_base",
                                "kn_token": knowledge_base.token,
                            },
                            "refresh_freq": 86400,
                            "prune_freq": 0,
                            "disabled": False,
                        }
                    ),
                )
                print("Response from store service:", res.content, res.status_code)

            if gmail_space:
                email_already_linked_space = AppConfigLink.objects.filter(
                    app_config__state="active",
                    app_config__hub=user.organization,
                    app_config__configuration__email=email,
                    app_config__app=app.id,
                    content_type=ContentType.objects.get_for_model(Space),
                    spaces__space_type=SpaceType.general.name,
                ).first()
                if email_already_linked_space:
                    if (
                        email_already_linked_space.content_object.slug
                        != gmail_space.slug
                    ):
                        # Connected with some other Space
                        return redirect(
                            f"{redirect_route}?error=This Account is already Liked to Different Space"
                        )

                app_link, _ = AppConfigLink.objects.get_or_create(
                    app_config=app_config,
                    user=user,
                    content_type=ContentType.objects.get_for_model(Space),
                    object_id=gmail_space.id,
                    link_config={"frequency": 86400},
                )

                res = requests.post(
                    f"{settings.API_SERVICE_URL}/connector/",
                    json.dumps(
                        {
                            "name": f"{app.name}-{app_link.content_type.model}-{app_link.id}",
                            "source": app.slug,
                            "input_type": "poll",
                            "connector_specific_config": {
                                "organization": user.organization.id,
                                "user": user.id,
                                "app": app.name,
                                "app_link_id": app_link.id,
                                "link_model": app_link.content_type.model,
                                "link_type": "space",
                                "kn_token": gmail_space.token,
                            },
                            "refresh_freq": 86400,
                            "prune_freq": 0,
                            "disabled": False,
                        }
                    ),
                )

                print("Response from store service:", res.content, res.status_code)

            # Redirect back to the original route
            return redirect(redirect_route)
        except Exception as e:
            logger.error("Error during Google Auth Callback: %s", e)
            traceback.print_exc()
            return redirect(f"{settings.BASE_FRONTEND_URL}?error=Something went wrong")


class OutlookAppConnector(GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == "outlook_auth_callback":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_redirect_uri(self, request, app):
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        redirect_url = reverse(f"channels:{app.config['redirection_url']}")
        redirect_url = f"{settings.BASE_URL}{redirect_url}"
        print("redirect", redirect_url)
        return redirect_url

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def outlook_auth(self, request, *args, **kwargs):
        try:
            data = request.data
            app_slug = slugify(data.get("name"))
            app = App.objects.get(slug=app_slug)
            config_path = app.config["client_secret"]
            # Path to your creds.json file
            CLIENT_SECRET_FILE = os.path.join(settings.ROOT_DIR, config_path)

            # Load credentials from creds.json
            with open(CLIENT_SECRET_FILE, "r") as creds_file:
                creds = json.load(creds_file)

            # Initialize MSAL client
            msal_app = ConfidentialClientApplication(
                client_id=creds["application_client_id"],
                client_credential=creds["secret_value"],
                authority=f"https://login.microsoftonline.com/{creds['tenant_id']}",
            )

            # Get the dynamic redirect URI
            redirect_uri = self.get_redirect_uri(request, app)

            # Generate authorization URL
            authorization_url = msal_app.get_authorization_request_url(
                scopes=["https://graph.microsoft.com/Mail.Read"],
                redirect_uri=redirect_uri,
                state=json.dumps(
                    {
                        "user_id": request.user.id,
                        "redirect_route": data.get("redirect_route", None),
                        "name": app.name,
                        "app_slug": app_slug,
                        "kb": data.get("kb", None),
                    }
                ),
            )

            # send a redirect
            return Response(
                {"redirect_url": authorization_url},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error("Error during Outlook Auth: %s", e)
            traceback.print_exc()
            return Response(
                {"error": "Something went wrong"},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def outlook_auth_callback(self, request, *args, **kwargs):
        try:
            # Path to your creds.json file
            CLIENT_SECRET_FILE = os.path.join(settings.ROOT_DIR, "creds.json")
            # Retrieve and parse the state parameter
            state = request.GET.get("state")
            code = request.GET.get("code")
            if not state:
                return redirect(f"{settings.BASE_FRONTEND_URL}?error=Invalid Request")

            try:
                state_data = json.loads(state)
                user_id = state_data["user_id"]
                redirect_route = state_data["redirect_route"]
                app_slug = state_data["app_slug"]
                kb = state_data.get("kb")
            except (KeyError, json.JSONDecodeError):
                return redirect(
                    f"{settings.BASE_FRONTEND_URL}?error=Invalid Request State"
                )

            app = App.objects.get(slug=app_slug)
            user = User.objects.get(id=int(user_id))

            if not app or not user:
                return redirect(
                    f"{redirect_route}?error=Invalid Request,Valid State not found"
                )

            # Initialize MSAL client
            with open(CLIENT_SECRET_FILE, "r") as creds_file:
                creds = json.load(creds_file)

            msal_app = ConfidentialClientApplication(
                client_id=creds["application_client_id"],
                client_credential=creds["secret_value"],
                authority=f"https://login.microsoftonline.com/{creds['tenant_id']}",
            )

            # Get tokens
            result = msal_app.acquire_token_by_authorization_code(
                code,
                scopes=["https://graph.microsoft.com/Mail.Read"],
                redirect_uri=self.get_redirect_uri(request, app),
            )

            if "access_token" in result:
                access_token = result["access_token"]
                print("Access token acquired:", access_token)
                # Further processing can be done here

            # Redirect back to the original route
            return redirect(redirect_route)
        except Exception as e:
            logger.error("Error during Outlook Auth Callback: %s", e)
            traceback.print_exc()
            return redirect(f"{settings.BASE_FRONTEND_URL}?error=Something went wrong")

class TwitterAuthConnector(GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]

    def get_permissions(self):
        if self.action == "twitter_callback":
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_redirect_uri(self, request, app):
        scheme = "https" if request.is_secure() else "http"
        host = request.get_host()
        redirect_url = reverse(f"channels:{app.config['redirection_url']}")
        redirect_url = f"{settings.BASE_URL}{redirect_url}"
        return redirect_url

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def twitter_auth(self, request, *args, **kwargs):
        try:
            print("Received twitter_auth request")
            data = request.data
            app_slug = slugify(data.get("name"))
            app = App.objects.get(slug=app_slug)

            user_id = request.user.id
            redirect_route = data.get("redirect_route", None)
            kb = data.get("kb", None)
            space = data.get("space", None)

            client_id = app.config["client_id"]
            scopes = app.config["scopes"]
            redirection_url = app.config["redirection_url"]
            reverse_url = reverse(f"channels:{redirection_url}")
            redirect_url = f"{settings.BASE_URL}{reverse_url}"

            # Already connected check
            if kb:
                print("Checking for existing connection to Knowledge Base")
                knowledge_base = Space.objects.get(
                    slug=kb, space_type=SpaceType.knowledge_base.name
                )
                checkSpaceAccess(request.user, space=knowledge_base, check_role=True)
                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    content_type=ContentType.objects.get_for_model(Space),
                    object_id=knowledge_base.id,
                ).exists()
                if already_connected:
                    print("Already connected to this Knowledge Base")
                    return Response(
                        {"error": "App Already Connected to this Knowledge Base"},
                        status=status.HTTP_206_PARTIAL_CONTENT,
                    )

            if space:
                print("Checking for existing connection to Space")
                twitter_space = Space.objects.get(
                    slug=space, space_type=SpaceType.general.name
                )
                checkSpaceAccess(request.user, space=twitter_space, check_role=True)
                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    content_type=ContentType.objects.get_for_model(Space),
                    object_id=twitter_space.id,
                ).exists()
                if already_connected:
                    print("Already connected to this Space")
                    return Response(
                        {"error": "App Already Connected to this Space"},
                        status=status.HTTP_206_PARTIAL_CONTENT,
                    )

            # PKCE
            print("Generating code_verifier and code_challenge")
            import base64, hashlib
            code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
            code_challenge = base64.urlsafe_b64encode(
                hashlib.sha256(code_verifier.encode()).digest()
            ).decode("utf-8").rstrip("=")

            print("Saving request state in DB")
            request_state = AppConnectRequest.objects.create(
                request_id=uuid.uuid1().hex,
                app=app,
                user=request.user,
                config={
                    "user_id": user_id,
                    "redirect_route": redirect_route,
                    "name": app.name,
                    "app_slug": app_slug,
                    "kb": kb,
                    "space": space,
                    "code_verifier": code_verifier,  # ✅ Saved here
                },
            )

            print("Sending Data", redirect_url, scopes, request_state.request_id, code_challenge)

            auth_url = (
                f"https://twitter.com/i/oauth2/authorize"
                f"?response_type=code&client_id={client_id}"
                f"&redirect_uri={redirect_url}"
                f"&scope={scopes.replace(' ', '%20')}"
                f"&state={request_state.request_id}&code_challenge={code_challenge}&code_challenge_method=S256"
            )
            print("Returning Twitter Auth URL:", auth_url)
            return Response({"redirect_url": auth_url}, status=200)
        except Exception as e:
            logger.error("Error during Twitter Auth: %s", e)
            traceback.print_exc()
            return Response({"error": "Something went wrong"}, status=206)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def twitter_callback(self, request, *args, **kwargs):
        try:
            print("Received Twitter callback")
            state = request.GET.get("state")
            code = request.GET.get("code")

            if not state or not code:
                print("Missing state or code")
                return redirect(f"{settings.BASE_FRONTEND_URL}?error=Invalid Request")

            request_state = AppConnectRequest.objects.get(request_id=state)
            request_state.status = "completed"
            request_state.save()
            state_data = request_state.config

            code_verifier = state_data.get("code_verifier")
            print("Retrieved code_verifier:", code_verifier)

            user_id = state_data["user_id"]
            redirect_route = state_data["redirect_route"]
            app_slug = state_data["app_slug"]
            kb = state_data.get("kb")
            space = state_data.get("space")

            if not redirect_route.startswith("http"):
                redirect_route = f"{settings.BASE_FRONTEND_URL}{redirect_route}"

            app = App.objects.get(slug=app_slug)
            user = User.objects.get(id=int(user_id))

            client_id = app.config["client_id"]
            client_secret = app.config["client_secret"]
            redirection_url = app.config["redirection_url"]
            reverse_url = reverse(f"channels:{redirection_url}")
            redirect_url = f"{settings.BASE_URL}{reverse_url}"

            # Exchange code for tokens
            print("Exchanging code for tokens")
            token_url = "https://api.twitter.com/2/oauth2/token"
            data = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "redirect_uri": redirect_url,
                "code_verifier": code_verifier,
                "code": code
            }
            client_creds = f"{client_id}:{client_secret}"

            print("Client credentials:", client_creds)
            print("Request Data", data)
            b64_creds = base64.b64encode(client_creds.encode()).decode()
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {b64_creds}"
            }

            response = requests.post(token_url, data=data, headers=headers)
            print("Token exchange response status:", response.status_code)
            if response.status_code != 200:
                print("Token exchange failed:", response.text)
                return redirect(f"{redirect_route}?error=Token exchange failed")

            tokens = response.json()
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")
            expires_in = tokens.get("expires_in")

            # Fetch user info
            print("Fetching user info from Twitter API")
            user_info = requests.get(
                "https://api.twitter.com/2/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            print("User info status:", user_info.status_code)
            if user_info.status_code != 200:
                return redirect(f"{redirect_route}?error=Failed to fetch user info")
            user_data = user_info.json()
            twitter_user_id = user_data.get("data", {}).get("id")
            twitter_username = user_data.get("data", {}).get("username")

            print("Twitter user ID:", twitter_user_id)
            print("Twitter username:", twitter_username)

            # Validation and linking
            if kb:
                knowledge_base = Space.objects.get(
                    slug=kb, space_type=SpaceType.knowledge_base.name
                )
                checkSpaceAccess(user, space=knowledge_base, check_role=True)
                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    app_config__configuration__twitter_user_id=twitter_user_id,
                    content_type=ContentType.objects.get_for_model(Space),
                    spaces__space_type=SpaceType.knowledge_base.name,
                ).first()
                if already_connected and already_connected.content_object.slug != knowledge_base.slug:
                    return redirect(
                        f"{redirect_route}?error=This Twitter account is already linked to a different Knowledge Base"
                    )

            if space:
                twitter_space = Space.objects.get(
                    slug=space, space_type=SpaceType.general.name
                )
                checkSpaceAccess(user, space=twitter_space, check_role=True)
                already_connected = AppConfigLink.objects.filter(
                    app_config__app=app.id,
                    app_config__state="active",
                    app_config__configuration__twitter_user_id=twitter_user_id,
                    content_type=ContentType.objects.get_for_model(Space),
                    spaces__space_type=SpaceType.general.name,
                ).first()
                if already_connected and already_connected.content_object.slug != twitter_space.slug:
                    return redirect(
                        f"{redirect_route}?error=This Twitter account is already linked to a different Space"
                    )

            print("Saving AppConnectorConfig")
            app_config, created = AppConnectorConfig.objects.update_or_create(
                organization=user.organization,
                user=user,
                app=app,
                configuration__twitter_user_id=twitter_user_id,
                defaults={
                    "state": "active",
                    "configuration": {
                        "twitter_user_id": twitter_user_id,
                        "twitter_username": twitter_username,
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_expiry": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
                        "token_generated": int(time.time()),
                    },
                },
            )

            if kb:
                AppConfigLink.objects.get_or_create(
                    app_config=app_config,
                    user=user,
                    content_type=ContentType.objects.get_for_model(Space),
                    object_id=knowledge_base.id,
                    link_config={"frequency": 86400},
                )

            if space:
                AppConfigLink.objects.get_or_create(
                    app_config=app_config,
                    user=user,
                    content_type=ContentType.objects.get_for_model(Space),
                    object_id=twitter_space.id,
                    link_config={"frequency": 86400},
                )

            print("Redirecting to:", redirect_route)
            return redirect(redirect_route)
        except Exception as e:
            logger.error("Error during Twitter Auth Callback: %s", e)
            traceback.print_exc()
            return redirect(f"{settings.BASE_FRONTEND_URL}?error=Something went wrong")




class AppsView(GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]
    permission_classes = [IsAuthenticated]

    def list_apps(self, request, *args, **kwargs):
        """
        API endpoint to list all active apps.
        """
        try:
            apps = App.objects.filter(is_active=True)
            connected_app_names = set(
                AppConnectorConfig.objects.filter(
                    organization=request.user.organization
                ).values_list("app__name", flat=True)
            )

            app_data = []
            for app in apps:
                app_data.append(
                    {
                        "name": app.name,
                        "description": app.description,
                        "logo": (
                            imagekitBackend.generateURL(app.icon.name)
                            if app.icon
                            else None
                        ),
                        "status": "active" if app.is_active else "inactive",
                        "url": (
                            reverse(
                                f"channels:{app.config.get('initiate_url')}"
                            ).replace("/api/v1", "")
                            if app.config.get("initiate_url")
                            else None
                        ),
                        "slug": app.slug,
                        "is_connected": app.name in connected_app_names,
                    }
                )

            return Response(
                {"data": app_data, "message": "App List fetched successfully"},
                status=200,
            )

        except Exception as e:
            logger.exception("Error listing apps: %s", e)
            return Response({"message": "Internal server error"}, status=206)


class AppConfigLinkView(GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]

    def get_permissions(self):
        if self.action == "retrieve":
            return [AllowAny()]
        return [IsAuthenticated()]

    # make a route to send back detail of particular app link
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def retrieve(self, request, *args, **kwargs):
        """
        API endpoint to retrieve details of a specific app link.
        """
        try:
            app_link_id = kwargs.get("app_link_id")
            app_link = AppConfigLink.objects.get(id=app_link_id)
            return Response(
                {
                    "data": {
                        "link_config": app_link.link_config,
                        "app": app_link.app_config.app.name,
                        "link_model": app_link.content_type.model,
                        "configuration": {
                            **app_link.app_config.configuration,
                            **AppCredUtility.get_client_credentials(
                                app_link.app_config.app
                            ),
                        },
                        "config_state": app_link.app_config.state,
                    },
                    "message": "App Link fetched successfully",
                },
                status=status.HTTP_200_OK,
            )
        except AppConfigLink.DoesNotExist:
            return Response(
                {"message": "App Link not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error retrieving app link: %s", e)
            return Response(
                {"message": "Internal server error"},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def update_link_config(self, request, *args, **kwargs):
        try:
            app_config_link_id = kwargs.get("app_link_id")
            frequency = request.data.get("frequency")
            enabled = request.data.get("enabled")

            if frequency is None or enabled is None:
                return Response(
                    {"error": "Missing Required Parameters"},
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )

            if not isinstance(frequency, int) or frequency <= 0:
                return Response(
                    {
                        "error": "Invalid frequency value. It must be a positive integer."
                    },
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )

            # check appConfigLink exists
            try:
                app_config_link = AppConfigLink.objects.get(id=app_config_link_id)
            except AppConfigLink.DoesNotExist:
                return Response({"error": "Config not Found"}, status=404)

            user = request.user
            if user.id != app_config_link.user.id:
                return Response(
                    {"error": "Not authorized to perform this action."},
                    status=status.HTTP_206_PARTIAL_CONTENT,
                )

            app_config_link.link_config = request.data
            app_config_link.save()

            link_type = ""
            if app_config_link.content_type.model == "space":
                if (
                    app_config_link.content_object.space_type
                    == SpaceType.knowledge_base.value
                ):
                    link_type = "knowledge_base"
                else:
                    link_type = "space"

            res = requests.post(
                f"{settings.API_SERVICE_URL}/connector/",
                json.dumps(
                    {
                        "name": f"{app_config_link.app_config.app.name}-{app_config_link.content_type.model}-{app_config_link.id}",
                        "source": app_config_link.app_config.app.slug,
                        "input_type": "poll",
                        "connector_specific_config": {
                            "organization": user.organization.id,
                            "user": user.id,
                            "app": app_config_link.app_config.app.name,
                            "app_link_id": app_config_link.id,
                            "link_model": app_config_link.content_type.model,
                            "link_type": link_type,
                            "link_config": app_config_link.link_config,
                        },
                        "refresh_freq": frequency,
                        "prune_freq": 0,
                        "disabled": not enabled,
                    }
                ),
            )

            print("Response from store service:", res.content, res.status_code)

            return Response(
                {
                    "message": "Config  Updated Successfully",
                    "link_config": app_config_link.link_config,
                }
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"error": "An error occurred.", "details": str(e)},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
