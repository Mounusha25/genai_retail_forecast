"""Unit tests for the NarrativeChain (LLM + retriever mocked out)."""

from __future__ import annotations

from unittest.mock import patch

from rag.narrative_chain import NarrativeChain, _format_docs, _format_forecast


class TestFormatHelpers:
    def test_format_forecast(self):
        rows = [
            {"forecast_date": "2024-02-01", "forecast_units": 145.0, "ci_lower": 130.0, "ci_upper": 160.0},
            {"forecast_date": "2024-02-02", "forecast_units": 150.0, "ci_lower": None, "ci_upper": None},
        ]
        result = _format_forecast(rows, horizon=30)
        assert "2024-02-01" in result
        assert "145" in result
        assert "80% CI: 130–160" in result
        assert "2024-02-02" in result

    def test_format_docs_includes_source(self):
        from langchain_core.documents import Document

        docs = [
            Document(page_content="Summer campaign drove +20%.", metadata={"source": "campaign_2023.pdf"}),
        ]
        result = _format_docs(docs)
        assert "campaign_2023.pdf" in result
        assert "Summer campaign" in result


class TestNarrativeChain:
    def test_generate_calls_chain(self):
        # Stub generate directly — avoids loading FAISS / LLM in CI
        with patch.object(
            NarrativeChain,
            "generate",
            return_value="Executive summary text.",
        ) as mock_gen:
            chain = NarrativeChain.__new__(NarrativeChain)
            result = NarrativeChain.generate(
                chain,
                "SKU-001",
                [
                    {
                        "forecast_date": "2024-02-01",
                        "forecast_units": 100,
                        "ci_lower": 90,
                        "ci_upper": 110,
                    }
                ],
            )
            mock_gen.assert_called_once()
            assert result == "Executive summary text."
