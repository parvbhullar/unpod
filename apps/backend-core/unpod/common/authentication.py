from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

# Import our custom JWT handlers
from unpod.common.jwt import jwt_decode_handler

# Import SimpleJWT for Django 4.2+ compatibility
try:
    from rest_framework_simplejwt.authentication import JWTAuthentication as SimpleJWTAuthentication
    SIMPLE_JWT_AVAILABLE = True
except ImportError:
    SIMPLE_JWT_AVAILABLE = False


class StaticAPITokenAuthentication(BaseAuthentication):

    keyword = "Api-Key"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            msg = _("Authorization header required.")
            raise exceptions.AuthenticationFailed(msg)

        if smart_str(auth[0].lower()) != self.keyword.lower():
            msg = _("Invalid Authorization header. Use 'Api-Key <token>' format.")
            raise exceptions.AuthenticationFailed(msg)

        if len(auth) == 1:
            msg = _("Invalid Authorization header. No API key provided.")
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _("Invalid Authorization header. API key should not contain spaces.")
            raise exceptions.AuthenticationFailed(msg)

        token = smart_str(auth[1])
        return self.authenticate_token(token)

    def authenticate_token(self, token):
        """
        Validate the static API token against the configured token in settings.
        """
        expected_token = getattr(settings, "SECRET_API_TOKEN", None)

        if not expected_token:
            msg = _("API token not configured on server.")
            raise exceptions.AuthenticationFailed(msg)

        if token != expected_token:
            msg = _("Invalid API token.")
            raise exceptions.AuthenticationFailed(msg)

        return (None, token)

    def authenticate_header(self, request):
        return self.keyword


class DualJWTAuthentication(BaseAuthentication):
    """
    JWT authentication backend using our custom PyJWT handlers (Django 4.2+ compatible).

    Supports both "JWT" and "Bearer" authorization headers for backward compatibility:
    - Authorization: JWT <token>
    - Authorization: Bearer <token>

    Uses our custom jwt_decode_handler to validate tokens created by jwt_encode_handler.
    """

    def authenticate(self, request):
        """
        Authenticate the request using our custom JWT tokens.

        Returns:
            tuple: (user, token) if authentication successful
            None: if authentication fails or no token provided
        """
        # Get the authorization header
        auth_header = get_authorization_header(request).split()

        # Handle cookie-based auth if no header
        if not auth_header:
            # Check for cookie-based JWT (if configured)
            jwt_cookie = getattr(settings, "SIMPLE_JWT", {}).get("AUTH_COOKIE")
            if jwt_cookie and jwt_cookie in request.COOKIES:
                token = request.COOKIES.get(jwt_cookie)
                if token:
                    try:
                        return self._authenticate_token(token)
                    except Exception:
                        return None
            return None

        # Check if it's "JWT" or "Bearer" prefix (both supported for compatibility)
        auth_prefix = smart_str(auth_header[0].lower())
        if auth_prefix not in ['jwt', 'bearer']:
            return None

        if len(auth_header) == 1:
            msg = _("Invalid Authorization header. No credentials provided.")
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            msg = _("Invalid Authorization header. Credentials string should not contain spaces.")
            raise exceptions.AuthenticationFailed(msg)

        # Extract and validate the token
        token = smart_str(auth_header[1])
        try:
            return self._authenticate_token(token)
        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            raise exceptions.AuthenticationFailed(_("Invalid or expired token."))

    def _authenticate_token(self, token):
        """
        Validate the token and return the associated user.

        Args:
            token: JWT token string

        Returns:
            tuple: (user, token)

        Raises:
            AuthenticationFailed: If token is invalid or user not found
        """
        try:
            # Decode the token using our custom handler
            payload = jwt_decode_handler(token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(_("Invalid or expired token."))

        # Extract user_id from payload
        user_id = payload.get('user_id')
        if not user_id:
            raise exceptions.AuthenticationFailed(_("Token contained no recognizable user identification."))

        # Get the user
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("User not found."))

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_("User account is disabled."))

        return (user, token)

    def authenticate_header(self, request):
        """
        Return string to be used as WWW-Authenticate header in 401 responses.
        Support both JWT and Bearer for backward compatibility.
        """
        return 'JWT realm="api"'


# Legacy class names for backward compatibility
UnpodJSONWebTokenAuthentication = DualJWTAuthentication
BaseJSONWebTokenAuthentication = DualJWTAuthentication
