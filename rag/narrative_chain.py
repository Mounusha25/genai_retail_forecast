from __future__ import annotations

import logging
from typing import Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import get_settings
from rag.prompts import HUMAN_PROMPT, SYSTEM_PROMPT
from rag.vector_store import load_vector_store

logger = logging.getLogger(__name__)


def _make_llm():
    """Return a chat model based on LLM_PROVIDER setting."""
    cfg = get_settings()
    if cfg.llm_provider == "groq":
        from langchain_groq import ChatGroq  # type: ignore[import]

        return ChatGroq(  # type: ignore[call-arg]
            model=cfg.groq_chat_model,
            groq_api_key=cfg.groq_api_key,
            temperature=0.3,
            max_retries=3,
        )
    else:
        from langchain_openai import ChatOpenAI  # type: ignore[import]

        return ChatOpenAI(
            model=cfg.openai_chat_model,
            temperature=0.3,
            openai_api_key=cfg.openai_api_key,
            request_timeout=cfg.openai_request_timeout,
            max_retries=3,
        )


def _format_docs(docs: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] Source: {source}\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def _format_forecast(rows: list[dict[str, Any]], horizon: int) -> str:
    lines = []
    for row in rows:
        lower = row.get("ci_lower")
        upper = row.get("ci_upper")
        ci = f" (80% CI: {lower:.0f}–{upper:.0f})" if lower is not None else ""
        lines.append(f"  {row['forecast_date']}: {row['forecast_units']:.0f} units{ci}")
    return "\n".join(lines)


class NarrativeChain:
    """
    LangChain RAG chain that:
    1. Retrieves top-K business-context chunks for a given product query.
    2. Formats the numeric forecast alongside the context.
    3. Calls GPT-4 to produce a grounded executive summary.

    The chain is stateless and can be called concurrently.
    """

    def __init__(self) -> None:
        cfg = get_settings()
        self._cfg = cfg
        self._store: FAISS | None = None  # lazy-loaded
        self._llm = _make_llm()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", HUMAN_PROMPT),
            ]
        )

    def _get_store(self) -> FAISS:
        if self._store is None:
            self._store = load_vector_store()
        return self._store

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def generate(self, product_id: str, forecast_rows: list[dict[str, Any]]) -> str:
        """
        Generate a narrative summary for *product_id* using *forecast_rows*.

        Args:
            product_id:    SKU identifier, e.g. ``"SKU-001"``.
            forecast_rows: List of dicts with keys
                           ``forecast_date``, ``forecast_units``,
                           ``ci_lower``, ``ci_upper``.

        Returns:
            A 3-paragraph executive summary string.
        """
        cfg = self._cfg
        store = self._get_store()
        retriever = store.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diversity
            search_kwargs={"k": cfg.retriever_top_k, "fetch_k": cfg.retriever_top_k * 3},
        )

        forecast_str = _format_forecast(forecast_rows, cfg.forecast_horizon_days)

        chain = (
            {
                "context": RunnableLambda(lambda x: x["product_id"]) | retriever | RunnableLambda(_format_docs),
                "product_id": RunnableLambda(lambda x: x["product_id"]),
                "forecast_data": RunnableLambda(lambda x: x["forecast_data"]),
                "horizon": RunnableLambda(lambda _: str(cfg.forecast_horizon_days)),
            }
            | self._prompt
            | self._llm
            | StrOutputParser()
        )

        logger.info("Generating narrative for %s (%d forecast rows)", product_id, len(forecast_rows))

        result: str = chain.invoke(
            {
                "product_id": product_id,
                "forecast_data": forecast_str,
            }
        )

        logger.info("Narrative generated for %s (%d chars)", product_id, len(result))
        return result.strip()
