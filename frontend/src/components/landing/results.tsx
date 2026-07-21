import { LiquidGlassCard } from "@/components/liquid-glass-card";

// Real backtest — data/reports/baseline_comparison.md (1,115 stores, 33,450 holdout rows, 2015-07-02 to 2015-07-31)
const BASELINES = [
  { model: "local_seasonal_trend", mae: 1898.84, mape: 16.92, isWinner: true },
  { model: "seasonal_naive_7d", mae: 1936.19, mape: 21.91, isWinner: false },
  { model: "moving_average_28d", mae: 2175.1, mape: 23.03, isWinner: false },
  { model: "moving_average_7d", mae: 2251.98, mape: 24.74, isWinner: false },
];

const maxMae = Math.max(...BASELINES.map((b) => b.mae));

export function Results() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-12 sm:px-10 md:py-16">
      <h2 className="text-3xl font-semibold text-white sm:text-4xl">Backtested, not just built</h2>
      <p className="mt-3 max-w-xl text-neutral-400">
        The forecasting approach is validated against simple baselines on a real holdout window —
        not just assumed to work.
      </p>

      <LiquidGlassCard className="mt-8 px-6 py-8 sm:px-10">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-[auto_1fr]">
          <div className="flex flex-col justify-center border-white/10 sm:border-r sm:pr-10">
            <p className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Best model</p>
            <p className="mt-2 text-4xl font-semibold text-white">16.92%</p>
            <p className="mt-1 text-sm text-neutral-400">MAPE — local seasonal-trend forecaster</p>
            <p className="mt-4 text-xs text-neutral-500">1,115 stores · 33,450 holdout rows · Jul 2015</p>
          </div>

          <div className="flex flex-col justify-center gap-3">
            <p className="text-xs text-neutral-500">Mean absolute error by model — shorter bar is better</p>
            {BASELINES.map((b) => (
              <div key={b.model}>
                <div className="flex items-center justify-between text-xs">
                  <span className={b.isWinner ? "font-medium text-white" : "text-neutral-400"}>
                    {b.model}
                    {b.isWinner && <span className="ml-2 rounded-full bg-emerald-400/15 px-2 py-0.5 text-[10px] text-emerald-300">winner</span>}
                  </span>
                  <span className="text-neutral-400">MAE {b.mae.toLocaleString()}</span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-white/5">
                  <div
                    className={`h-full rounded-full ${b.isWinner ? "bg-emerald-400" : "bg-white/25"}`}
                    style={{ width: `${(b.mae / maxMae) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </LiquidGlassCard>
    </section>
  );
}
