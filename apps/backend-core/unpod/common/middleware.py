import threading
import logging
from django.conf import settings
from django.http import JsonResponse

from unpod.common.helpers.checksum_helper import (
    generate_checksum,
    validate_checksum,
    get_current_timestamp,
    is_timestamp_valid,
    should_skip_checksum,
    extract_request_data,
    get_relative_url,
)

_thread_locals = threading.local()

logger = logging.getLogger(__name__)


def get_current_request():
    return getattr(_thread_locals, "request", None)


class CheckHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        return self.get_response(request)


class ChecksumValidationMiddleware:
    """
    Middleware for HMAC-SHA256 checksum validation.
    Validates incoming request checksums and adds checksums to outgoing responses.

    NOTE: Only applies to BROWSER requests. Mobile apps are skipped.

    Frontend formula: HMAC-SHA256(METHOD + URL + DATA + TIMESTAMP + SECRET, SECRET)
    """

    # Known mobile app User-Agent patterns
    MOBILE_APP_PATTERNS = [
        "okhttp",           # Android HTTP client
        "Alamofire",        # iOS HTTP client
        "CFNetwork",        # iOS native
        "Unpod/",           # Custom mobile app identifier
        "UnpodApp/",        # Custom mobile app identifier
        "Darwin/",          # iOS/macOS native (without browser)
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, "ENABLE_CHECKSUM", False)
        self.secret = getattr(settings, "CHECKSUM_SECRET", "")
        self.max_timestamp_age = getattr(
            settings, "CHECKSUM_MAX_TIMESTAMP_AGE", 300
        )  # 5 minutes
        # If True, only validate browser requests (skip mobile apps)
        # If False, validate ALL requests (browser + mobile)
        self.browser_only = getattr(settings, "CHECKSUM_BROWSER_ONLY", True)
        # If True, requests WITHOUT checksum headers will be REJECTED
        # If False, requests without checksums are allowed (graceful degradation)
        self.required = getattr(settings, "CHECKSUM_REQUIRED", False)

        if self.enabled and not self.secret:
            logger.warning(
                "ENABLE_CHECKSUM is True but CHECKSUM_SECRET is not set. Checksum validation disabled."
            )
            self.enabled = False

        if self.enabled:
            mode = "browser requests only" if self.browser_only else "all requests"
            enforcement = "REQUIRED" if self.required else "optional"
            logger.info(f"Checksum validation middleware enabled ({mode}, {enforcement})")

    def _is_browser_request(self, request):
        """
        Detect if request is from a web browser (not mobile app).

        Browser indicators:
        - Origin header present (CORS)
        - Referer header with http/https
        - User-Agent contains browser identifiers

        Mobile app indicators:
        - No Origin header
        - User-Agent contains mobile SDK patterns (okhttp, Alamofire, etc.)
        """
        origin = request.headers.get("Origin", "")
        referer = request.headers.get("Referer", "")
        user_agent = request.headers.get("User-Agent", "")

        # Check for mobile app User-Agent patterns
        user_agent_lower = user_agent.lower()
        for pattern in self.MOBILE_APP_PATTERNS:
            if pattern.lower() in user_agent_lower:
                return False  # Mobile app detected

        # Browser indicators: Origin or Referer with http(s)
        if origin and (origin.startswith("http://") or origin.startswith("https://")):
            return True

        if referer and (referer.startswith("http://") or referer.startswith("https://")):
            return True

        # Check for common browser User-Agent patterns
        browser_patterns = ["mozilla", "chrome", "safari", "firefox", "edge", "opera"]
        for pattern in browser_patterns:
            if pattern in user_agent_lower:
                return True

        # Default: assume not a browser (skip checksum)
        return False

    def __call__(self, request):
        # Skip checksum validation if disabled
        if not self.enabled:
            return self.get_response(request)

        # Skip checksum for certain paths/methods/content types
        content_type = request.content_type or ""
        if should_skip_checksum(request.path, request.method, content_type):
            return self.get_response(request)

        # Skip checksum for mobile apps if browser_only mode is enabled
        if self.browser_only and not self._is_browser_request(request):
            return self.get_response(request)

        # Validate incoming request checksum
        validation_error = self._validate_request_checksum(request)
        if validation_error:
            return validation_error

        # Process the request
        response = self.get_response(request)

        # Add checksum to response (only for browser requests)
        self._add_response_checksum(response, request)

        return response

    def _validate_request_checksum(self, request):
        """
        Validate checksum for incoming requests.

        Returns:
            JsonResponse with error if validation fails, None if valid
        """
        try:
            # Extract headers
            received_checksum = request.headers.get("UP-Checksum")
            received_timestamp = request.headers.get("UP-Timestamp")

            # If no checksum provided
            if not received_checksum or not received_timestamp:
                if self.required:
                    # Reject requests without checksum when required
                    logger.warning(
                        f"Missing checksum headers for {request.method} {request.path}"
                    )
                    return JsonResponse(
                        {
                            "message": "Checksum headers required (UP-Checksum and UP-Timestamp)",
                            "error": "CHECKSUM_REQUIRED",
                        },
                        status=400,
                    )
                # Allow graceful degradation when not required
                return None

            # Validate timestamp freshness (prevent replay attacks)
            if not is_timestamp_valid(received_timestamp, self.max_timestamp_age):
                logger.warning(
                    f"Invalid or expired timestamp for request to {request.path}"
                )
                return JsonResponse(
                    {
                        "message": "Request timestamp is invalid or expired",
                        "error": "TIMESTAMP_VALIDATION_FAILED",
                    },
                    status=400,
                )

            # Get method and relative URL (matching frontend's format)
            method = request.method.upper()
            # Use path without query string - frontend's axios config.url doesn't include params
            url = get_relative_url(request.path)

            # Extract and serialize request data
            serialized_data, data_type = extract_request_data(request)

            # Validate checksum
            is_valid = validate_checksum(
                method, url, serialized_data, received_timestamp, received_checksum, self.secret
            )

            if not is_valid:
                # Debug logging - full data for diagnosis
                expected = generate_checksum(method, url, serialized_data, received_timestamp, self.secret)
                logger.warning(
                    f"Checksum validation failed for {method} {request.path}"
                )
                logger.warning(f"CHECKSUM_DEBUG url={url}")
                logger.warning(f"CHECKSUM_DEBUG data={serialized_data}")
                logger.warning(f"CHECKSUM_DEBUG timestamp={received_timestamp}")
                logger.warning(f"CHECKSUM_DEBUG received={received_checksum}")
                logger.warning(f"CHECKSUM_DEBUG expected={expected}")
                return JsonResponse(
                    {
                        "message": "Request checksum validation failed",
                        "error": "CHECKSUM_VALIDATION_FAILED",
                    },
                    status=400,
                )

            return None

        except Exception as e:
            logger.error(f"Error validating request checksum: {str(e)}")
            # Allow request to proceed on error (graceful degradation)
            return None

    def _add_response_checksum(self, response, request):
        """
        Add checksum to outgoing responses.
        """
        try:
            # Skip for non-JSON responses
            content_type = response.get("Content-Type", "")
            if "application/json" not in content_type:
                return

            # Skip for error responses
            if response.status_code >= 400:
                return

            # Get response content
            if hasattr(response, "content") and response.content:
                response_data = response.content.decode("utf-8")
            else:
                return

            # Get method and relative URL (matching frontend's format)
            method = request.method.upper()
            # Use path without query string - frontend's axios config.url doesn't include params
            url = get_relative_url(request.path)

            # Generate timestamp and checksum
            timestamp = get_current_timestamp()
            checksum = generate_checksum(method, url, response_data, timestamp, self.secret)

            # Add headers
            response["UP-Checksum"] = checksum
            response["UP-Timestamp"] = timestamp

        except Exception as e:
            logger.error(f"Error adding response checksum: {str(e)}")
