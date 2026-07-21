"use client";

import { useEffect, useState } from "react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { LineChart, type LineSeries } from "@/components/charts/line-chart";
import { Insight } from "@/components/dashboard/insight";
import { StoreSelect } from "@/components/dashboard/store-select";
import { compareInsight } from "@/lib/insights";
import { getForecast } from "@/lib/api";
import { chartColor } from "@/lib/chart-theme";

type Result = { key: string; series: LineSeries[]; totalA: number | null; totalB: number | null };

export function CompareSection({ stores }: { stores: string[] }) {
  const [storeA, setStoreA] = useState(stores[0] ?? "");
  const [storeB, setStoreB] = useState(stores[1] ?? stores[0] ?? "");
  const [result, setResult] = useState<Result | null>(null);
  const key = `${storeA}|${storeB}`;
  const loading = result?.key !== key;
  const series = loading ? [] : (result?.series ?? []);

  useEffect(() => {
    if (!storeA || !storeB) return;
    let cancelled = false;
    Promise.all([getForecast(storeA).catch(() => null), getForecast(storeB).catch(() => null)]).then(([a, b]) => {
      if (cancelled) return;
      const next: LineSeries[] = [];
      if (a) {
        next.push({
          id: storeA,
          label: storeA,
          color: chartColor.categorical[0],
          data: a.forecasts.map((f) => ({ x: new Date(f.forecast_date), y: f.forecast_units })),
        });
      }
      if (b && storeB !== storeA) {
        next.push({
          id: storeB,
          label: storeB,
          color: chartColor.categorical[1],
          data: b.forecasts.map((f) => ({ x: new Date(f.forecast_date), y: f.forecast_units })),
        });
      }
      setResult({
        key: `${storeA}|${storeB}`,
        series: next,
        totalA: a ? a.forecasts.reduce((sum, f) => sum + f.forecast_units, 0) : null,
        totalB: b ? b.forecasts.reduce((sum, f) => sum + f.forecast_units, 0) : null,
      });
    });
    return () => {
      cancelled = true;
    };
  }, [storeA, storeB, key]);

  return (
    <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-base font-medium text-neutral-200">Compare forecasts</h2>
        <div className="flex flex-wrap gap-3">
          <StoreSelect stores={stores} value={storeA} onChange={setStoreA} label="Store A" />
          <StoreSelect stores={stores} value={storeB} onChange={setStoreB} label="Store B" />
        </div>
      </div>
      <div className="mt-4">
        {loading && <p className="text-sm text-neutral-500">Loading…</p>}
        {!loading && series.length > 0 ? <LineChart series={series} /> : !loading && <p className="text-sm text-neutral-500">No data available.</p>}
      </div>
      {!loading && compareInsight(storeA, result?.totalA ?? null, storeB, result?.totalB ?? null) && (
        <Insight>{compareInsight(storeA, result?.totalA ?? null, storeB, result?.totalB ?? null)}</Insight>
      )}
    </LiquidGlassCard>
  );
}
