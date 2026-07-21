import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { AmbientBackground } from "@/components/landing/ambient-background";
import {
  getBaselineMetrics,
  getDailyTrend,
  getDowPattern,
  getFleetSummary,
  getNarrativeCoverage,
  getStores,
  type BaselineMetricsResponse,
  type DailyTrendResponse,
  type DayOfWeekPatternResponse,
  type FleetSummaryResponse,
  type NarrativeCoverageResponse,
  type StoreListResponse,
} from "@/lib/api";

async function settle<T>(promise: Promise<T>): Promise<T | null> {
  try {
    return await promise;
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const [stores, fleetSummary, dailyTrend, dowPattern, narrativeCoverage, baselineMetrics] = await Promise.all([
    settle<StoreListResponse>(getStores()),
    settle<FleetSummaryResponse>(getFleetSummary()),
    settle<DailyTrendResponse>(getDailyTrend()),
    settle<DayOfWeekPatternResponse>(getDowPattern()),
    settle<NarrativeCoverageResponse>(getNarrativeCoverage()),
    settle<BaselineMetricsResponse>(getBaselineMetrics()),
  ]);

  return (
    <div className="relative flex-1 bg-neutral-950">
      <AmbientBackground />
      <div className="relative z-10">
        <DashboardShell
          stores={stores?.stores ?? []}
          fleetSummary={fleetSummary}
          dailyTrend={dailyTrend}
          dowPattern={dowPattern}
          narrativeCoverage={narrativeCoverage}
          baselineMetrics={baselineMetrics}
        />
      </div>
    </div>
  );
}
