from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class SalesRow:
    date: str  # ISO 8601: YYYY-MM-DD
    product_id: str  # upper-case, e.g. "SKU-001"
    store_id: str
    units_sold: float
    revenue: float

    def to_bq_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "product_id": self.product_id,
            "store_id": self.store_id,
            "units_sold": self.units_sold,
            "revenue": self.revenue,
        }


BQ_SCHEMA = {
    "fields": [
        {"name": "date", "type": "DATE", "mode": "REQUIRED"},
        {"name": "product_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "store_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "units_sold", "type": "FLOAT64", "mode": "REQUIRED"},
        {"name": "revenue", "type": "FLOAT64", "mode": "REQUIRED"},
    ]
}

EXPECTED_COLUMNS = ("date", "product_id", "store_id", "units_sold", "revenue")
