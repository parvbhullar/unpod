import json
import os

os.environ.setdefault("EVENTLET_IMPORT_VERSION_ONLY", "1")
from kafka import KafkaConsumer, KafkaProducer
from nameko.extensions import Entrypoint
from libs.api.config import get_settings

settings = get_settings()


class KAFKA_BASE:
    def serialize_data(self, data):
        return json.dumps(data).encode("utf-8")

    def deserialize_data(self, data):
        return json.loads(data.decode("utf-8"))

    def get_producer(self):
        if hasattr(settings, "kafka_pub"):
            kafka_pub = settings.kafka_pub
            if not kafka_pub._closed:
                return kafka_pub
        kafka_pub = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER,
            api_version=(2, 5, 0),
            value_serializer=lambda v: self.serialize_data(v),
            api_version_auto_timeout_ms=settings.KAFKA_VERSION_TIMEOUT,
            request_timeout_ms=settings.KAFKA_REQUEST_TIMEOUT,
        )
        settings.kafka_pub = kafka_pub
        return kafka_pub

    def get_consumer(self, topic_name, group_id, consumer_timeout=10000, **kwargs):
        topic_name = settings.KAFKA_TOPIC_BASE_MESSAGING + topic_name
        return KafkaConsumer(
            topic_name,
            bootstrap_servers=settings.KAFKA_BROKER,
            value_deserializer=lambda v: self.deserialize_data(v),
            group_id=group_id,
            consumer_timeout_ms=consumer_timeout,
            **kwargs
        )

    def push_to_kafka(self, topic_name, data, prefix=None):
        if prefix:
            topic_name = prefix + topic_name
        else:
            topic_name = settings.KAFKA_TOPIC_BASE_MESSAGING + topic_name
        producer = self.get_producer()
        producer.send(topic_name, data)
        producer.close()


class NamekoKafka(Entrypoint):
    def __init__(self, topic, group_id):
        topic = settings.KAFKA_TOPIC_BASE_MESSAGING + topic
        self.topics = topic
        self.group_id = group_id
        self.consumer = None
        self.kafka_brokers = settings.KAFKA_BROKER
        if isinstance(self.kafka_brokers, list) and len(self.kafka_brokers) > 1:
            self.kafka_brokers = self.kafka_brokers[::-1]

    def setup(self):
        self.consumer = KafkaConsumer(
            self.topics,
            group_id=self.group_id,
            bootstrap_servers=self.kafka_brokers,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            auto_commit_interval_ms=1000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

    def start(self):
        self.container.spawn_managed_thread(self.run, identifier="NamekoKafka.run")

    def run(self):
        for message in self.consumer:
            self.handle_message(message)

    def handle_message(self, message):
        args = (message,)
        kwargs = {}
        self.container.spawn_worker(self, args, kwargs)

    def stop(self):
        self.consumer.close()


consume = NamekoKafka.decorator
