"""
Unit tests for Kafka store service.

Tests the KAFKA_BASE class methods for producing and consuming Kafka messages.

Run tests:
    pytest unpod/common/tests/test_kafka_store.py -v
"""
import json
import sys
import pytest
from unittest.mock import patch, MagicMock


class TestKafkaBaseSerialization:
    """Tests for serialization/deserialization methods."""

    @pytest.fixture(autouse=True)
    def setup_kafka_base(self):
        """Setup KAFKA_BASE with mocked settings."""
        # Create mock settings
        mock_settings = MagicMock()
        mock_settings.KAFKA_BROKER = "localhost:9092"
        mock_settings.KAFKA_VERSION_TIMEOUT = 5000
        mock_settings.KAFKA_REQUEST_TIMEOUT = 10000

        # Patch settings before import
        with patch.dict('sys.modules', {'django.conf': MagicMock(settings=mock_settings)}):
            with patch('unpod.common.services.kafka_store.settings', mock_settings):
                from unpod.common.services.kafka_store import KAFKA_BASE
                self.KAFKA_BASE = KAFKA_BASE
                self.mock_settings = mock_settings
                yield

    def test_serialize_data_dict(self):
        """Test serializing a dictionary."""
        data = {"key": "value", "number": 42}
        result = self.KAFKA_BASE.serialize_data(data)

        assert isinstance(result, bytes)
        assert json.loads(result.decode("utf-8")) == data

    def test_serialize_data_list(self):
        """Test serializing a list."""
        data = [1, 2, 3, "four"]
        result = self.KAFKA_BASE.serialize_data(data)

        assert isinstance(result, bytes)
        assert json.loads(result.decode("utf-8")) == data

    def test_serialize_data_nested(self):
        """Test serializing nested data."""
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ],
            "count": 2
        }
        result = self.KAFKA_BASE.serialize_data(data)

        assert isinstance(result, bytes)
        assert json.loads(result.decode("utf-8")) == data

    def test_serialize_data_unicode(self):
        """Test serializing unicode characters."""
        data = {"message": "Hello, 世界! 🎉"}
        result = self.KAFKA_BASE.serialize_data(data)

        assert isinstance(result, bytes)
        assert json.loads(result.decode("utf-8")) == data

    def test_deserialize_data(self):
        """Test deserializing bytes to dict."""
        original = {"key": "value", "number": 42}
        serialized = json.dumps(original).encode("utf-8")

        result = self.KAFKA_BASE.deserialize_data(serialized)

        assert result == original

    def test_deserialize_data_list(self):
        """Test deserializing bytes to list."""
        original = [1, 2, 3]
        serialized = json.dumps(original).encode("utf-8")

        result = self.KAFKA_BASE.deserialize_data(serialized)

        assert result == original

    def test_serialize_deserialize_roundtrip(self):
        """Test roundtrip serialization and deserialization."""
        original = {
            "event": "user_created",
            "payload": {
                "user_id": 123,
                "email": "test@example.com"
            },
            "timestamp": "2026-01-29T10:00:00Z"
        }

        serialized = self.KAFKA_BASE.serialize_data(original)
        deserialized = self.KAFKA_BASE.deserialize_data(serialized)

        assert deserialized == original


class TestKafkaBaseProducer:
    """Tests for Kafka producer methods."""

    @pytest.fixture(autouse=True)
    def setup_kafka_base(self):
        """Setup KAFKA_BASE with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.KAFKA_BROKER = "localhost:9092"
        mock_settings.KAFKA_VERSION_TIMEOUT = 5000
        mock_settings.KAFKA_REQUEST_TIMEOUT = 10000

        # Remove kafka_pub attribute if exists
        if hasattr(mock_settings, 'kafka_pub'):
            delattr(mock_settings, 'kafka_pub')

        with patch('unpod.common.services.kafka_store.settings', mock_settings):
            from unpod.common.services.kafka_store import KAFKA_BASE
            self.KAFKA_BASE = KAFKA_BASE
            self.mock_settings = mock_settings
            yield

    def test_get_producer_creates_new_producer(self):
        """Test that get_producer creates a new KafkaProducer when none exists."""
        kafka_base = self.KAFKA_BASE()

        with patch('unpod.common.services.kafka_store.KafkaProducer') as MockProducer:
            mock_producer = MagicMock()
            MockProducer.return_value = mock_producer

            # Ensure no existing kafka_pub
            if hasattr(self.mock_settings, 'kafka_pub'):
                delattr(self.mock_settings, 'kafka_pub')

            producer = kafka_base.get_producer()

            MockProducer.assert_called_once()
            assert producer == mock_producer

    def test_get_producer_reuses_existing_producer(self):
        """Test that get_producer reuses existing open producer."""
        kafka_base = self.KAFKA_BASE()

        with patch('unpod.common.services.kafka_store.KafkaProducer') as MockProducer:
            mock_producer = MagicMock()
            mock_producer._closed = False

            self.mock_settings.kafka_pub = mock_producer

            producer = kafka_base.get_producer()

            # Should not create a new producer
            MockProducer.assert_not_called()
            assert producer == mock_producer

    def test_get_producer_creates_new_when_closed(self):
        """Test that get_producer creates new producer when existing is closed."""
        kafka_base = self.KAFKA_BASE()

        with patch('unpod.common.services.kafka_store.KafkaProducer') as MockProducer:
            # Existing closed producer
            closed_producer = MagicMock()
            closed_producer._closed = True
            self.mock_settings.kafka_pub = closed_producer

            # New producer
            new_producer = MagicMock()
            MockProducer.return_value = new_producer

            producer = kafka_base.get_producer()

            MockProducer.assert_called_once()
            assert producer == new_producer


class TestKafkaBaseConsumer:
    """Tests for Kafka consumer methods."""

    @pytest.fixture(autouse=True)
    def setup_kafka_base(self):
        """Setup KAFKA_BASE with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.KAFKA_BROKER = "localhost:9092"
        mock_settings.KAFKA_VERSION_TIMEOUT = 5000
        mock_settings.KAFKA_REQUEST_TIMEOUT = 10000

        with patch('unpod.common.services.kafka_store.settings', mock_settings):
            from unpod.common.services.kafka_store import KAFKA_BASE
            self.KAFKA_BASE = KAFKA_BASE
            self.mock_settings = mock_settings
            yield

    def test_get_consumer_creates_consumer(self):
        """Test that get_consumer creates a KafkaConsumer with correct params."""
        kafka_base = self.KAFKA_BASE()

        with patch('unpod.common.services.kafka_store.KafkaConsumer') as MockConsumer:
            mock_consumer = MagicMock()
            MockConsumer.return_value = mock_consumer

            consumer = kafka_base.get_consumer(
                topic_name="test-topic",
                group_id="test-group"
            )

            # Verify consumer was created
            MockConsumer.assert_called_once()
            call_args = MockConsumer.call_args

            # Check positional args
            assert call_args[0][0] == "test-topic"

            # Check keyword args
            assert call_args[1]['bootstrap_servers'] == "localhost:9092"
            assert call_args[1]['group_id'] == "test-group"
            assert call_args[1]['consumer_timeout_ms'] == 10000

            assert consumer == mock_consumer

    def test_get_consumer_with_custom_timeout(self):
        """Test get_consumer with custom consumer timeout."""
        kafka_base = self.KAFKA_BASE()

        with patch('unpod.common.services.kafka_store.KafkaConsumer') as MockConsumer:
            mock_consumer = MagicMock()
            MockConsumer.return_value = mock_consumer

            consumer = kafka_base.get_consumer(
                topic_name="test-topic",
                group_id="test-group",
                consumer_timeout=5000
            )

            call_kwargs = MockConsumer.call_args[1]
            assert call_kwargs['consumer_timeout_ms'] == 5000

    def test_get_consumer_with_extra_kwargs(self):
        """Test get_consumer passes extra kwargs to KafkaConsumer."""
        kafka_base = self.KAFKA_BASE()

        with patch('unpod.common.services.kafka_store.KafkaConsumer') as MockConsumer:
            mock_consumer = MagicMock()
            MockConsumer.return_value = mock_consumer

            consumer = kafka_base.get_consumer(
                topic_name="test-topic",
                group_id="test-group",
                auto_offset_reset='earliest',
                enable_auto_commit=False
            )

            call_kwargs = MockConsumer.call_args[1]
            assert call_kwargs['auto_offset_reset'] == 'earliest'
            assert call_kwargs['enable_auto_commit'] is False


class TestKafkaBasePushToKafka:
    """Tests for push_to_kafka method."""

    @pytest.fixture(autouse=True)
    def setup_kafka_base(self):
        """Setup KAFKA_BASE with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.KAFKA_BROKER = "localhost:9092"
        mock_settings.KAFKA_VERSION_TIMEOUT = 5000
        mock_settings.KAFKA_REQUEST_TIMEOUT = 10000

        with patch('unpod.common.services.kafka_store.settings', mock_settings):
            from unpod.common.services.kafka_store import KAFKA_BASE
            self.KAFKA_BASE = KAFKA_BASE
            self.mock_settings = mock_settings
            yield

    def test_push_to_kafka_sends_message(self):
        """Test that push_to_kafka sends message to correct topic."""
        kafka_base = self.KAFKA_BASE()

        with patch.object(kafka_base, 'get_producer') as mock_get_producer:
            mock_producer = MagicMock()
            mock_get_producer.return_value = mock_producer

            data = {"event": "test", "value": 123}
            kafka_base.push_to_kafka("test-topic", data)

            mock_producer.send.assert_called_once_with("test-topic", data)
            mock_producer.flush.assert_called_once()
            mock_producer.close.assert_called_once()

    def test_push_to_kafka_with_different_topics(self):
        """Test pushing to different topics."""
        kafka_base = self.KAFKA_BASE()

        with patch.object(kafka_base, 'get_producer') as mock_get_producer:
            mock_producer = MagicMock()
            mock_get_producer.return_value = mock_producer

            # Push to first topic
            kafka_base.push_to_kafka("topic-1", {"data": 1})
            mock_producer.send.assert_called_with("topic-1", {"data": 1})

            # Reset mock for second call
            mock_producer.reset_mock()

            # Push to second topic
            kafka_base.push_to_kafka("topic-2", {"data": 2})
            mock_producer.send.assert_called_with("topic-2", {"data": 2})

    def test_push_to_kafka_flushes_before_close(self):
        """Test that flush is called before close."""
        kafka_base = self.KAFKA_BASE()

        with patch.object(kafka_base, 'get_producer') as mock_get_producer:
            mock_producer = MagicMock()
            mock_get_producer.return_value = mock_producer

            call_order = []
            mock_producer.flush.side_effect = lambda: call_order.append('flush')
            mock_producer.close.side_effect = lambda: call_order.append('close')

            kafka_base.push_to_kafka("test-topic", {"test": True})

            assert call_order == ['flush', 'close']

    def test_push_to_kafka_with_complex_data(self):
        """Test pushing complex nested data."""
        kafka_base = self.KAFKA_BASE()

        with patch.object(kafka_base, 'get_producer') as mock_get_producer:
            mock_producer = MagicMock()
            mock_get_producer.return_value = mock_producer

            complex_data = {
                "event_type": "order_created",
                "timestamp": "2026-01-29T10:00:00Z",
                "payload": {
                    "order_id": 12345,
                    "items": [
                        {"product_id": 1, "quantity": 2, "price": 99.99},
                        {"product_id": 2, "quantity": 1, "price": 49.99}
                    ],
                    "customer": {
                        "id": 789,
                        "email": "customer@example.com"
                    }
                }
            }

            kafka_base.push_to_kafka("orders", complex_data)

            mock_producer.send.assert_called_once_with("orders", complex_data)


class TestKafkaBaseEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.fixture(autouse=True)
    def setup_kafka_base(self):
        """Setup KAFKA_BASE with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.KAFKA_BROKER = "localhost:9092"
        mock_settings.KAFKA_VERSION_TIMEOUT = 5000
        mock_settings.KAFKA_REQUEST_TIMEOUT = 10000

        with patch('unpod.common.services.kafka_store.settings', mock_settings):
            from unpod.common.services.kafka_store import KAFKA_BASE
            self.KAFKA_BASE = KAFKA_BASE
            yield

    def test_serialize_empty_dict(self):
        """Test serializing empty dictionary."""
        result = self.KAFKA_BASE.serialize_data({})
        assert result == b'{}'

    def test_serialize_empty_list(self):
        """Test serializing empty list."""
        result = self.KAFKA_BASE.serialize_data([])
        assert result == b'[]'

    def test_serialize_null_value(self):
        """Test serializing None/null."""
        result = self.KAFKA_BASE.serialize_data(None)
        assert result == b'null'

    def test_serialize_boolean(self):
        """Test serializing boolean values."""
        assert self.KAFKA_BASE.serialize_data(True) == b'true'
        assert self.KAFKA_BASE.serialize_data(False) == b'false'

    def test_serialize_number(self):
        """Test serializing numeric values."""
        assert self.KAFKA_BASE.serialize_data(42) == b'42'
        assert self.KAFKA_BASE.serialize_data(3.14) == b'3.14'

    def test_serialize_string(self):
        """Test serializing string value."""
        result = self.KAFKA_BASE.serialize_data("hello")
        assert result == b'"hello"'

    def test_deserialize_empty_dict(self):
        """Test deserializing empty dictionary."""
        result = self.KAFKA_BASE.deserialize_data(b'{}')
        assert result == {}

    def test_deserialize_empty_list(self):
        """Test deserializing empty list."""
        result = self.KAFKA_BASE.deserialize_data(b'[]')
        assert result == []

    def test_serialize_special_characters(self):
        """Test serializing data with special characters."""
        data = {"text": "Line1\nLine2\tTab\"Quote"}
        result = self.KAFKA_BASE.serialize_data(data)
        deserialized = self.KAFKA_BASE.deserialize_data(result)
        assert deserialized == data

    def test_serialize_large_data(self):
        """Test serializing large data payload."""
        large_list = [{"id": i, "data": f"item_{i}"} for i in range(1000)]
        data = {"items": large_list}

        result = self.KAFKA_BASE.serialize_data(data)
        deserialized = self.KAFKA_BASE.deserialize_data(result)

        assert deserialized == data
        assert len(deserialized["items"]) == 1000


class TestKafkaBaseIntegration:
    """Integration-style tests for KAFKA_BASE."""

    @pytest.fixture(autouse=True)
    def setup_kafka_base(self):
        """Setup KAFKA_BASE with mocked settings."""
        mock_settings = MagicMock()
        mock_settings.KAFKA_BROKER = "localhost:9092"
        mock_settings.KAFKA_VERSION_TIMEOUT = 5000
        mock_settings.KAFKA_REQUEST_TIMEOUT = 10000

        with patch('unpod.common.services.kafka_store.settings', mock_settings):
            from unpod.common.services.kafka_store import KAFKA_BASE
            self.KAFKA_BASE = KAFKA_BASE
            yield

    def test_serialize_used_by_producer(self):
        """Test that serializer function works with producer pattern."""
        kafka_base = self.KAFKA_BASE()

        # Simulate what KafkaProducer does with the serializer
        data = {"key": "value"}
        serializer = lambda v: kafka_base.serialize_data(v)

        result = serializer(data)

        assert isinstance(result, bytes)
        assert json.loads(result) == data

    def test_deserialize_used_by_consumer(self):
        """Test that deserializer function works with consumer pattern."""
        kafka_base = self.KAFKA_BASE()

        # Simulate what KafkaConsumer does with the deserializer
        original = {"event": "test"}
        message_bytes = json.dumps(original).encode("utf-8")
        deserializer = lambda v: kafka_base.deserialize_data(v)

        result = deserializer(message_bytes)

        assert result == original

    def test_full_message_flow(self):
        """Test full message serialization -> send -> receive -> deserialize flow."""
        kafka_base = self.KAFKA_BASE()

        # Original message
        original_message = {
            "event": "user_action",
            "user_id": 123,
            "action": "login",
            "metadata": {"ip": "192.168.1.1", "browser": "Chrome"}
        }

        # Serialize (producer side)
        serialized = kafka_base.serialize_data(original_message)
        assert isinstance(serialized, bytes)

        # Deserialize (consumer side)
        deserialized = kafka_base.deserialize_data(serialized)
        assert deserialized == original_message
