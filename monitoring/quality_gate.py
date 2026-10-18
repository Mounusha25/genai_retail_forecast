"""Deterministic quality gates for forecast monitoring runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Literal


@dataclass(frozen=True)
class QualityGateConfig:
    """Thresholds that decide whether a model should be retrained."""

    max_mape_pct: float = 25.0
    max_abs_bias_pct: float = 20.0
    max_mae_regression_pct: float = 15.0


@dataclass(frozen=True)
class EvaluationSnapshot:
    """Observed forecast quality over one historical holdout window."""

    model: str
    model_version: str
    window_start: date
    window_end: date
    sample_count: int
    store_count: int
    mae: float
    rmse: float
    mape_pct: float
    bias_pct: float

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["window_start"] = self.window_start.isoformat()
        payload["window_end"] = self.window_end.isoformat()
        return payload


@dataclass(frozen=True)
class GateResult:
    """Quality-gate decision and evidence used to make it."""

    status: Literal["pass", "fail"]
    retrain_recommended: bool
    reference_mae: float
    mae_regression_pct: float
    violations: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["violations"] = list(self.violations)
        return payload


def evaluate_quality_gate(
    current: EvaluationSnapshot,
    reference: EvaluationSnapshot,
    config: QualityGateConfig | None = None,
) -> GateResult:
    """Compare a monitoring snapshot with a reference using explicit gates."""
    thresholds = config or QualityGateConfig()
    regression = ((current.mae - reference.mae) / reference.mae * 100) if reference.mae else 0.0
    violations: list[str] = []

    if current.mape_pct > thresholds.max_mape_pct:
        violations.append(f"MAPE {current.mape_pct:.2f}% exceeds {thresholds.max_mape_pct:.2f}%")
    if abs(current.bias_pct) > thresholds.max_abs_bias_pct:
        violations.append(f"absolute bias {abs(current.bias_pct):.2f}% exceeds {thresholds.max_abs_bias_pct:.2f}%")
    if regression > thresholds.max_mae_regression_pct:
        violations.append(f"MAE regression {regression:.2f}% exceeds {thresholds.max_mae_regression_pct:.2f}%")

    failed = bool(violations)
    return GateResult(
        status="fail" if failed else "pass",
        retrain_recommended=failed,
        reference_mae=reference.mae,
        mae_regression_pct=regression,
        violations=tuple(violations),
    )
