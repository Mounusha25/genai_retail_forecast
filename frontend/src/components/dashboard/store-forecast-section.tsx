"use client";

import { Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { LineChart } from "@/components/charts/line-chart";
import { Insight } from "@/components/dashboard/insight";
import { RagBadge } from "@/components/dashboard/rag-badge";
import { StoreSelect } from "@/components/dashboard/store-select";
import { forecastInsight } from "@/lib/insights";
import { generateNarrative, getForecast, getNarrative, type ForecastsResponse, type NarrativeResponse } from "@/lib/api";
import { chartColor } from "@/lib/chart-theme";

type Result = { key: string; forecast: ForecastsResponse | null; narrative: NarrativeResponse | null };

const dateFmt = new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" });

export function StoreForecastSection({ stores }: { stores: string[] }) {
  const [storeId, setStoreId] = useState(stores[0] ?? "");
  const [result, setResult] = useState<Result | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const loading = result?.key !== storeId;
  const forecast = loading ? null : (result?.forecast ?? null);
  const narrative = loading ? null : (result?.narrative ?? null);

  useEffect(() => {
    if (!storeId) return;
    let cancelled = false;
    Promise.all([getForecast(storeId).catch(() => null), getNarrative(storeId).catch(() => null)]).then(([f, n]) => {
      if (cancelled) return;
      setResult({ key: storeId, forecast: f, narrative: n });
    });
    return () => {
      cancelled = true;
    };
  }, [storeId]);

  async function handleGenerate() {
    setGenerating(true);
    setGenerateError(null);
    try {
      const fresh = await generateNarrative(storeId);
      setResult({ key: storeId, forecast, narrative: fresh });
    } catch (err) {
      setGenerateError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h2 className="text-base font-medium text-neutral-200">30-day demand forecast</h2>
          <StoreSelect stores={stores} value={storeId} onChange={setStoreId} label="Store" />
        </div>
        <div className="mt-4">
          {loading && <p className="text-sm text-neutral-500">Loading…</p>}
          {!loading && forecast && forecast.forecasts.length > 0 ? (
            <LineChart
              series={[
                {
                  id: storeId,
                  label: storeId,
                  color: chartColor.categorical[0],
                  data: forecast.forecasts.map((f) => ({
                    x: new Date(f.forecast_date),
                    y: f.forecast_units,
                    ciLower: f.ci_lower,
                    ciUpper: f.ci_upper,
                  })),
                },
              ]}
            />
          ) : (
            !loading && <p className="text-sm text-neutral-500">No forecast found for {storeId || "this store"}.</p>
          )}
        </div>
        {forecastInsight(forecast) && <Insight>{forecastInsight(forecast)}</Insight>}
      </LiquidGlassCard>

      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-base font-medium text-neutral-200">AI executive summary</h2>
          <button
            onClick={handleGenerate}
            disabled={generating || !storeId}
            className="inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2.5 text-sm font-medium text-black transition-colors hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="size-3.5" aria-hidden />
            {generating ? "Generating via Ollama…" : "Generate AI analysis"}
          </button>
        </div>

        <p className="mt-3 text-base leading-relaxed text-neutral-200">
          {loading ? "Loading…" : (narrative?.summary ?? `No narrative generated yet for ${storeId || "this store"}.`)}
        </p>
        {!loading && narrative?.generated_at && (
          <p className="mt-3 text-xs text-neutral-500">Generated {dateFmt.format(new Date(narrative.generated_at))}</p>
        )}
        {narrative?.retrieved_sources && <RagBadge sources={narrative.retrieved_sources} />}
        {generateError && <p className="mt-3 text-xs text-red-400">{generateError}</p>}
      </LiquidGlassCard>
    </div>
  );
}
