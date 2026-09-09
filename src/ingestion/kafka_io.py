"""Real Kafka topic management and broker-acknowledged JSON publication."""

import json
from confluent_kafka import KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from src.common.config import IngestionConfig


def ensure_topics(config: IngestionConfig) -> None:
    admin = AdminClient({'bootstrap.servers': config.bootstrap_servers})
    topics = [config.raw_topic, config.quarantine_topic]
    futures = admin.create_topics([NewTopic(name, num_partitions=1, replication_factor=1)
                                  for name in topics], request_timeout=15)
    for name, future in futures.items():
        try:
            future.result()
            print(json.dumps({'action': 'topic_created', 'topic': name}), flush=True)
        except KafkaException as error:
            from confluent_kafka import KafkaError
            if error.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                raise
            print(json.dumps({'action': 'topic_exists', 'topic': name}), flush=True)


def new_producer(config: IngestionConfig) -> Producer:
    return Producer({'bootstrap.servers': config.bootstrap_servers,
                     'enable.idempotence': True, 'acks': 'all',
                     'delivery.timeout.ms': 30000, 'request.timeout.ms': 10000})


def publish_json(producer: Producer, topic: str, records: list[dict],
                 run_id: str, timeout: float) -> list[dict]:
    deliveries, errors = [], []

    def delivered(error, message):
        if error is not None:
            errors.append(str(error))
        else:
            deliveries.append({'topic': message.topic(), 'partition': message.partition(),
                               'offset': message.offset(), 'key': message.key().decode('utf-8')})

    for index, record in enumerate(records):
        key = f"{run_id}:{record.get('event_id', index)}"
        payload = json.dumps(record, ensure_ascii=False, allow_nan=False).encode('utf-8')
        producer.produce(topic, key=key, value=payload, headers={'run_id': run_id.encode()},
                         on_delivery=delivered)
        producer.poll(0)
    pending = producer.flush(timeout)
    if errors or pending or len(deliveries) != len(records):
        raise RuntimeError(f'Kafka delivery failed: errors={errors}, pending={pending}, '
                           f'acknowledged={len(deliveries)}, expected={len(records)}')
    return sorted(deliveries, key=lambda item: (item['partition'], item['offset']))
