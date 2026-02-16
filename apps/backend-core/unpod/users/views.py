import math

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialConnectView
from django.contrib.auth import get_user_model
from django.http.request import HttpRequest

# from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

# Import simplejwt for token migration
try:
    from rest_framework_simplejwt.tokens import RefreshToken
    SIMPLE_JWT_AVAILABLE = True
except ImportError:
    SIMPLE_JWT_AVAILABLE = False


# Base class to replace ObtainJSONWebToken from old djangorestframework-jwt
class ObtainJSONWebToken(APIView):
    """
    API view to obtain JWT token (Django 4.2+ compatible).
    Replaces old djangorestframework-jwt view.
    """
    permission_classes = (AllowAny,)
    serializer_class = None  # Set in subclass

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from unpod.common.otp import (
    verify_number,
    verify_otp_format,
    send_forgot_password_email,
    send_verify_email_otp,
)
from unpod.common.redis import (
    delete_key,
    get_otp,
    get_status,
    redis_delete,
    redis_get,
    redis_key,
    redis_set,
)
from unpod.common.mixin import QueryOptimizationMixin
from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.serializer import CommonSerializer
from unpod.common.string import generate_color_hex
from unpod.common.validation import Validation, validate_email
from unpod.space.models import SpaceInvite
from unpod.thread.services import checkCreatePostPermission
from unpod.users.models import BlackListToken, UserBasicDetail, UserDevice
from unpod.users.serializers import (
    JWTSerializer,
    SignUpSerializer,
    UserSerializer,
    UserUpdateSerializer,
    UserDeviceInfoSerializer,
    UserDeviceSerializer,
    AuthTokenSerializer,
)
from unpod.users.utils import (
    check_user,
    checkInvited,
    checkUserOragaization,
    otp_generation,
    processInvitedUser,
    send_resend_otp,
)
from unpod.common.jwt import jwt_decode_handler, jwt_encode_handler, jwt_payload_handler

User = get_user_model()


class ObtainJWTView(ObtainJSONWebToken):
    serializer_class = JWTSerializer
    schema = None  # Exclude from OpenAPI schema (incompatible with drf-spectacular)


class AuthView(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]
    schema = None  # Exclude from OpenAPI schema (incompatible with drf-spectacular)

    def auth_me(self, request: HttpRequest):
        user = request.user
        data = UserSerializer(user).data
        return Response(data, status=200)


class LogoutView(viewsets.GenericViewSet):
    renderer_classes = [UnpodJSONRenderer]
    schema = None  # Exclude from OpenAPI schema (incompatible with drf-spectacular)

    def get(self, request):
        token = request.headers.get("Authorization")
        if token:
            BlackListToken.objects.create(user_id=request.user.id, token=token)
        return Response(
            {"message": "Successfully logged out"}, status=status.HTTP_200_OK
        )


# fmt: off
class OTPView(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]
    schema = None  # Exclude from OpenAPI schema (incompatible with drf-spectacular)

    def generate_otp(self, request: HttpRequest):
        ser = SignUpSerializer(data=request.data)
        if not ser.is_valid():
            return Response({"message": "Please Provide Valid Data", "errors": ser.errors}, status=206)
        request_data = ser.validated_data
        email = request_data.pop("email")
        password = request_data.pop("password")
        if email and password:
            if not validate_email(email):
                return Response({"message": "Please Provide a Valid Email"}, status=206)
            try:
                invite_type = checkInvited(email)
                if invite_type:
                    data = processInvitedUser(email, password, request_data, invite_type)
                    return Response(data)
                message, error = otp_generation(email, password, request_data)
                if not error:
                    return Response({"success": message}, status=200)
                return Response({"message": message}, status=206)
            except Exception as e:
                print(str(e), "Exception in otp_generation")
                return Response({"message": "something wrong"}, status=206)
        return Response({"message": "Email and password Required"}, status=206)

    def change_register_email(self, request: HttpRequest):
        payload = request.data
        old_email = payload.get("old_email")
        email = payload.get("email")

        if email and old_email:
            try:
                if not validate_email(email):
                    return Response({"message": "Please Provide a Valid Email"}, status=206)

                user = User.objects.filter(email=old_email, is_active=False).first()

                if not user:
                    return Response(
                        {"message": "Old Email is not valid or User already verified"},
                        status=206
                    )

                user.email = email
                user.save()

                delete_key(old_email, str(user.id), prefix='signup')
                otp_check, time_left, otp = get_status(
                    email, str(user.id), prefix="signup"
                )

                if otp_check:
                    send_verify_email_otp(email, otp)

                    return Response(
                        {
                            "success": "Email changed successfully, OTP sent to new email address"
                        },
                        status=200,
                    )

                else:
                    time_left = math.ceil(time_left / 60)
                    time_message_str = f"{time_left} mins" if time_left > 1 else f"{time_left} min"

                    return Response(
                        {
                            "message": f"You Already Requested For OTP, Please Try After {time_message_str}"
                        },
                        status=206,
                    )
            except Exception as e:
                print(str(e), "Exception in change_register_email")
                return Response({"message": "something wrong"}, status=206)
        return Response({"message": "Old Email and New Email Required"}, status=206)

    def resend_otp(self, request: HttpRequest):
        email = request.data.get("email")
        if email:
            try:
                if not validate_email(email):
                    return Response({"message": "Please Provide a Valid Email"}, status=206)
                message, error = send_resend_otp(email)
                if not error:
                    return Response({"success": message}, status=200)
                return Response({"message": message}, status=206)
            except Exception as e:
                print(str(e), "Exception in otp_generation")
                return Response({"message": "something wrong"}, status=206)
        return Response({"message": "Email Required"}, status=206)

    def verify_otp(self, request):
        error_message = None
        success_message = None
        token = None
        data = request.data.copy()
        verify = None
        otp = data.get('otp')
        email = data.get('email')
        invite_data = []
        extra_data = {}
        if not otp:
            return Response({"message": "OTP can not be empty"}, status=206)

        print(email, otp, 'verify_otp_request')
        number = None
        if email or number:
            is_email = True if email else False
            is_number = True if number else False

            mode, username = ("Email", email)

            # otp = data.get('otp')
            if is_number:
                verify = verify_number(username)
            otp_verify = verify_otp_format(otp)

            user = check_user(email, None, False)
            if not user:
                return Response({"message": "Invalid Email Verification OTP / User Not Exists"}, status=206)

            if is_number and not verify:
                error_message = "Invalid Number"

            elif not otp_verify:
                error_message = "Email Verification OTP is not valid"
            else:
                otp_from_redis = get_otp(username, str(user.id), prefix='signup')
                if otp_from_redis:
                    if otp_from_redis == otp:
                        success_message = "Email verification successful"
                        delete_key(username, str(user.id), prefix='signup')

                        user.is_active = True
                        payload = jwt_payload_handler(user)
                        token = jwt_encode_handler(payload)
                        if is_number:
                            user.verify_mob = True
                        elif is_email:
                            user.verify_email = True
                        user.save()
                        domain, org = checkUserOragaization(user)
                        extra_data.update({
                            "domain": domain,
                            "organization": org
                        })
                        invite_list = SpaceInvite.objects.filter(
                            user_email=user.email, invite_verified=True).select_related('space')
                        for inv in invite_list:
                            invite_data.append(
                                {
                                    "user_email": inv.user_email,
                                    "invite_token": inv.invite_token,
                                    "name": inv.space.name
                                }
                            )
                    else:
                        error_message = "Invalid OTP, please try again"
                else:
                    error_message = "OTP not found or already used, please request for new OTP"
        else:
            error_message = "Phone Number or Email can not be empty"

        if error_message:
            return Response({
                "message": error_message
            }, status=status.HTTP_206_PARTIAL_CONTENT)

        if success_message:
            return Response({
                "success": success_message,
                "token": token,
                "verification_done": True if token else False,
                "invitation_list": invite_data,
                **extra_data
            }, status=status.HTTP_200_OK)


class PasswordResetView(viewsets.GenericViewSet):
    permission_classes = []
    authentication_classes = []
    serializer_class = CommonSerializer
    renderer_classes = [UnpodJSONRenderer]

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        if email:
            user = check_user(email, None, False)
            if user:
                if not user.verify_email:
                    return Response({"message": "User Email is not verified"}, status=status.HTTP_206_PARTIAL_CONTENT)
                if not user.is_active:
                    return Response({"message": "User account is not active."}, status=status.HTTP_206_PARTIAL_CONTENT)
                otp_check, time_left, otp = get_status(user.username, str(
                    user.id), prefix='reset-password', ttl=1800, resend=True)
                if not otp_check:
                    time_left = math.ceil(time_left / 60)
                    time_message_str = f"{time_left} mins" if time_left > 1 else f"{time_left} min"
                    return Response(
                        {"message": f"You Already Requested For Reset Password, Please Try After {time_message_str}"},
                        status=206)

                token_payload = {"user_token": user.user_token, "token": otp}
                token = jwt_encode_handler(token_payload)

                send_forgot_password_email(
                    email,
                    token,
                    user_name=user.full_name  # optional
                )

                return Response(
                    {
                        "message": "Password reset link has been sent to your email address"
                    }, status=status.HTTP_200_OK
                )
        return Response({"message": "No user found."}, status=status.HTTP_206_PARTIAL_CONTENT)

    def verify_password(self, request, *args, **kwargs):
        token = request.data.get('token')
        try:
            token_payload = jwt_decode_handler(token)
            token = token_payload.get('token')
            user_token = token_payload.get("user_token")

            if user_token and token:
                user = User.objects.filter(user_token=user_token).first()
                if not user:
                    return Response({"message": "Invalid Token"}, status=status.HTTP_206_PARTIAL_CONTENT)

                otp = get_otp(user.username, str(user.id), prefix='reset-password')
                if otp and otp == token:
                    delete_key(user.username, str(user.id), prefix='reset-password')
                    verify_key = redis_key(user.username, str(user.id), prefix='verify-reset-password')
                    redis_set(verify_key, {"verify": True}, 600)

                    return Response(
                        {
                            "message": "Password reset token verified successfully, proceed to reset your password",
                            "user_token": user_token,
                            'status': True
                        },
                        status=status.HTTP_200_OK
                    )

                return Response(
                    {"message": "There something issue in extracting token"},
                    status=status.HTTP_206_PARTIAL_CONTENT
                )

            return Response({"message": "Invalid token format"}, status=status.HTTP_206_PARTIAL_CONTENT)
        except Exception as e:
            print(e)
            return Response(
                {"message": f"There is an error: {str(e)}"},
                status=status.HTTP_206_PARTIAL_CONTENT
            )

    def confirm(self, request, *args, **kwargs):
        data = request.data.copy()
        user_token = data.get('user_token')
        try:
            if user_token and "password" in data:
                user = User.objects.filter(user_token=user_token).first()
                if not user:
                    return Response({"message": "Invalid User Id"}, status=status.HTTP_206_PARTIAL_CONTENT)
                verify_key = redis_key(user.username, str(user.id), prefix='verify-reset-password')
                verify_case = redis_get(verify_key)
                if not verify_case:
                    return Response({"message": "Invalid User Token or Password Reset Session Expired"},
                                    status=status.HTTP_206_PARTIAL_CONTENT)
                user.set_password(data['password'])
                user.save()
                redis_delete(verify_key)
                return Response({"message": "Your Password has been Reset Successfully"}, status=status.HTTP_200_OK)

            return Response({"message": "User Token and Password are required"}, status=status.HTTP_206_PARTIAL_CONTENT)
        except Exception as e:
            print(e)
            return Response(
                {"message": f"There is an error: {str(e)}"},
                status=status.HTTP_206_PARTIAL_CONTENT
            )


class UserProfileUpdateViewSet(QueryOptimizationMixin, viewsets.GenericViewSet):
    """
    Phase 2.2: Refactored to use QueryOptimizationMixin for query optimization.
    """
    serializer_class = CommonSerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [UnpodJSONRenderer]

    def changePassword(self, request, *args, **kwargs):
        input_data = request.data
        user = request.user
        required_fields = ['old_password', 'new_password', 'repeat_password']
        validate = Validation(required_fields, input_data)
        if not validate.check_required_fields():
            return Response(validate.get_error(), status=206)
        validate.setData()
        input_data = validate.get_data()
        if not user.check_password(input_data["old_password"]):
            return Response({"message": "Wrong old password"}, status=status.HTTP_206_PARTIAL_CONTENT)

        if input_data["new_password"] == input_data.get("old_password"):
            return Response({"message": "Old password and new password can not be same."},
                            status=status.HTTP_206_PARTIAL_CONTENT)

        if input_data["new_password"] != input_data.get("repeat_password"):
            return Response({"message": "Both Password should be same."}, status=status.HTTP_206_PARTIAL_CONTENT)

        user.set_password(input_data.get("new_password"))
        user.change_password = True
        user.save()
        token = request.headers.get("Authorization")
        if token:
            BlackListToken.objects.create(user_id=request.user.id, token=token)
        return Response({"success": "Password successfully changed, please login with new password"},
                        status=status.HTTP_200_OK)

    def updateProfile(self, request, *args, **kwargs):
        input_data = request.data
        user = request.user
        ser = UserUpdateSerializer(data=input_data)
        if ser.is_valid():
            user_data = {}
            validated_data = ser.validated_data
            for key in ['last_name', 'first_name']:
                if key in validated_data and validated_data.get(key):
                    user_data[key] = validated_data.pop(key)
            User.objects.filter(id=user.id).update(**user_data)
            if len(validated_data):
                obj, created = UserBasicDetail.objects.get_or_create(user=user)
                file = validated_data.pop('profile_picture', None)
                if not created:
                    if obj.profile_color is None:
                        validated_data['profile_color'] = generate_color_hex()
                    UserBasicDetail.objects.filter(user=user).update(**validated_data)
                else:
                    for key, val in validated_data.items():
                        setattr(obj, key, val)
                    obj.save()
                if file:
                    obj.profile_picture = file
                    obj.save()
            user.refresh_from_db()
            data = UserSerializer(user).data
            return Response({"data": data, "success": "Profile Updated Successfully"}, status=status.HTTP_200_OK)
        return Response(ser.error_messages, status=status.HTTP_206_PARTIAL_CONTENT)

    def completeSignUp(self, request, *args, **kwargs):
        input_data = request.data
        user = request.user
        required_fields = ['name', 'role_name']
        validate = Validation(required_fields, input_data, {'description': '', 'profile_color': ''})
        if not validate.check_required_fields():
            return Response({"errors": validate.get_error(), "message": "Required Parameter Missing"}, status=206)
        user_obj, created = UserBasicDetail.objects.get_or_create(user=user)
        if not created:
            data = UserSerializer(user).data
            return Response({"data": data, "message": "You Already Completed the SignUp"}, status=200)
        validate.setData()
        input_data = validate.get_data()
        name = input_data.pop('name')
        user_obj = user_obj.updateModel(input_data)
        user = user.update_name(name)
        data = UserSerializer(user).data
        checkCreatePostPermission(user)
        return Response({"data": data, "message": "Your Details has been Updated"}, status=status.HTTP_200_OK)


# fmt: on
class GoogleView(SocialConnectView):
    permission_classes = []
    authentication_classes = []
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(data=self.request.data)
        self.serializer.is_valid(raise_exception=True)
        response = self.login()
        if response.status_code != 200:
            return response
        return response

    def login(self):
        from django.contrib.auth import user_logged_in

        self.user = self.serializer.validated_data["user"]
        payload = jwt_payload_handler(self.user)
        user_logged_in.send(
            sender=self.user.__class__, request=self.request, user=self.user
        )
        return Response({"token": jwt_encode_handler(payload)})


class RegisterDeviceViewSet(viewsets.GenericViewSet):
    queryset = UserDevice.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserDeviceInfoSerializer
    renderer_classes = [UnpodJSONRenderer]

    def get_device_info(self, request, device_id):
        user = request.user
        device = UserDevice.objects.filter(user=user, device_id=device_id).first()

        if not device:
            return Response(
                {"message": "Device not found"}, status=status.HTTP_206_PARTIAL_CONTENT
            )

        serializer = self.get_serializer(device)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def register_device(self, request, *args, **kwargs):
        try:
            input_data = request.data
            device_id = input_data.get("device_id")
            user = request.user
            serializer = UserDeviceSerializer(data=input_data, partial=True)
            if not serializer.is_valid():
                return Response(
                    {
                        "message": "Please Provide Valid Data",
                        "errors": serializer.errors,
                    },
                    status=206,
                )

            existing_device = UserDevice.objects.filter(
                user=user, device_id=device_id
            ).first()
            if existing_device:
                return Response(
                    {"message": "Device already registered"}, status=status.HTTP_200_OK
                )

            device = serializer.save(user=user)

            serializer = self.get_serializer(device)
            return Response(
                {"message": "Device registered successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            print(str(e), "Exception in register_device")
            return Response(
                {"message": f"There is an error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserAuthTokenView(viewsets.GenericViewSet):
    """
    API endpoint to create/obtain DRF Auth Token.
    Allows authenticated users to generate or retrieve their token.
    1. POST request to create a new token if it doesn't exist.
    2. GET request to fetch the existing token.
    3. Returns the token and a message indicating whether it was created or retrieved.
    """

    queryset = Token.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = AuthTokenSerializer
    renderer_classes = [UnpodJSONRenderer]

    def create(self, request):
        user = request.user

        # Get or create token
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Token generated successfully"
                if created
                else "Token retrieved successfully",
                "data": {
                    "token": token.key,
                    "created": created,
                },
            },
            status=status.HTTP_200_OK,
        )

    def list(self, request):
        try:
            user = request.user

            # Get or create token for the authenticated user
            queryset = self.get_queryset().filter(user=user)
            print(queryset, "user tokens", user.id)
            serializer = self.get_serializer(queryset, many=True)

            return Response(
                {
                    "message": "Tokens fetched successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": f"There is an error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def delete(self, request, token):
        try:
            user = request.user

            if not token:
                return Response(
                    {"message": "Token key is required for deletion."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Delete the specified token for the authenticated user
            deleted, _ = self.get_queryset().filter(user=user, key=token).delete()

            if deleted == 0:
                return Response(
                    {"message": "Token not found or already deleted."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {"message": "Token deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"message": f"There is an error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MigrateTokenView(APIView):
    """
    Token migration endpoint for Django 4.2 JWT migration.

    Exchanges old djangorestframework-jwt tokens for new simplejwt tokens.

    Usage:
        POST /api/v1/auth/migrate-token/
        Headers: Authorization: JWT <old_token>

    Returns:
        {
            "access": "new_access_token",
            "refresh": "new_refresh_token",
            "message": "Token migrated successfully"
        }

    Note: This endpoint uses old JWT authentication to verify the user,
    then generates new simplejwt tokens for them.
    """
    # Use old JWT authentication to verify the request
    from unpod.common.authentication import UnpodJSONWebTokenAuthentication
    authentication_classes = [UnpodJSONWebTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Generate new simplejwt tokens for authenticated user.
        """
        if not SIMPLE_JWT_AVAILABLE:
            return Response(
                {
                    "error": "Simple JWT not available",
                    "message": "Token migration is not available. Please install djangorestframework-simplejwt."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        try:
            user = request.user

            # Generate new simplejwt tokens
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'message': 'Token migrated successfully',
                    'user_id': user.id,
                    'username': user.username,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "error": "Token migration failed",
                    "message": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
