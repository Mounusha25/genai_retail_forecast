export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

// ── Types (mirrors api/schemas.py) ────────────────────────────

export type FleetSummaryRow = {
  product_id: string;
  total_30d: number;
  avg_daily: number;
  peak_day: number;
  avg_ci_width: number | null;
};

export type FleetSummaryResponse = {
  count: number;
  stores: FleetSummaryRow[];
};

export type DailyTrendRow = {
  forecast_date: string;
  total_units: number;
  avg_per_store: number;
  stores_active: number;
};

export type DailyTrendResponse = {
  count: number;
  days: DailyTrendRow[];
};

export type DayOfWeekPatternRow = {
  dow: number;
  day_abbr: string;
  avg_units: number;
  total_units: number;
};

export type DayOfWeekPatternResponse = {
  count: number;
  days: DayOfWeekPatternRow[];
};

export type NarrativeCoverageResponse = {
  narrative_rows: number;
  stores_with_narratives: number;
  total_stores: number;
  coverage_pct: number;
};

export type BaselineMetricRow = {
  model: string;
  mae: number;
  rmse: number;
  mape_pct: number;
  bias_pct: number;
};

export type BaselineMetricsResponse = {
  count: number;
  metrics: BaselineMetricRow[];
};

export type StoreListResponse = {
  count: number;
  stores: string[];
};

export type ForecastRow = {
  forecast_date: string;
  forecast_units: number;
  ci_lower: number | null;
  ci_upper: number | null;
};

export type ForecastsResponse = {
  product_id: string;
  count: number;
  forecasts: ForecastRow[];
};

export type NarrativeResponse = {
  product_id: string;
  summary: string;
  generated_at: string;
  retrieved_sources?: string[] | null;
};

// ── Fetch helpers ──────────────────────────────────────────────

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { method: "POST", cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `${path} failed: ${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const getFleetSummary = () => getJson<FleetSummaryResponse>("/v1/dashboard/fleet-summary");
export const getDailyTrend = () => getJson<DailyTrendResponse>("/v1/dashboard/daily-trend");
export const getDowPattern = () => getJson<DayOfWeekPatternResponse>("/v1/dashboard/dow-pattern");
export const getNarrativeCoverage = () => getJson<NarrativeCoverageResponse>("/v1/dashboard/narrative-coverage");
export const getBaselineMetrics = () => getJson<BaselineMetricsResponse>("/v1/dashboard/baseline-metrics");
export const getStores = () => getJson<StoreListResponse>("/v1/dashboard/stores");
export const getForecast = (productId: string) => getJson<ForecastsResponse>(`/v1/forecasts/${productId}`);
export const getNarrative = (productId: string) => getJson<NarrativeResponse>(`/v1/narrative/${productId}`);
export const generateNarrative = (productId: string) => postJson<NarrativeResponse>(`/v1/narrative/${productId}/generate`);
