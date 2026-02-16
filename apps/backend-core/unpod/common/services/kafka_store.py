import json

from django.conf import settings

from kafka import KafkaConsumer, KafkaProducer


class KAFKA_BASE:

    @staticmethod
    def serialize_data(data):
        return json.dumps(data).encode("utf-8")

    @staticmethod
    def deserialize_data(data):
        return json.loads(data.decode("utf-8"))

    def get_producer(self):
        if hasattr(settings, "kafka_pub"):
            kafka_pub = settings.kafka_pub
            if not kafka_pub._closed:
                return kafka_pub

        print("Creating Kafka Producer", settings.KAFKA_BROKER)
        kafka_pub = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKER,
            api_version=(2, 5, 0),
            value_serializer=lambda v: self.serialize_data(v),
            api_version_auto_timeout_ms=settings.KAFKA_VERSION_TIMEOUT,
            request_timeout_ms=settings.KAFKA_REQUEST_TIMEOUT,
        )
        settings.kafka_pub = kafka_pub
        return kafka_pub

    def get_consumer(self, topic_name, group_id, prefix=None, consumer_timeout=10000, **kwargs):
        if prefix:
            topic_name = prefix + topic_name
        else:
            topic_name = settings.KAFKA_TOPIC_BASE + topic_name

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
            topic_name = settings.KAFKA_TOPIC_BASE + topic_name

        print("Pushing to Kafka Topic", topic_name)
        producer = self.get_producer()
        producer.send(topic_name, data)
        producer.flush()
        print("Documents sent to Kafka.")
        producer.close()
