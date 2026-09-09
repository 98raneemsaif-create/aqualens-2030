"""Select only broker-acknowledged offsets belonging to one finite run."""

from time import monotonic
from collections.abc import Iterator
from confluent_kafka import Consumer, KafkaException, TopicPartition

from src.ingestion.quarantine import recover_run_id


class RunWindow:
    def __init__(self, run_id: str, deliveries: list[dict]):
        self.run_id = run_id
        self.expected = {(item['partition'], item['offset']) for item in deliveries}
        if len(self.expected) != len(deliveries):
            raise ValueError('Duplicate offsets in run manifest')
        self.seen: set[tuple[int, int]] = set()

    def includes(self, partition: int, offset: int, run_id: str | None) -> bool:
        position = (partition, offset)
        if position not in self.expected or position in self.seen:
            return False
        # A manifest offset still identifies a malformed record when its run ID
        # cannot be recovered. Let boundary validation route it to quarantine.
        if run_id is not None and run_id != self.run_id:
            raise ValueError(f'Run metadata mismatch at {position}: expected {self.run_id}, got {run_id}')
        return True

    def record_seen(self, partition: int, offset: int) -> None:
        self.seen.add((partition, offset))

    @property
    def complete(self) -> bool:
        return self.seen == self.expected

    def check_deadline(self, deadline: float, now: float) -> None:
        if not self.complete and now >= deadline:
            raise TimeoutError(f'Bounded Kafka read timed out; missing offsets: {sorted(self.expected - self.seen)}')


def read_run(bootstrap: str, topic: str, run_id: str, deliveries: list[dict],
             timeout: float, group_prefix: str) -> Iterator:
    window = RunWindow(run_id, deliveries)
    consumer = Consumer({'bootstrap.servers': bootstrap, 'group.id': f'{group_prefix}-{run_id}',
                         'enable.auto.commit': False, 'enable.auto.offset.store': False,
                         'auto.offset.reset': 'error'})
    starts = {}
    for item in deliveries:
        partition, offset = item['partition'], item['offset']
        starts[partition] = min(starts.get(partition, offset), offset)
    try:
        consumer.assign([TopicPartition(topic, p, offset) for p, offset in starts.items()])
        deadline = monotonic() + timeout
        while not window.complete:
            window.check_deadline(deadline, monotonic())
            message = consumer.poll(min(1.0, max(0.0, deadline - monotonic())))
            if message is None:
                continue
            if message.error():
                raise KafkaException(message.error())
            recovered = recover_run_id(message.value(), message.headers())
            if window.includes(message.partition(), message.offset(), recovered):
                yield message
                window.record_seen(message.partition(), message.offset())
    finally:
        consumer.close()
