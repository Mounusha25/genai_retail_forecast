"use client";

import { useState } from "react";
import { Sidebar, SECTIONS, type Section } from "@/components/dashboard/sidebar";
import { OverviewSection } from "@/components/dashboard/overview-section";
import { StoreForecastSection } from "@/components/dashboard/store-forecast-section";
import { CompareSection } from "@/components/dashboard/compare-section";
import { BenchmarksSection } from "@/components/dashboard/benchmarks-section";
import { NarrativeSection } from "@/components/dashboard/narrative-section";
import { AboutSection } from "@/components/dashboard/about-section";
import type {
  BaselineMetricsResponse,
  DailyTrendResponse,
  DayOfWeekPatternResponse,
  FleetSummaryResponse,
  NarrativeCoverageResponse,
} from "@/lib/api";

export function DashboardShell({
  stores,
  fleetSummary,
  dailyTrend,
  dowPattern,
  narrativeCoverage,
  baselineMetrics,
}: {
  stores: string[];
  fleetSummary: FleetSummaryResponse | null;
  dailyTrend: DailyTrendResponse | null;
  dowPattern: DayOfWeekPatternResponse | null;
  narrativeCoverage: NarrativeCoverageResponse | null;
  baselineMetrics: BaselineMetricsResponse | null;
}) {
  const [active, setActive] = useState<Section>(SECTIONS[0]);
  // Sidebar collapse only applies to Overview (dense layout benefits from the space).
  // Every other tab always shows the full sidebar and can't be collapsed.
  const [overviewCollapsed, setOverviewCollapsed] = useState(true);
  const isOverview = active === "Overview";

  return (
    <div className="mx-auto flex w-full max-w-[1800px] flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:gap-6 xl:px-10">
      <Sidebar
        active={active}
        onSelect={setActive}
        coveragePct={narrativeCoverage?.coverage_pct ?? null}
        collapsed={isOverview && overviewCollapsed}
        collapsible={isOverview}
        onToggleCollapsed={() => setOverviewCollapsed((v) => !v)}
      />

      <main className="min-w-0 flex-1">
        <div className="mb-3">
          <p className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Dashboard</p>
          <h1 className="mt-0.5 text-2xl font-semibold text-white">{active}</h1>
        </div>

        {active === "Overview" && (
          <OverviewSection
            fleetSummary={fleetSummary}
            dailyTrend={dailyTrend}
            dowPattern={dowPattern}
            narrativeCoverage={narrativeCoverage}
            baselineMetrics={baselineMetrics}
          />
        )}
        {active === "Store Forecast" && <StoreForecastSection stores={stores} />}
        {active === "Compare" && <CompareSection stores={stores} />}
        {active === "Model Benchmarks" && <BenchmarksSection baselineMetrics={baselineMetrics} />}
        {active === "AI Narrative" && <NarrativeSection stores={stores} />}
        {active === "About" && <AboutSection />}
      </main>
    </div>
  );
}
