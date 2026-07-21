import type {
  BaselineMetricsResponse,
  DailyTrendResponse,
  DayOfWeekPatternResponse,
  FleetSummaryResponse,
  ForecastsResponse,
} from "@/lib/api";

const num = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export function dailyTrendInsight(data: DailyTrendResponse | null): string | null {
  if (!data || data.days.length < 2) return null;
  const first = data.days[0];
  const last = data.days[data.days.length - 1];
  const change = ((last.total_units - first.total_units) / first.total_units) * 100;
  const direction = change >= 0 ? "rises" : "falls";
  return `Fleet-wide demand ${direction} ${Math.abs(change).toFixed(1)}% over the forecast window — from ${num.format(first.total_units)} to ${num.format(last.total_units)} units/day.`;
}

export function topStoreInsight(data: FleetSummaryResponse | null): string | null {
  if (!data || data.stores.length === 0) return null;
  const total = data.stores.reduce((sum, s) => sum + s.total_30d, 0);
  const top = data.stores[0];
  const share = (top.total_30d / total) * 100;
  return `${top.product_id} leads the fleet with ${num.format(top.total_30d)} forecasted units — ${share.toFixed(1)}% of total 30-day volume.`;
}

export function dowInsight(data: DayOfWeekPatternResponse | null): string | null {
  if (!data || data.days.length === 0) return null;
  const avg = data.days.reduce((sum, d) => sum + d.avg_units, 0) / data.days.length;
  const peak = [...data.days].sort((a, b) => b.avg_units - a.avg_units)[0];
  const lift = ((peak.avg_units - avg) / avg) * 100;
  return `${peak.day_abbr} is the peak demand day, ${lift.toFixed(0)}% above the weekly average.`;
}

export function peakDay(data: DayOfWeekPatternResponse | null): { day_abbr: string; avg_units: number } | null {
  if (!data || data.days.length === 0) return null;
  return [...data.days].sort((a, b) => b.avg_units - a.avg_units)[0];
}

export function tierInsight(high: number, mid: number, low: number, total: number): string {
  return `${high} store${high === 1 ? "" : "s"} rank High volume (top 5%), ${mid} Mid, and ${low} Low — out of ${total} forecasted stores.`;
}

export function uncertaintyInsight(data: FleetSummaryResponse | null): string | null {
  if (!data || data.stores.length === 0) return null;
  const withCi = data.stores.filter((s) => s.avg_ci_width != null);
  if (withCi.length === 0) return null;
  const widest = [...withCi].sort((a, b) => (b.avg_ci_width ?? 0) - (a.avg_ci_width ?? 0))[0];
  return `${widest.product_id} carries the widest forecast uncertainty (±${num.format((widest.avg_ci_width ?? 0) / 2)} units) relative to its volume.`;
}

export function baselineInsight(data: BaselineMetricsResponse | null): string | null {
  if (!data || data.metrics.length < 2) return null;
  const sorted = [...data.metrics].sort((a, b) => a.mae - b.mae);
  const best = sorted[0];
  const runnerUp = sorted[1];
  const improvement = ((runnerUp.mae - best.mae) / runnerUp.mae) * 100;
  return `${best.model} beats the next-best baseline (${runnerUp.model}) by ${improvement.toFixed(1)}% MAE, at ${best.mape_pct.toFixed(1)}% MAPE.`;
}

export function forecastInsight(data: ForecastsResponse | null): string | null {
  if (!data || data.forecasts.length < 2) return null;
  const first = data.forecasts[0];
  const last = data.forecasts[data.forecasts.length - 1];
  const change = ((last.forecast_units - first.forecast_units) / first.forecast_units) * 100;
  const direction = change >= 0 ? "trending up" : "trending down";
  const avgCiWidth =
    data.forecasts.filter((f) => f.ci_lower != null && f.ci_upper != null).reduce((sum, f) => sum + ((f.ci_upper ?? 0) - (f.ci_lower ?? 0)), 0) /
    data.forecasts.length;
  return `${data.product_id} is ${direction} ${Math.abs(change).toFixed(1)}% over the 30-day horizon, with an average confidence band of ±${num.format(avgCiWidth / 2)} units.`;
}

export function compareInsight(
  storeA: string,
  totalA: number | null,
  storeB: string,
  totalB: number | null,
): string | null {
  if (totalA == null || totalB == null || storeA === storeB) return null;
  const higher = totalA >= totalB ? storeA : storeB;
  const lower = totalA >= totalB ? storeB : storeA;
  const diff = Math.abs(totalA - totalB);
  const pctDiff = (diff / Math.min(totalA, totalB)) * 100;
  return `${higher} outforecasts ${lower} by ${num.format(diff)} units over 30 days — a ${pctDiff.toFixed(1)}% gap.`;
}
