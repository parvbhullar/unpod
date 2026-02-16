"""Custom schema preprocessing hooks for drf-spectacular."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class UnpodJWTAuthenticationExtension(OpenApiAuthenticationExtension):
    """OpenAPI extension for UnpodJSONWebTokenAuthentication."""

    target_class = "unpod.common.authentication.UnpodJSONWebTokenAuthentication"
    name = "jwtAuth"  # This name should match the security scheme name in SPECTACULAR_SETTINGS

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "JWT Authorization header. Example: 'jwt <token>'",
        }
