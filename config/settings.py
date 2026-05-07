from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── GCP ────────────────────────────────────────────────────
    google_cloud_project: str = Field(..., description="GCP project ID")
    gcs_bucket: str = Field(..., description="GCS bucket for raw sales data")
    bq_dataset: str = Field("retail_forecasting", description="BigQuery dataset name")
    bq_location: str = Field("US", description="BigQuery dataset region")
    dataflow_region: str = Field("us-central1", description="Dataflow worker region")

    # ── Database ───────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host/db",
    )
    db_pool_size: int = Field(10, ge=1, le=50)
    db_max_overflow: int = Field(20, ge=0, le=100)
    db_pool_timeout: int = Field(30, ge=5)

    # ── LLM / Embedding provider ───────────────────────────────
    llm_provider: Literal["groq", "openai"] = Field("groq", description="LLM backend")
    embedding_provider: Literal["local", "openai"] = Field(
        "local", description="Embedding backend: 'local' = HuggingFace, 'openai' = OpenAI"
    )

    # ── OpenAI (optional — only needed when provider=openai) ───
    openai_api_key: str | None = Field(None, description="OpenAI secret key")
    openai_embed_model: str = Field("text-embedding-3-small")
    openai_chat_model: str = Field("gpt-4o")
    openai_request_timeout: int = Field(60, ge=10)

    # ── Groq (free tier — https://console.groq.com) ────────────
    groq_api_key: str | None = Field(None, description="Groq API key")
    groq_chat_model: str = Field("llama-3.3-70b-versatile")

    # ── HuggingFace local embeddings ───────────────────────────
    huggingface_embed_model: str = Field("all-MiniLM-L6-v2")

    # ── RAG ────────────────────────────────────────────────────
    faiss_index_path: str = Field("data/faiss_index")
    docs_dir: str = Field("data/business_docs")
    chunk_size: int = Field(600, ge=100)
    chunk_overlap: int = Field(80, ge=0)
    retriever_top_k: int = Field(5, ge=1, le=20)

    # ── Pipeline / Scheduler ───────────────────────────────────
    scheduler_secret: str = Field(..., description="Shared secret for /run-pipeline endpoint")
    forecast_horizon_days: int = Field(30, ge=1, le=365)

    # ── App ────────────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    environment: Literal["development", "staging", "production"] = "development"
    app_version: str = "1.0.0"

    @field_validator("database_url")
    @classmethod
    def _validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("database_url must use the postgresql+asyncpg:// scheme for async support")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def gcs_raw_path(self) -> str:
        return f"gs://{self.gcs_bucket}/sales/*.csv"

    @property
    def gcs_temp(self) -> str:
        return f"gs://{self.gcs_bucket}/tmp"

    @property
    def gcs_staging(self) -> str:
        return f"gs://{self.gcs_bucket}/staging"

    @property
    def bq_sales_table(self) -> str:
        return f"{self.google_cloud_project}:{self.bq_dataset}.sales_clean"

    @property
    def bq_forecast_table(self) -> str:
        return f"{self.google_cloud_project}.{self.bq_dataset}.forecasts_30d"

    @property
    def bq_model_ref(self) -> str:
        return f"`{self.google_cloud_project}.{self.bq_dataset}.arima_sales_model`"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # pydantic-settings reads env vars, not ctor args
