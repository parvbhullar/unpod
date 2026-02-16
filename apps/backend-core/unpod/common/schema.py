"""Custom schema preprocessing hooks for drf-spectacular."""
from drf_spectacular.openapi import AutoSchema
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


def filter_v2_platform_endpoints(endpoints):
    """Filter endpoints to include only those under /api/v2/platform/.

    This ensures that only API V2 Platform endpoints are included in the OpenAPI schema.
    Excludes the schema documentation endpoints themselves to avoid circular references.
    Also filters out views that don't have compatible schema classes.

    Args:
        endpoints: List of endpoint tuples (path, path_regex, method, callback)

    Returns:
        Filtered list of endpoints
    """
    # Schema documentation paths to exclude
    excluded_paths = [
        "/api/v2/platform/schema/",
        "/api/v2/platform/docs/",
        "/api/v2/platform/redoc/",
    ]

    filtered_endpoints = []

    for path, path_regex, method, callback in endpoints:
        # Only include endpoints that start with /api/v2/platform/
        # but exclude the schema documentation endpoints themselves
        if path.startswith("/api/v2/platform/") and path not in excluded_paths:
            # Check if the view has a schema attribute and if it's None, skip it
            view = callback.cls if hasattr(callback, "cls") else callback

            # Skip views that explicitly set schema = None
            if hasattr(view, "schema") and view.schema is None:
                continue

            # Only include views that either don't have a schema attribute
            # or have a compatible AutoSchema
            if (
                not hasattr(view, "schema")
                or isinstance(getattr(view, "schema", None), type(None))
                or isinstance(getattr(view, "schema", None), AutoSchema)
            ):
                filtered_endpoints.append((path, path_regex, method, callback))

    return filtered_endpoints
