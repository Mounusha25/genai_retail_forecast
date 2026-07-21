import type { FleetSummaryResponse } from "@/lib/api";

export type StoreTier = "High" | "Mid" | "Low";

export type TieredStore = {
  product_id: string;
  total_30d: number;
  avg_ci_width: number | null;
  tier: StoreTier;
};

// Percentile-based split by 30-day volume: top 5% High, next 45% Mid, bottom 50% Low.
export function computeStoreTiers(fleetSummary: FleetSummaryResponse | null): TieredStore[] {
  if (!fleetSummary || fleetSummary.stores.length === 0) return [];

  const sorted = [...fleetSummary.stores].sort((a, b) => b.total_30d - a.total_30d);
  const n = sorted.length;
  const highCut = Math.max(1, Math.round(n * 0.05));
  const midCut = Math.max(highCut + 1, Math.round(n * 0.5));

  return sorted.map((s, i) => ({
    product_id: s.product_id,
    total_30d: s.total_30d,
    avg_ci_width: s.avg_ci_width,
    tier: i < highCut ? "High" : i < midCut ? "Mid" : "Low",
  }));
}

export function tierCounts(tiered: TieredStore[]): { tier: StoreTier; count: number }[] {
  const counts: Record<StoreTier, number> = { High: 0, Mid: 0, Low: 0 };
  for (const s of tiered) counts[s.tier]++;
  return (["High", "Mid", "Low"] as StoreTier[]).map((tier) => ({ tier, count: counts[tier] }));
}
