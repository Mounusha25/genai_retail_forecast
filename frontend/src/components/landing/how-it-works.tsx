import { BrainCircuit, Database, LineChart, Rows3, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";

const STEPS: { title: string; description: string; icon: LucideIcon }[] = [
  {
    title: "Ingest",
    description: "Apache Beam validates, dedups, and type-coerces raw Rossmann sales data from CSV into BigQuery.",
    icon: Database,
  },
  {
    title: "Engineer features",
    description: "PySpark builds rolling averages, lag features, and calendar signals per store.",
    icon: Rows3,
  },
  {
    title: "Forecast",
    description: "BigQuery ML ARIMA_PLUS trains a per-store model and produces a 30-day forecast with a confidence interval.",
    icon: LineChart,
  },
  {
    title: "Summarize",
    description: "LangChain + FAISS retrieval turns the forecast into a plain-language executive narrative.",
    icon: BrainCircuit,
  },
  {
    title: "Serve",
    description: "FastAPI exposes forecasts, narratives, and fleet analytics; this dashboard renders them live.",
    icon: Sparkles,
  },
];

export function HowItWorks() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-12 sm:px-10 md:py-16">
      <h2 className="text-3xl font-semibold text-white sm:text-4xl">How it works</h2>
      <p className="mt-3 max-w-xl text-neutral-400">Five real pipeline stages, end to end — each one backed by actual code, not a diagram of intent.</p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-5">
        {STEPS.map(({ title, description, icon: Icon }, i) => (
          <LiquidGlassCard key={title} className="liquid-glass-interactive group relative px-5 py-6">
            <span className="text-xs font-medium text-neutral-500">{String(i + 1).padStart(2, "0")}</span>
            <div className="mt-3 flex size-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 transition-transform duration-300 group-hover:scale-110">
              <Icon className="size-5 text-neutral-100" aria-hidden />
            </div>
            <h3 className="mt-4 text-sm font-medium text-white">{title}</h3>
            <p className="mt-2 text-xs leading-relaxed text-neutral-400">{description}</p>
            {i < STEPS.length - 1 && (
              <span className="absolute top-1/2 right-[-18px] hidden -translate-y-1/2 text-neutral-600 sm:block" aria-hidden>
                →
              </span>
            )}
          </LiquidGlassCard>
        ))}
      </div>
    </section>
  );
}
