"""
Tests for checksum_helper module
Tests HMAC-SHA256 checksum generation, validation, and timestamp validation
"""
from datetime import datetime, timedelta
from unpod.common.helpers.checksum_helper import (
    generate_checksum,
    validate_checksum,
    get_current_timestamp,
    is_timestamp_valid,
    should_skip_checksum,
    extract_request_body,
)


class TestChecksumGeneration:
    """Test checksum generation with different data types"""

    def test_generate_checksum_with_dict(self):
        """Test checksum generation with dictionary data"""
        data = {"name": "test", "value": 123}
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum = generate_checksum(data, timestamp, secret)

        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # HMAC-SHA256 produces 64 hex characters

    def test_generate_checksum_with_string(self):
        """Test checksum generation with string data"""
        data = "test string data"
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum = generate_checksum(data, timestamp, secret)

        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64

    def test_generate_checksum_with_list(self):
        """Test checksum generation with list data"""
        data = ["item1", "item2", "item3"]
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum = generate_checksum(data, timestamp, secret)

        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64

    def test_generate_checksum_consistency(self):
        """Test that same input produces same checksum"""
        data = {"test": "data"}
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum1 = generate_checksum(data, timestamp, secret)
        checksum2 = generate_checksum(data, timestamp, secret)

        assert checksum1 == checksum2

    def test_generate_checksum_different_secrets(self):
        """Test that different secrets produce different checksums"""
        data = {"test": "data"}
        timestamp = "2026-01-21T10:00:00Z"

        checksum1 = generate_checksum(data, timestamp, "secret1")
        checksum2 = generate_checksum(data, timestamp, "secret2")

        assert checksum1 != checksum2


class TestChecksumValidation:
    """Test checksum validation"""

    def test_validate_checksum_valid(self):
        """Test validation with correct checksum"""
        data = {"test": "data"}
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum = generate_checksum(data, timestamp, secret)
        is_valid = validate_checksum(data, timestamp, checksum, secret)

        assert is_valid is True

    def test_validate_checksum_invalid(self):
        """Test validation with incorrect checksum"""
        data = {"test": "data"}
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum = "invalid-checksum-value"
        is_valid = validate_checksum(data, timestamp, checksum, secret)

        assert is_valid is False

    def test_validate_checksum_wrong_secret(self):
        """Test validation with wrong secret"""
        data = {"test": "data"}
        timestamp = "2026-01-21T10:00:00Z"

        checksum = generate_checksum(data, timestamp, "secret1")
        is_valid = validate_checksum(data, timestamp, checksum, "secret2")

        assert is_valid is False

    def test_validate_checksum_tampered_data(self):
        """Test validation with tampered data"""
        original_data = {"test": "data"}
        tampered_data = {"test": "modified"}
        timestamp = "2026-01-21T10:00:00Z"
        secret = "test-secret-key"

        checksum = generate_checksum(original_data, timestamp, secret)
        is_valid = validate_checksum(tampered_data, timestamp, checksum, secret)

        assert is_valid is False

    def test_validate_checksum_empty_values(self):
        """Test validation with empty checksum/timestamp"""
        data = {"test": "data"}
        secret = "test-secret-key"

        assert validate_checksum(data, "", "checksum", secret) is False
        assert validate_checksum(data, "timestamp", "", secret) is False
        assert validate_checksum(data, "timestamp", "checksum", "") is False


class TestTimestampValidation:
    """Test timestamp validation for replay attack prevention"""

    def test_get_current_timestamp_format(self):
        """Test that current timestamp is in correct ISO format"""
        timestamp = get_current_timestamp()

        assert timestamp is not None
        assert isinstance(timestamp, str)
        assert timestamp.endswith("Z")
        # Verify it can be parsed
        datetime.fromisoformat(timestamp.rstrip("Z"))

    def test_is_timestamp_valid_current(self):
        """Test that current timestamp is valid"""
        timestamp = get_current_timestamp()
        is_valid = is_timestamp_valid(timestamp, max_age_seconds=300)

        assert is_valid is True

    def test_is_timestamp_valid_old(self):
        """Test that old timestamp is invalid"""
        # Create timestamp from 10 minutes ago
        old_time = datetime.utcnow() - timedelta(minutes=10)
        timestamp = old_time.isoformat() + "Z"

        is_valid = is_timestamp_valid(timestamp, max_age_seconds=300)

        assert is_valid is False

    def test_is_timestamp_valid_future(self):
        """Test that future timestamp within window is valid"""
        # Create timestamp 1 minute in the future
        future_time = datetime.utcnow() + timedelta(minutes=1)
        timestamp = future_time.isoformat() + "Z"

        is_valid = is_timestamp_valid(timestamp, max_age_seconds=300)

        # Should be valid since we use abs() for time difference
        assert is_valid is True

    def test_is_timestamp_valid_invalid_format(self):
        """Test that invalid timestamp format returns False"""
        timestamp = "invalid-timestamp"

        is_valid = is_timestamp_valid(timestamp, max_age_seconds=300)

        assert is_valid is False

    def test_is_timestamp_valid_without_z_suffix(self):
        """Test timestamp validation without Z suffix"""
        # Create timestamp without Z
        timestamp = datetime.utcnow().isoformat()

        is_valid = is_timestamp_valid(timestamp, max_age_seconds=300)

        assert is_valid is True


class TestShouldSkipChecksum:
    """Test checksum skip logic for specific paths"""

    def test_should_skip_get_requests(self):
        """Test that GET requests are skipped"""
        assert should_skip_checksum("/api/v1/users/", "GET") is True

    def test_should_not_skip_post_requests(self):
        """Test that POST requests are not skipped"""
        assert should_skip_checksum("/api/v1/users/", "POST") is False

    def test_should_skip_file_upload_paths(self):
        """Test that file upload paths are skipped"""
        assert should_skip_checksum("/api/v1/media/upload/", "POST") is True
        assert should_skip_checksum("/api/v1/documents/create/", "POST") is True

    def test_should_skip_admin_paths(self):
        """Test that admin paths are skipped"""
        assert should_skip_checksum("/admin/users/", "POST") is True
        assert should_skip_checksum("/admin/", "GET") is True

    def test_should_skip_static_paths(self):
        """Test that static/media paths are skipped"""
        assert should_skip_checksum("/static/css/style.css", "GET") is True
        assert should_skip_checksum("/media/images/photo.jpg", "GET") is True

    def test_should_not_skip_api_paths(self):
        """Test that regular API paths are not skipped"""
        assert should_skip_checksum("/api/v1/threads/", "POST") is False


class TestExtractRequestBody:
    """Test request body extraction"""

    def test_extract_request_body_json(self):
        """Test extracting JSON request body"""
        # This would need a mock Django request object
        # For now, just test that the function exists and handles None
        body, is_json = extract_request_body(None)

        assert body is None
        assert is_json is False


class TestEndToEndChecksum:
    """End-to-end checksum validation tests"""

    def test_full_checksum_flow(self):
        """Test complete checksum generation and validation flow"""
        # Simulate request data
        request_data = {
            "user": "test_user",
            "action": "create_post",
            "content": "Test content",
        }
        secret = "shared-secret-key-between-frontend-and-backend"

        # 1. Generate timestamp
        timestamp = get_current_timestamp()

        # 2. Generate checksum (frontend would do this)
        checksum = generate_checksum(request_data, timestamp, secret)

        # 3. Validate checksum (backend would do this)
        is_valid = validate_checksum(request_data, timestamp, checksum, secret)

        assert is_valid is True

    def test_replay_attack_prevention(self):
        """Test that old requests are rejected"""
        request_data = {"test": "data"}
        secret = "test-secret"

        # Create old timestamp (10 minutes ago)
        old_time = datetime.utcnow() - timedelta(minutes=10)
        old_timestamp = old_time.isoformat() + "Z"

        # Generate checksum with old timestamp
        checksum = generate_checksum(request_data, old_timestamp, secret)

        # Checksum is valid...
        assert validate_checksum(request_data, old_timestamp, checksum, secret) is True

        # ...but timestamp is expired
        assert is_timestamp_valid(old_timestamp, max_age_seconds=300) is False

    def test_man_in_the_middle_detection(self):
        """Test that tampered data is detected"""
        original_data = {"amount": 100, "recipient": "user1"}
        secret = "test-secret"
        timestamp = get_current_timestamp()

        # Generate checksum for original data
        checksum = generate_checksum(original_data, timestamp, secret)

        # Attacker modifies the data
        tampered_data = {"amount": 1000, "recipient": "attacker"}

        # Validation should fail
        is_valid = validate_checksum(tampered_data, timestamp, checksum, secret)

        assert is_valid is False
