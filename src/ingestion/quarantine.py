"""Preserve rejected bytes and validation reasons in the Kafka DLQ payload."""

import base64
from datetime import datetime, timezone
import json


def recover_run_id(payload: bytes | None, headers: list | None) -> str | None:
    for key, value in headers or []:
        if key == 'run_id' and value is not None:
            try:
                return value.decode('utf-8')
            except UnicodeDecodeError:
                continue
    try:
        decoded = json.loads(payload) if payload is not None else None
    except (ValueError, UnicodeDecodeError):
        return None
    return decoded.get('run_id') if isinstance(decoded, dict) and isinstance(decoded.get('run_id'), str) else None


def quarantine_record(payload: bytes | None, run_id: str | None, reason: str,
                      topic: str, partition: int, offset: int) -> dict:
    if not reason.strip():
        raise ValueError('Every rejected record requires a rejection reason')
    return {'original_payload': payload.decode('utf-8', errors='replace') if payload is not None else None,
            'original_payload_base64': base64.b64encode(payload).decode('ascii') if payload is not None else None,
            'run_id': run_id, 'rejection_reason': reason,
            'rejected_at': datetime.now(timezone.utc).isoformat(),
            'raw_topic': topic, 'raw_partition': partition, 'raw_offset': offset}
