"use client";

import { BookOpenCheck, Calendar, Maximize2, Store, Trophy, TrendingUp } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useState } from "react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { LineChart } from "@/components/charts/line-chart";
import { BarChart } from "@/components/charts/bar-chart";
import { DonutChart } from "@/components/charts/donut-chart";
import { ScatterChart } from "@/components/charts/scatter-chart";
import { Insight } from "@/components/dashboard/insight";
import { ChartModal } from "@/components/dashboard/chart-modal";
import { chartColor } from "@/lib/chart-theme";
import { dailyTrendInsight, dowInsight, peakDay, tierInsight, topStoreInsight, uncertaintyInsight } from "@/lib/insights";
import { computeStoreTiers, tierCounts } from "@/lib/tiers";
import type {
  BaselineMetricsResponse,
  DailyTrendResponse,
  DayOfWeekPatternResponse,
  FleetSummaryResponse,
  NarrativeCoverageResponse,
} from "@/lib/api";

const numberFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const pctFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

const TIER_COLORS: Record<string, string> = {
  High: chartColor.categorical[5], // red — hottest/most valuable
  Mid: chartColor.categorical[2], // yellow
  Low: chartColor.categorical[1], // aqua
};

type ChartId = "tier" | "uncertainty" | "trend" | "topStores" | "dow";

const CHART_TITLES: Record<ChartId, string> = {
  tier: "Store tier distribution",
  uncertainty: "Volume vs. forecast uncertainty",
  trend: "Fleet daily forecast trend",
  topStores: "Top stores by 30-day forecast",
  dow: "Day-of-week demand pattern",
};

function ExpandButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Expand chart"
      className="rounded-md p-1 text-neutral-500 opacity-0 transition-opacity hover:bg-white/10 hover:text-white group-hover:opacity-100"
    >
      <Maximize2 className="size-3.5" />
    </button>
  );
}

function StatTile({
  icon: Icon,
  color,
  label,
  value,
  sub,
}: {
  icon: LucideIcon;
  color: string;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-4 py-3.5">
      <div className="flex items-center gap-2.5">
        <div className="flex size-7 shrink-0 items-center justify-center rounded-md" style={{ backgroundColor: `${color}26` }}>
          <Icon className="size-3.5" style={{ color }} aria-hidden />
        </div>
        <p className="truncate text-xs text-neutral-400">{label}</p>
      </div>
      <p className="mt-2 truncate text-xl font-semibold text-white">{value}</p>
      {sub && <p className="truncate text-[11px] text-neutral-500">{sub}</p>}
    </LiquidGlassCard>
  );
}

export function OverviewSection({
  fleetSummary,
  dailyTrend,
  dowPattern,
  narrativeCoverage,
  baselineMetrics,
}: {
  fleetSummary: FleetSummaryResponse | null;
  dailyTrend: DailyTrendResponse | null;
  dowPattern: DayOfWeekPatternResponse | null;
  narrativeCoverage: NarrativeCoverageResponse | null;
  baselineMetrics: BaselineMetricsResponse | null;
}) {
  const topStores = fleetSummary?.stores.slice(0, 6) ?? [];
  const topStore = fleetSummary?.stores[0] ?? null;
  const busiest = peakDay(dowPattern);
  const bestBaseline = baselineMetrics?.metrics.length
    ? [...baselineMetrics.metrics].sort((a, b) => a.mae - b.mae)[0]
    : null;

  const tiered = computeStoreTiers(fleetSummary);
  const counts = tierCounts(tiered);
  const donutData = counts.map((c) => ({ label: c.tier, value: c.count, color: TIER_COLORS[c.tier] }));

  const scatterData = tiered
    .filter((s) => s.avg_ci_width != null)
    .map((s) => ({ label: s.product_id, x: s.total_30d, y: s.avg_ci_width as number, category: s.tier }));

  const [expanded, setExpanded] = useState<ChartId | null>(null);

  return (
    <div className="flex flex-col gap-3">
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
        <StatTile
          icon={Store}
          color={chartColor.categorical[0]}
          label="Stores forecasted"
          value={fleetSummary ? numberFmt.format(fleetSummary.count) : "—"}
        />
        <StatTile
          icon={Trophy}
          color={chartColor.categorical[5]}
          label="Top store (30d)"
          value={topStore?.product_id ?? "—"}
          sub={topStore ? `${numberFmt.format(topStore.total_30d)} units` : undefined}
        />
        <StatTile
          icon={Calendar}
          color={chartColor.categorical[2]}
          label="Busiest weekday"
          value={busiest?.day_abbr ?? "—"}
          sub={busiest ? `${numberFmt.format(busiest.avg_units)} avg units/store` : undefined}
        />
        <StatTile
          icon={BookOpenCheck}
          color={chartColor.categorical[4]}
          label="Narrative coverage"
          value={narrativeCoverage ? `${pctFmt.format(narrativeCoverage.coverage_pct)}%` : "—"}
          sub={narrativeCoverage ? `${narrativeCoverage.stores_with_narratives} / ${narrativeCoverage.total_stores} stores` : undefined}
        />
        <StatTile
          icon={TrendingUp}
          color={chartColor.categorical[1]}
          label="Best local baseline"
          value={bestBaseline?.model ?? "—"}
          sub={bestBaseline ? `MAE ${numberFmt.format(bestBaseline.mae)}` : undefined}
        />
      </section>

      <section className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        <LiquidGlassCard className="liquid-glass-interactive group min-w-0 px-4 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-neutral-300">{CHART_TITLES.tier}</h2>
            {donutData.length > 0 && <ExpandButton onClick={() => setExpanded("tier")} />}
          </div>
          <div className="mt-2">
            {donutData.length > 0 ? (
              <DonutChart data={donutData} compact />
            ) : (
              <p className="text-sm text-neutral-500">No data available.</p>
            )}
          </div>
          {donutData.length > 0 && (
            <Insight compact>{tierInsight(counts[0].count, counts[1].count, counts[2].count, tiered.length)}</Insight>
          )}
        </LiquidGlassCard>

        <LiquidGlassCard className="liquid-glass-interactive group min-w-0 px-4 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-neutral-300">{CHART_TITLES.uncertainty}</h2>
            {scatterData.length > 0 && <ExpandButton onClick={() => setExpanded("uncertainty")} />}
          </div>
          <div className="mt-2">
            {scatterData.length > 0 ? (
              <ScatterChart
                height={140}
                data={scatterData}
                categoryColors={TIER_COLORS}
                xLabel="30-day volume (units)"
                yLabel="Avg CI width (units)"
              />
            ) : (
              <p className="text-sm text-neutral-500">No data available.</p>
            )}
          </div>
          {uncertaintyInsight(fleetSummary) && <Insight compact>{uncertaintyInsight(fleetSummary)}</Insight>}
        </LiquidGlassCard>
      </section>

      <section className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <LiquidGlassCard className="liquid-glass-interactive group min-w-0 px-4 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-neutral-300">{CHART_TITLES.trend}</h2>
            {dailyTrend && dailyTrend.days.length > 0 && <ExpandButton onClick={() => setExpanded("trend")} />}
          </div>
          <div className="mt-2">
            {dailyTrend && dailyTrend.days.length > 0 ? (
              <LineChart
                height={130}
                series={[
                  {
                    id: "total_units",
                    label: "Total units",
                    color: chartColor.categorical[0],
                    data: dailyTrend.days.map((d) => ({ x: new Date(d.forecast_date), y: d.total_units })),
                  },
                ]}
              />
            ) : (
              <p className="text-sm text-neutral-500">No data available.</p>
            )}
          </div>
          {dailyTrendInsight(dailyTrend) && <Insight compact>{dailyTrendInsight(dailyTrend)}</Insight>}
        </LiquidGlassCard>

        <LiquidGlassCard className="liquid-glass-interactive group min-w-0 px-4 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-neutral-300">{CHART_TITLES.topStores}</h2>
            {topStores.length > 0 && <ExpandButton onClick={() => setExpanded("topStores")} />}
          </div>
          <div className="mt-2">
            {topStores.length > 0 ? (
              <BarChart height={130} data={topStores.map((s) => ({ label: s.product_id, value: s.total_30d }))} />
            ) : (
              <p className="text-sm text-neutral-500">No data available.</p>
            )}
          </div>
          {topStoreInsight(fleetSummary) && <Insight compact>{topStoreInsight(fleetSummary)}</Insight>}
        </LiquidGlassCard>

        <LiquidGlassCard className="liquid-glass-interactive group min-w-0 px-4 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-medium text-neutral-300">{CHART_TITLES.dow}</h2>
            {dowPattern && dowPattern.days.length > 0 && <ExpandButton onClick={() => setExpanded("dow")} />}
          </div>
          <div className="mt-2">
            {dowPattern && dowPattern.days.length > 0 ? (
              <BarChart
                height={130}
                data={dowPattern.days.map((d) => ({ label: d.day_abbr, value: d.avg_units }))}
                color={chartColor.categorical[1]}
              />
            ) : (
              <p className="text-sm text-neutral-500">No data available.</p>
            )}
          </div>
          {dowInsight(dowPattern) && <Insight compact>{dowInsight(dowPattern)}</Insight>}
        </LiquidGlassCard>
      </section>

      {expanded && (
        <ChartModal title={CHART_TITLES[expanded]} onClose={() => setExpanded(null)}>
          {expanded === "tier" && (
            <>
              <DonutChart data={donutData} />
              <Insight>{tierInsight(counts[0].count, counts[1].count, counts[2].count, tiered.length)}</Insight>
            </>
          )}
          {expanded === "uncertainty" && (
            <>
              <ScatterChart
                height={380}
                data={scatterData}
                categoryColors={TIER_COLORS}
                xLabel="30-day volume (units)"
                yLabel="Avg CI width (units)"
              />
              {uncertaintyInsight(fleetSummary) && <Insight>{uncertaintyInsight(fleetSummary)}</Insight>}
            </>
          )}
          {expanded === "trend" && dailyTrend && (
            <>
              <LineChart
                height={380}
                series={[
                  {
                    id: "total_units",
                    label: "Total units",
                    color: chartColor.categorical[0],
                    data: dailyTrend.days.map((d) => ({ x: new Date(d.forecast_date), y: d.total_units })),
                  },
                ]}
              />
              {dailyTrendInsight(dailyTrend) && <Insight>{dailyTrendInsight(dailyTrend)}</Insight>}
            </>
          )}
          {expanded === "topStores" && (
            <>
              <BarChart height={380} data={topStores.map((s) => ({ label: s.product_id, value: s.total_30d }))} />
              {topStoreInsight(fleetSummary) && <Insight>{topStoreInsight(fleetSummary)}</Insight>}
            </>
          )}
          {expanded === "dow" && dowPattern && (
            <>
              <BarChart
                height={380}
                data={dowPattern.days.map((d) => ({ label: d.day_abbr, value: d.avg_units }))}
                color={chartColor.categorical[1]}
              />
              {dowInsight(dowPattern) && <Insight>{dowInsight(dowPattern)}</Insight>}
            </>
          )}
        </ChartModal>
      )}
    </div>
  );
}
