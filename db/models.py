from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Forecast(Base):
    """Stores per-product, per-day numeric forecasts with confidence intervals."""

    __tablename__ = "forecasts"
    __table_args__ = (Index("ix_forecasts_product_date", "product_id", "forecast_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_units: Mapped[float] = mapped_column(Float, nullable=False)
    ci_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    ci_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<Forecast product={self.product_id} date={self.forecast_date} units={self.forecast_units}>"


class Narrative(Base):
    """Stores the latest GPT-4 executive summary for each product."""

    __tablename__ = "narratives"
    __table_args__ = (Index("ix_narratives_product_generated", "product_id", "generated_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<Narrative product={self.product_id} at={self.generated_at}>"


class PipelineRun(Base):
    """Audit log for each pipeline execution."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # "running"|"success"|"failed"
    triggered_by: Mapped[str] = mapped_column(String(64), nullable=False, default="scheduler")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<PipelineRun id={self.id} status={self.status}>"
