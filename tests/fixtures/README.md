# Ingestion test fixtures

`malformed_water_event.json` is a controlled malformed transport event, not an analytical dataset. The proof producer labels it `record_kind=test_fixture` and adds its run/event IDs before publishing it through the real raw topic. It must be rejected by the consumer and appear in Kafka's quarantine topic.

The numeric `-1` example in `test_ingestion.py` tests structural acceptance only. It is never inserted into the official CSV or the 56-row accepted proof output. Business-quality checks belong to the later Great Expectations phase.
