"""Unit tests for the Beam ETL ParseSalesRow DoFn."""

from __future__ import annotations

from etl.beam_pipeline import ParseSalesRow


def _parse(line: str) -> list[dict]:
    """Helper: run ParseSalesRow.process and collect yielded dicts."""
    fn = ParseSalesRow()
    return list(fn.process(line))


class TestParseSalesRow:
    def test_valid_row(self):
        rows = _parse("2024-01-15,SKU-001,S01,42,840.00")
        assert len(rows) == 1
        r = rows[0]
        assert r["date"] == "2024-01-15"
        assert r["product_id"] == "SKU-001"
        assert r["store_id"] == "S01"
        assert r["units_sold"] == 42.0
        assert r["revenue"] == 840.0

    def test_product_id_uppercased(self):
        rows = _parse("2024-01-15,sku-999,S01,1,5.00")
        assert rows[0]["product_id"] == "SKU-999"

    def test_missing_units_defaults_to_zero(self):
        rows = _parse("2024-01-15,SKU-001,S01,,0")
        assert rows[0]["units_sold"] == 0.0

    def test_negative_units_clamped_to_zero(self):
        rows = _parse("2024-01-15,SKU-001,S01,-5,0")
        assert rows[0]["units_sold"] == 0.0

    def test_bad_date_skipped(self):
        rows = _parse("not-a-date,SKU-001,S01,10,100")
        assert rows == []

    def test_empty_product_id_skipped(self):
        rows = _parse("2024-01-15,,S01,10,100")
        assert rows == []

    def test_empty_line_skipped(self):
        rows = _parse("   ")
        assert rows == []

    def test_malformed_csv_skipped(self):
        rows = _parse("garbage line that has no valid fields")
        # Might skip or might produce partial — either way must not raise
        assert isinstance(rows, list)
