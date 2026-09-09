"""Environment configuration for the bounded Kafka ingestion commands."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class IngestionConfig:
    bootstrap_servers: str
    raw_topic: str
    quarantine_topic: str
    source_path: Path
    output_root: Path
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> 'IngestionConfig':
        timeout = float(os.getenv('INGESTION_TIMEOUT_SECONDS', '60'))
        if timeout <= 0:
            raise ValueError('INGESTION_TIMEOUT_SECONDS must be positive')
        return cls(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092'),
            raw_topic=os.getenv('KAFKA_RAW_TOPIC', 'aqualens.water.raw.v1'),
            quarantine_topic=os.getenv('KAFKA_QUARANTINE_TOPIC', 'aqualens.water.quarantine.v1'),
            source_path=Path(os.getenv('WATER_SOURCE_CSV', 'data/source/water_distribution_urban_saudi.csv')),
            output_root=Path(os.getenv('INGESTION_OUTPUT_ROOT', 'storage/ingestion')),
            timeout_seconds=timeout,
        )
