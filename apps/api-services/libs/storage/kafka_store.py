import json
import os

os.environ.setdefault("EVENTLET_IMPORT_VERSION_ONLY", "1")
from kafka import KafkaConsumer, KafkaProducer
from libs.api.logger import get_logger

app_logging = get_logger("kafka")


class KAFKA_BASE:
    """
    Base class for Kafka operations.

    This class requires settings to be provided via constructor or passed
    to individual methods. Settings object should have the following attributes:
    - KAFKA_BROKER: Kafka broker URL
    - KAFKA_TOPIC_BASE: Base topic name prefix
    - KAFKA_VERSION_TIMEOUT: Version timeout in ms
    - KAFKA_REQUEST_TIMEOUT: Request timeout in ms
    - kafka_pub: (optional) Cached Kafka producer instance
    """

    def __init__(self, settings=None):
        """
        Initialize KAFKA_BASE with settings.

        Args:
            settings: Settings object with Kafka configuration
        """
        self.settings = settings

    def serialize_data(self, data):
        return json.dumps(data).encode("utf-8")

    def deserialize_data(self, data):
        return json.loads(data.decode("utf-8"))

    def get_producer(self, settings=None):
        """
        Get or create a Kafka producer.

        Args:
            settings: Settings object (uses instance settings if not provided)

        Returns:
            KafkaProducer instance
        """
        if settings is None:
            settings = self.settings
        if settings is None:
            raise ValueError(
                "Settings must be provided either in constructor or method call"
            )

        if hasattr(settings, "kafka_pub"):
            kafka_pub = settings.kafka_pub
            if not kafka_pub._closed:
                return kafka_pub
        app_logging.info("Creating Kafka Producer", settings.KAFKA_BROKER)
        kafka_pub = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER,
            api_version=(2, 5, 0),
            value_serializer=lambda v: self.serialize_data(v),
            api_version_auto_timeout_ms=settings.KAFKA_VERSION_TIMEOUT,
            request_timeout_ms=settings.KAFKA_REQUEST_TIMEOUT,
        )
        settings.kafka_pub = kafka_pub
        return kafka_pub

    def get_consumer(
        self, topic_name, group_id, consumer_timeout=10000, settings=None, **kwargs
    ):
        """
        Create a Kafka consumer.

        Args:
            topic_name: Topic name (will be prefixed with KAFKA_TOPIC_BASE)
            group_id: Consumer group ID
            consumer_timeout: Consumer timeout in ms (default: 10000)
            settings: Settings object (uses instance settings if not provided)
            **kwargs: Additional keyword arguments for KafkaConsumer

        Returns:
            KafkaConsumer instance
        """
        if settings is None:
            settings = self.settings
        if settings is None:
            raise ValueError(
                "Settings must be provided either in constructor or method call"
            )

        topic_name = settings.KAFKA_TOPIC_BASE + topic_name
        return KafkaConsumer(
            topic_name,
            bootstrap_servers=settings.KAFKA_BROKER,
            value_deserializer=lambda v: self.deserialize_data(v),
            group_id=group_id,
            consumer_timeout_ms=consumer_timeout,
            **kwargs
        )

    def push_to_kafka(self, topic_name, data, settings=None):
        """
        Push data to Kafka topic.

        Args:
            topic_name: Topic name (will be prefixed with KAFKA_TOPIC_BASE)
            data: Data to publish
            settings: Settings object (uses instance settings if not provided)
        """
        if settings is None:
            settings = self.settings
        if settings is None:
            raise ValueError(
                "Settings must be provided either in constructor or method call"
            )

        topic_name = settings.KAFKA_TOPIC_BASE + topic_name
        app_logging.info("Pushing to Kafka Topic", topic_name)
        producer = self.get_producer(settings)
        producer.send(topic_name, data)
        producer.flush()
        app_logging.info("Documents sent to Kafka.")
        producer.close()
