"""Structural ingestion contract; business-quality rules belong to later GX."""

from typing import Literal
from pydantic import BaseModel, ConfigDict


class WaterEvent(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', allow_inf_nan=False)

    year: int
    region: str
    source: str
    volume_m3: float  # Numeric negatives and zero deliberately remain valid.
    run_id: str
    event_id: str
    record_kind: Literal['source', 'test_fixture']
