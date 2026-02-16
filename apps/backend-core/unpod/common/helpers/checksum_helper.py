"""
Checksum Helper for HMAC-SHA256 validation
Provides data integrity validation for API requests and responses

Frontend formula: HMAC-SHA256(METHOD + URL + DATA + TIMESTAMP + SECRET, SECRET)
"""
import hmac
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Optional, Tuple


# API prefixes to strip from URL to match frontend's relative URLs
API_PREFIXES = [
    "/api/v2/platform/",
    "/api/v2/platform",
    "/api/v1/",
    "/api/v1",
]


def get_relative_url(path: str) -> str:
    """
    Convert Django request.path to frontend's relative URL format.
    Frontend uses axios with baseURL, so config.url is relative without the API prefix.

    Examples:
        /api/v1/auth/login/ -> auth/login/
        /api/v1/agents -> agents
        /api/v2/platform/spaces/ -> spaces/
    """
    url = path

    # Strip API prefix
    for prefix in API_PREFIXES:
        if url.startswith(prefix):
            url = url[len(prefix):]
            break

    # Remove leading slash (frontend doesn't have it in config.url)
    if url.startswith("/"):
        url = url[1:]

    return url


def generate_checksum(method: str, url: str, data: Any, timestamp: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 checksum matching frontend's CryptoHelper.

    Frontend formula: HMAC-SHA256(METHOD + URL + DATA + TIMESTAMP + SECRET, SECRET)

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        url: Request URL/path (relative, without API prefix)
        data: The data to hash (dict, list, str, or any JSON-serializable object)
        timestamp: ISO format timestamp string
        secret: Shared secret key

    Returns:
        Hex string of the HMAC-SHA256 hash
    """
    try:
        # Normalize method to uppercase
        normalized_method = (method or "").upper()

        # Serialize data - must match frontend's JSON.stringify (no sorting!)
        if data is None or data == "":
            serialized_data = ""
        elif isinstance(data, str):
            serialized_data = data
        elif isinstance(data, bytes):
            serialized_data = data.decode("utf-8")
        elif isinstance(data, (dict, list)):
            # IMPORTANT: sort_keys=False to match JavaScript's JSON.stringify
            # ensure_ascii=False to output UTF-8 chars like JavaScript (not \u escapes)
            serialized_data = json.dumps(data, separators=(",", ":"), sort_keys=False, ensure_ascii=False)
        else:
            serialized_data = json.dumps(data, separators=(",", ":"), ensure_ascii=False)

        # Frontend formula: METHOD + URL + DATA + TIMESTAMP + SECRET
        message = normalized_method + url + serialized_data + timestamp + secret

        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"CHECKSUM_CALC method={normalized_method} url={url} data_len={len(serialized_data) if serialized_data else 0}")
        # Log first 200 bytes as hex for exact comparison
        if serialized_data:
            hex_preview = serialized_data[:200].encode('utf-8').hex()
            logger.warning(f"CHECKSUM_DATA_HEX (first 200 chars): {hex_preview}")

        # Generate HMAC-SHA256 with secret as key
        hmac_obj = hmac.new(
            secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        )

        return hmac_obj.hexdigest()
    except Exception as e:
        raise ValueError(f"Error generating checksum: {str(e)}")


def validate_checksum(
    method: str, url: str, data: Any, timestamp: str, received_checksum: str, secret: str
) -> bool:
    """
    Validate HMAC-SHA256 checksum

    Args:
        method: HTTP method
        url: Request URL/path (relative)
        data: The data to validate
        timestamp: ISO format timestamp string
        received_checksum: The checksum to validate against
        secret: Shared secret key

    Returns:
        True if checksum is valid, False otherwise
    """
    try:
        if not received_checksum or not timestamp or not secret:
            return False

        # Generate expected checksum
        expected_checksum = generate_checksum(method, url, data, timestamp, secret)

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_checksum, received_checksum)
    except Exception:
        return False


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format

    Returns:
        ISO format timestamp string
    """
    return datetime.utcnow().isoformat(timespec='milliseconds') + "Z"


def is_timestamp_valid(timestamp: str, max_age_seconds: int = 300) -> bool:
    """
    Validate timestamp freshness to prevent replay attacks

    Args:
        timestamp: ISO format timestamp string
        max_age_seconds: Maximum age in seconds (default: 300 = 5 minutes)

    Returns:
        True if timestamp is fresh, False otherwise
    """
    try:
        # Parse timestamp (handle both with and without 'Z' suffix)
        timestamp_clean = timestamp.rstrip("Z")

        # Try parsing with microseconds/milliseconds
        try:
            timestamp_dt = datetime.fromisoformat(timestamp_clean)
        except ValueError:
            # Try parsing without fractional seconds
            timestamp_dt = datetime.strptime(timestamp_clean, "%Y-%m-%dT%H:%M:%S")

        # Get current time
        current_dt = datetime.utcnow()

        # Calculate time difference
        time_diff = abs((current_dt - timestamp_dt).total_seconds())

        # Check if within acceptable range
        return time_diff <= max_age_seconds
    except Exception:
        return False


def should_skip_checksum(request_path: str, request_method: str, content_type: str = "") -> bool:
    """
    Determine if checksum validation should be skipped for this request

    Args:
        request_path: The request path/URL
        request_method: HTTP method (GET, POST, etc.)
        content_type: Request content type (optional)

    Returns:
        True if checksum should be skipped, False otherwise
    """
    # Skip admin endpoints
    if request_path.startswith("/api/v2/") or request_path.startswith("/api/v2/platform/docs/") or request_path.startswith("/api/v2/platform/schema/") or request_path.startswith("/api/v2/platform/redoc/"):
        return True

    if request_path.startswith("/admin/"):
        return True

    # Skip unpod-admin endpoints
    if request_path.startswith("/unpod-admin/") or "/unpod-admin/" in request_path:
        return True

    # Skip static files
    if request_path.startswith("/static/") or request_path.startswith("/media/"):
        return True

    # Skip health check endpoints
    if request_path in ["/health/", "/health", "/api/health/"]:
        return True

    # Skip public media endpoints
    if "/media/download-signed-url" in request_path:
        return True

    # Skip generate_room_token endpoints (voice/video room tokens)
    if "/generate_room_token/" in request_path:
        return True

    # Skip register-as-user admin action (admin panel button, no checksum from browser)
    if "/register-as-user/" in request_path:
        return True

    # Skip multipart/form-data requests (POST/PUT/PATCH)
    # Django's MultiPartParser doesn't preserve field order, causing checksum mismatch
    # between frontend (sorts fields alphabetically) and backend (receives in HTTP order)
    # Additionally, line ending normalization (LF vs CRLF) in text fields causes mismatches
    if request_method.upper() in ("POST", "PUT", "PATCH") and "multipart/form-data" in content_type:
        return True

    return False


def extract_request_data(request) -> Tuple[Optional[str], str]:
    """
    Extract and serialize request data for checksum validation.
    Must match frontend's serialization exactly.

    Args:
        request: Django request object

    Returns:
        Tuple of (serialized_data, data_type) where data_type is 'params', 'body', 'formdata', or 'none'
    """
    try:
        content_type = request.content_type or ""
        method = request.method.upper()

        # For GET requests, frontend serializes query params sorted alphabetically
        if method == "GET":
            query_params = request.GET.dict()
            if query_params:
                # Convert values to appropriate types and sort alphabetically
                converted_params = {}
                for key, value in query_params.items():
                    converted_params[key] = _convert_value(value)
                sorted_params = _sort_dict_recursively(converted_params)
                return json.dumps(sorted_params, separators=(",", ":"), ensure_ascii=False), "params"
            return "", "none"

        # For multipart/form-data (file uploads)
        if "multipart/form-data" in content_type:
            formdata_obj = {}

            # For PUT/PATCH requests, Django doesn't automatically populate request.POST
            # We need to manually parse the multipart data
            post_data = request.POST
            files_data = request.FILES

            if method in ("PUT", "PATCH") and not post_data:
                # Manually parse multipart data for PUT/PATCH
                from django.http.multipartparser import MultiPartParser
                from io import BytesIO

                # Use request.body which contains the raw request data
                body = request.body
                if body:
                    parser = MultiPartParser(request.META, BytesIO(body), request.upload_handlers)
                    post_data, files_data = parser.parse()

            # Add POST text fields, handling bracket notation for arrays and objects
            # e.g., knowledge_bases[0], knowledge_bases[1] -> knowledge_bases: [...]
            # e.g., address[street], address[city] -> address: {street: ..., city: ...}
            array_bracket_pattern = re.compile(r'^(.+)\[(\d+)\]$')  # field[0], field[1]
            object_bracket_pattern = re.compile(r'^(.+)\[([^\]]+)\]$')  # field[key]

            for key, value in post_data.items():
                array_match = array_bracket_pattern.match(key)
                if array_match:
                    # This is an array field like knowledge_bases[0]
                    base_key = array_match.group(1)
                    index = int(array_match.group(2))
                    if base_key not in formdata_obj:
                        formdata_obj[base_key] = []
                    # Ensure list is large enough
                    while len(formdata_obj[base_key]) <= index:
                        formdata_obj[base_key].append(None)
                    formdata_obj[base_key][index] = _parse_formdata_value(value)
                else:
                    object_match = object_bracket_pattern.match(key)
                    if object_match:
                        # This is an object field like address[street]
                        base_key = object_match.group(1)
                        nested_key = object_match.group(2)
                        if base_key not in formdata_obj:
                            formdata_obj[base_key] = {}
                        # Only treat as object if it's not already an array
                        if isinstance(formdata_obj[base_key], dict):
                            formdata_obj[base_key][nested_key] = _parse_formdata_value(value)
                    else:
                        # Parse JSON-like string values to match frontend behavior
                        # e.g., "[]" -> [], "true" -> true, "123" -> 123
                        formdata_obj[key] = _parse_formdata_value(value)

            # Clean up any None values from sparse arrays
            for key, value in list(formdata_obj.items()):
                if isinstance(value, list):
                    formdata_obj[key] = [v for v in value if v is not None]

            # Add file metadata (matches frontend's extraction)
            for key, file in files_data.items():
                formdata_obj[key] = {
                    "name": file.name or "unknown",
                    "size": file.size or 0,
                    "type": file.content_type or "unknown",
                }

            if formdata_obj:
                # Sort keys alphabetically (recursively) to match frontend serialization
                sorted_obj = _sort_dict_recursively(formdata_obj)
                return json.dumps(sorted_obj, separators=(",", ":"), ensure_ascii=False), "formdata"
            return "", "none"

        # For POST/PUT/PATCH with JSON body
        if request.body:
            body_str = request.body.decode("utf-8")
            # Frontend sorts keys alphabetically before calculating checksum
            # We need to do the same to match
            try:
                body_obj = json.loads(body_str)
                sorted_obj = _sort_dict_recursively(body_obj)
                return json.dumps(sorted_obj, separators=(",", ":"), ensure_ascii=False), "body"
            except (json.JSONDecodeError, ValueError):
                # If not valid JSON, use raw body
                return body_str, "body"

        return "", "none"
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"extract_request_data error: {type(e).__name__}: {e}")
        return "", "none"


def _convert_value(value: str) -> Any:
    """
    Convert string value to appropriate type (matches frontend behavior).
    Query params come as strings but frontend's config.params may have numbers.
    """
    if value == "":
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _sort_dict_recursively(obj: Any) -> Any:
    """
    Recursively sort dictionary keys alphabetically.
    Handles nested dicts and lists containing dicts.
    """
    if isinstance(obj, dict):
        return {k: _sort_dict_recursively(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [_sort_dict_recursively(item) for item in obj]
    return obj


def _normalize_line_endings(value: str) -> str:
    """
    Normalize line endings to CRLF to match frontend behavior.

    Browsers and JavaScript may use different line endings:
    - Windows/HTTP: CRLF (\r\n)
    - Unix/macOS: LF (\n)
    - Old macOS: CR (\r)

    Frontend FormData typically uses CRLF when serializing for checksum.
    We normalize to CRLF to match frontend's serialization.
    """
    if not isinstance(value, str):
        return value

    # First, normalize all line endings to LF, then convert to CRLF
    # This handles mixed line endings (CRLF, LF, CR)
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", "\r\n")


def _parse_formdata_value(value: str) -> Any:
    """
    Parse FormData string values to match frontend behavior.
    Frontend parses JSON-like strings: "[]" -> [], "{}" -> {}, "true" -> true, etc.
    Also normalizes line endings to CRLF to match frontend serialization.
    """
    if not isinstance(value, str):
        return value

    # Normalize line endings to CRLF to match frontend
    value = _normalize_line_endings(value)

    # Try to parse as JSON (for arrays and objects like "[]", "{}", etc.)
    stripped = value.strip()
    if stripped.startswith(("[", "{")):
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

    # Boolean conversion
    if stripped.lower() == "true":
        return True
    if stripped.lower() == "false":
        return False

    # Number conversion (only for purely numeric strings)
    try:
        if "." in stripped:
            return float(stripped)
        return int(stripped)
    except ValueError:
        pass

    return value
