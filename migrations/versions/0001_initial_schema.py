"""Initial schema — forecasts, narratives, pipeline_runs

Revision ID: 0001
Revises:
Create Date: 2026-04-21
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "forecasts",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("forecast_units", sa.Float(), nullable=False),
        sa.Column("ci_lower", sa.Float(), nullable=True),
        sa.Column("ci_upper", sa.Float(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forecasts_product_date", "forecasts", ["product_id", "forecast_date"])

    op.create_table(
        "narratives",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("product_id", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_narratives_product_generated", "narratives", ["product_id", "generated_at"])

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("triggered_by", sa.String(64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("pipeline_runs")
    op.drop_index("ix_narratives_product_generated", table_name="narratives")
    op.drop_table("narratives")
    op.drop_index("ix_forecasts_product_date", table_name="forecasts")
    op.drop_table("forecasts")
