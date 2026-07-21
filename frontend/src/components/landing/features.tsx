import { BrainCircuit, Database, LineChart, ServerCog } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";

function StatChip({ label }: { label: string }) {
  return (
    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-300">{label}</span>
  );
}

function FeatureIcon({ icon: Icon }: { icon: LucideIcon }) {
  return (
    <div className="flex size-12 items-center justify-center rounded-xl border border-white/10 bg-gradient-to-br from-white/10 to-white/0 transition-transform duration-300 group-hover:scale-110">
      <Icon className="size-6 text-neutral-100" aria-hidden />
    </div>
  );
}

export function Features() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-12 sm:px-10 md:py-16">
      <div>
        <h2 className="text-3xl font-semibold text-white sm:text-4xl">What this system does</h2>
        <p className="mt-3 max-w-xl text-neutral-400">A real forecasting pipeline, from raw sales data to an AI-written summary — not a notebook demo.</p>
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
        {/* Primary feature — spans full width */}
        <LiquidGlassCard className="liquid-glass-interactive group px-8 py-8 sm:col-span-3 sm:px-10">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-5">
              <FeatureIcon icon={LineChart} />
              <div>
                <h3 className="text-lg font-medium text-white">30-day ML forecasting</h3>
                <p className="mt-2 max-w-md text-sm leading-relaxed text-neutral-400">
                  BigQuery ML ARIMA_PLUS trains a per-store model across every store, forecasting
                  30 days out with a bounded confidence interval on every prediction.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 sm:flex-col sm:items-end">
              <StatChip label="1,115 stores" />
              <StatChip label="80% CI" />
              <StatChip label="ARIMA_PLUS" />
            </div>
          </div>
        </LiquidGlassCard>

        <LiquidGlassCard className="liquid-glass-interactive group px-6 py-8 sm:px-7">
          <FeatureIcon icon={ServerCog} />
          <h3 className="mt-5 font-medium text-white">End-to-end MLOps pipeline</h3>
          <p className="mt-2 text-sm leading-relaxed text-neutral-400">
            Apache Beam ETL, PySpark feature engineering, and an orchestrator that runs
            ingestion through forecasting in one pass.
          </p>
        </LiquidGlassCard>

        <LiquidGlassCard className="liquid-glass-interactive group px-6 py-8 sm:px-7">
          <FeatureIcon icon={BrainCircuit} />
          <h3 className="mt-5 font-medium text-white">AI executive narratives</h3>
          <p className="mt-2 text-sm leading-relaxed text-neutral-400">
            RAG over business docs (LangChain + FAISS) turns raw forecasts into plain-language
            store summaries.
          </p>
        </LiquidGlassCard>

        <LiquidGlassCard className="liquid-glass-interactive group px-6 py-8 sm:px-7">
          <FeatureIcon icon={Database} />
          <h3 className="mt-5 font-medium text-white">Production-shaped API</h3>
          <p className="mt-2 text-sm leading-relaxed text-neutral-400">
            Async FastAPI over PostgreSQL, tested, containerized, and deployed via CI/CD to
            Cloud Run.
          </p>
        </LiquidGlassCard>
      </div>
    </section>
  );
}
