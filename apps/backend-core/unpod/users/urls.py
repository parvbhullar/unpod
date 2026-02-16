from django.urls import path

from unpod.users.views import (
    AuthView,
    OTPView,
    ObtainJWTView,
    PasswordResetView,
    UserProfileUpdateViewSet,
    GoogleView,
    LogoutView,
    RegisterDeviceViewSet,
    UserAuthTokenView,
    MigrateTokenView,  # Django 4.2 JWT migration endpoint
)

app_name = "users"
urlpatterns = [
    path("auth/login/", ObtainJWTView.as_view(), name="allow-all"),
    path("auth/migrate-token/", MigrateTokenView.as_view(), name="migrate-token"),  # JWT migration
    path("auth/logout/", LogoutView.as_view({"get": "get"}), name="allow-all"),
    path("auth/me/", AuthView.as_view({"get": "auth_me"}), name="auth-me"),
    path(
        "auth/register/", OTPView.as_view({"post": "generate_otp"}), name="generate-otp"
    ),
    path(
        "auth/register/change-email/",
        OTPView.as_view({"post": "change_register_email"}),
        name="change_register_email",
    ),
    path(
        "auth/register/resend-otp/",
        OTPView.as_view({"post": "resend_otp"}),
        name="resend-otp",
    ),
    path(
        "auth/register/verify-otp/",
        OTPView.as_view({"post": "verify_otp"}),
        name="verify-otp-request",
    ),
    path(
        "password/forgot/",
        PasswordResetView.as_view({"post": "create"}),
        name="reset-password",
    ),
    path(
        "password/reset/verify/",
        PasswordResetView.as_view({"post": "verify_password"}),
        name="reset-password",
    ),
    path(
        "password/reset/confirm/",
        PasswordResetView.as_view({"post": "confirm"}),
        name="reset-password",
    ),
    path(
        "change-password/",
        UserProfileUpdateViewSet.as_view({"post": "changePassword"}),
        name="change-password",
    ),
    path(
        "user-profile/",
        UserProfileUpdateViewSet.as_view({"put": "updateProfile"}),
        name="user-profile",
    ),
    path(
        "complete-signup/",
        UserProfileUpdateViewSet.as_view({"post": "completeSignUp"}),
        name="complete-signup",
    ),
    path(
        f"user/device-info/<str:device_id>/",
        RegisterDeviceViewSet.as_view({"get": "get_device_info"}),
        name="get_device_info",
    ),
    path(
        "user/register-device/",
        RegisterDeviceViewSet.as_view({"post": "register_device"}),
        name="register-device",
    ),
    path("google/login/", GoogleView.as_view(), name="google-login"),
    # User Token Authentication endpoints
    path(
        "user/auth-tokens/",
        UserAuthTokenView.as_view({"get": "list", "post": "create"}),
        name="user_token",
    ),
    path(
        "user/auth-tokens/<str:token>/",
        UserAuthTokenView.as_view({"delete": "delete"}),
        name="delete_user_token",
    ),
]
