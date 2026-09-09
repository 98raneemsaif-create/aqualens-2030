"""Focused structural and bounded-run tests; no external service substitutions."""

import base64
import json
import unittest
from pydantic import ValidationError

from src.ingestion.bounded import RunWindow
from src.ingestion.quarantine import quarantine_record, recover_run_id
from src.ingestion.schema import WaterEvent


class IngestionTests(unittest.TestCase):
    def event(self, volume=0):
        return dict(year=2024, region='Grand Total', source='Groundwater', volume_m3=volume,
                    run_id='unit-test-run', event_id='unit-test-event', record_kind='test_fixture')

    def test_valid_event_zero_and_grand_total_accepted(self):
        self.assertEqual(WaterEvent.model_validate(self.event()).volume_m3, 0)

    def test_malformed_numeric_field_rejected(self):
        with self.assertRaises(ValidationError):
            WaterEvent.model_validate(self.event('not-a-number'))

    def test_negative_numeric_value_structurally_accepted(self):
        event = WaterEvent.model_validate(self.event(-1))
        self.assertEqual(event.volume_m3, -1)
        print('NEGATIVE STRUCTURAL PROOF:', event.model_dump_json(), flush=True)

    def test_required_field_and_strict_types(self):
        for field in ['year', 'region', 'source', 'volume_m3']:
            event = self.event()
            del event[field]
            with self.subTest(field=field), self.assertRaises(ValidationError):
                WaterEvent.model_validate(event)
        for value in ['12', True, None]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                WaterEvent.model_validate(self.event(value))

    def test_quarantine_reason_and_original_bytes(self):
        payload = json.dumps(self.event('not-a-number')).encode()
        try:
            WaterEvent.model_validate_json(payload)
        except ValidationError as error:
            record = quarantine_record(payload, 'unit-test-run', str(error), 'raw', 0, 2)
        else:
            self.fail('Malformed event was accepted')
        self.assertIn('volume_m3', record['rejection_reason'])
        self.assertEqual(base64.b64decode(record['original_payload_base64']), payload)
        self.assertTrue(record['rejected_at'])
        with self.assertRaises(ValueError):
            quarantine_record(payload, None, ' ', 'raw', 0, 2)

    def test_invalid_json_run_id_recovered_from_header(self):
        self.assertEqual(recover_run_id(b'{broken', [('run_id', b'current')]), 'current')
        self.assertIsNone(recover_run_id(b'{broken', None))
        self.assertEqual(recover_run_id(b'{"run_id":"body"}', None), 'body')
        with self.assertRaises(ValidationError):
            WaterEvent.model_validate_json(b'{broken')

    def test_run_filters_old_offsets_and_other_runs(self):
        window = RunWindow('current', [{'partition': 0, 'offset': 57}, {'partition': 0, 'offset': 59}])
        self.assertFalse(window.includes(0, 1, 'old'))
        self.assertFalse(window.includes(0, 58, 'interleaved-other-run'))
        self.assertTrue(window.includes(0, 57, 'current'))
        with self.assertRaises(ValueError):
            window.includes(0, 59, 'wrong-run-at-expected-offset')
        window.record_seen(0, 57)
        self.assertFalse(window.includes(0, 57, 'current'))
        self.assertFalse(window.complete)
        window.record_seen(0, 59)
        self.assertTrue(window.complete)

    def test_incomplete_run_times_out_instead_of_hanging(self):
        window = RunWindow('current', [{'partition': 0, 'offset': 57}])
        window.check_deadline(deadline=10, now=9)
        with self.assertRaisesRegex(TimeoutError, 'missing offsets'):
            window.check_deadline(deadline=10, now=10)
        window.record_seen(0, 57)
        window.check_deadline(deadline=10, now=11)

    def test_unrecoverable_run_id_still_reaches_boundary(self):
        window = RunWindow('current', [{'partition': 0, 'offset': 57}])
        payload = b'{broken'
        recovered = recover_run_id(payload, None)
        self.assertTrue(window.includes(0, 57, recovered))
        record = quarantine_record(payload, recovered, 'Invalid JSON', 'raw', 0, 57)
        self.assertIsNone(record['run_id'])
        self.assertTrue(record['rejection_reason'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
