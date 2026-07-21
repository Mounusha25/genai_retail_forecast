import { Trophy } from "lucide-react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { Insight } from "@/components/dashboard/insight";
import { baselineInsight } from "@/lib/insights";
import type { BaselineMetricsResponse } from "@/lib/api";

const numberFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

const MODEL_LABELS: Record<string, string> = {
  local_seasonal_trend: "Seasonal + Trend",
  seasonal_naive_7d: "Naive (7-day)",
  moving_average_28d: "Moving Avg (28d)",
  moving_average_7d: "Moving Avg (7d)",
};

function displayName(model: string): string {
  return MODEL_LABELS[model] ?? model;
}

export function BenchmarksSection({ baselineMetrics }: { baselineMetrics: BaselineMetricsResponse | null }) {
  const metrics = [...(baselineMetrics?.metrics ?? [])].sort((a, b) => a.mae - b.mae);
  const maxMae = Math.max(...metrics.map((m) => m.mae), 1);

  return (
    <div className="flex flex-col gap-6">
      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-base font-medium text-neutral-200">Local baseline comparison</h2>
          <span className="text-xs text-neutral-500">Mean absolute error — shorter bar is better</span>
        </div>

        {metrics.length > 0 ? (
          <div className="mt-6 flex flex-col gap-5">
            {metrics.map((m, i) => {
              const isWinner = i === 0;
              return (
                <div
                  key={m.model}
                  className="group rounded-xl border border-transparent px-3 py-2 transition-colors hover:border-white/10 hover:bg-white/5"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                    <div className="flex items-baseline gap-2">
                      <span className={`text-sm font-medium ${isWinner ? "text-white" : "text-neutral-300"}`}>
                        {displayName(m.model)}
                      </span>
                      {isWinner && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/15 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                          <Trophy className="size-3" aria-hidden />
                          Best
                        </span>
                      )}
                      <span className="text-xs text-neutral-500">{m.model}</span>
                    </div>
                    <div className="flex gap-3 text-xs text-neutral-400">
                      <span>MAE {numberFmt.format(m.mae)}</span>
                      <span>MAPE {m.mape_pct.toFixed(1)}%</span>
                      <span>RMSE {numberFmt.format(m.rmse)}</span>
                      <span>Bias {m.bias_pct >= 0 ? "+" : ""}{m.bias_pct.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/5">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${isWinner ? "bg-emerald-400" : "bg-white/25 group-hover:bg-white/40"}`}
                      style={{ width: `${(m.mae / maxMae) * 100}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="mt-4 text-sm text-neutral-500">No baseline metrics available.</p>
        )}
        {baselineInsight(baselineMetrics) && <Insight>{baselineInsight(baselineMetrics)}</Insight>}
      </LiquidGlassCard>

      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <h2 className="text-base font-medium text-neutral-200">Metric detail</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead>
              <tr className="text-neutral-400">
                <th className="pb-2 font-normal">Model</th>
                <th className="pb-2 font-normal">MAE</th>
                <th className="pb-2 font-normal">RMSE</th>
                <th className="pb-2 font-normal">MAPE %</th>
                <th className="pb-2 font-normal">Bias %</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m) => (
                <tr key={m.model} className="border-t border-white/10 text-neutral-200">
                  <td className="py-2">
                    <div>{displayName(m.model)}</div>
                    <div className="text-xs text-neutral-500">{m.model}</div>
                  </td>
                  <td className="py-2">{numberFmt.format(m.mae)}</td>
                  <td className="py-2">{numberFmt.format(m.rmse)}</td>
                  <td className="py-2">{numberFmt.format(m.mape_pct)}</td>
                  <td className="py-2">{numberFmt.format(m.bias_pct)}</td>
                </tr>
              ))}
              {metrics.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-2 text-neutral-500">
                    No data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </LiquidGlassCard>
    </div>
  );
}
