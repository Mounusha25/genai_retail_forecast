import { Mail } from "lucide-react";
import {
  SiApachespark,
  SiD3,
  SiDocker,
  SiFastapi,
  SiGithubactions,
  SiGooglebigquery,
  SiLangchain,
  SiNextdotjs,
  SiOllama,
  SiPandas,
  SiPostgresql,
  SiPydantic,
  SiPython,
  SiPytest,
  SiSqlalchemy,
  SiTailwindcss,
  SiTypescript,
} from "react-icons/si";
import { FaGithub, FaLinkedin } from "react-icons/fa6";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { SplineScene } from "@/components/landing/spline-scene";

const STACK = [
  { name: "Python", Icon: SiPython },
  { name: "FastAPI", Icon: SiFastapi },
  { name: "Pydantic", Icon: SiPydantic },
  { name: "Pandas", Icon: SiPandas },
  { name: "PostgreSQL", Icon: SiPostgresql },
  { name: "SQLAlchemy", Icon: SiSqlalchemy },
  { name: "Apache Spark", Icon: SiApachespark },
  { name: "BigQuery ML", Icon: SiGooglebigquery },
  { name: "LangChain", Icon: SiLangchain },
  { name: "Ollama", Icon: SiOllama },
  { name: "pytest", Icon: SiPytest },
  { name: "Docker", Icon: SiDocker },
  { name: "GitHub Actions", Icon: SiGithubactions },
  { name: "Next.js", Icon: SiNextdotjs },
  { name: "TypeScript", Icon: SiTypescript },
  { name: "Tailwind CSS", Icon: SiTailwindcss },
  { name: "D3.js", Icon: SiD3 },
];

const PIPELINE = [
  { name: "ETL", detail: "Apache Beam — CSV → GCS → BigQuery, validation/dedup/type-coercion" },
  { name: "Feature engineering", detail: "PySpark rolling averages, lag features, calendar signals" },
  { name: "Forecasting", detail: "BigQuery ML ARIMA_PLUS — per-store model, 30-day horizon, 80% CI" },
  { name: "Database", detail: "PostgreSQL via SQLAlchemy async + Alembic migrations" },
  { name: "API", detail: "FastAPI — forecasts, narratives, dashboard analytics, pipeline runs" },
  { name: "RAG narratives", detail: "LangChain + FAISS retrieval over business docs, served by a local Ollama LLM" },
  { name: "CI/CD", detail: "GitHub Actions — lint, type-check, test on push; semver-tag deploy to Cloud Run" },
];

export function AboutSection() {
  return (
    <div className="flex flex-col gap-6">
      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <h2 className="text-base font-medium text-neutral-200">About RetailForecastAI</h2>
        <p className="mt-3 text-base leading-relaxed text-neutral-300">
          End-to-end retail demand forecasting system built on the Rossmann Store Sales dataset —
          1,115 real German stores. Portfolio-grade MLOps pipeline spanning ETL, feature
          engineering, BigQuery ML forecasting, and AI-assisted executive summaries, served through
          this dashboard via a FastAPI backend.
        </p>
      </LiquidGlassCard>

      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <h2 className="text-base font-medium text-neutral-200">Pipeline</h2>
        <ul className="mt-4 flex flex-col gap-3">
          {PIPELINE.map((item) => (
            <li key={item.name} className="text-sm">
              <span className="font-medium text-white">{item.name}</span>
              <span className="text-neutral-400"> — {item.detail}</span>
            </li>
          ))}
        </ul>
      </LiquidGlassCard>

      <LiquidGlassCard className="liquid-glass-interactive min-w-0 px-6 py-6 sm:px-8 sm:py-8">
        <h2 className="text-base font-medium text-neutral-200">Full stack</h2>
        <div className="mt-6 grid grid-cols-3 gap-x-4 gap-y-6 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-9">
          {STACK.map(({ name, Icon }) => (
            <div key={name} className="group flex flex-col items-center gap-2 text-center">
              <div className="flex size-11 items-center justify-center rounded-xl border border-transparent transition-all duration-300 group-hover:border-white/15 group-hover:bg-white/5">
                <Icon className="size-6 text-neutral-400 transition-colors duration-300 group-hover:text-white" aria-hidden />
              </div>
              <span className="text-xs text-neutral-400 transition-colors duration-300 group-hover:text-neutral-200">{name}</span>
            </div>
          ))}
        </div>
      </LiquidGlassCard>

      <LiquidGlassCard className="liquid-glass-interactive min-w-0 overflow-hidden px-0 py-0">
        <div className="grid grid-cols-1 md:grid-cols-2">
          <div className="flex flex-col justify-center px-8 py-10 sm:px-10">
            <h2 className="text-2xl font-semibold text-white">Let&apos;s collaborate</h2>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-neutral-400">
              Built this end to end — data engineering, ML forecasting, RAG, and the full-stack
              dashboard you&apos;re looking at. Open to talking through any of it.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a
                href="mailto:bkumar25@asu.edu"
                className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-medium text-black transition-colors hover:bg-neutral-200"
              >
                <Mail className="size-4" aria-hidden />
                bkumar25@asu.edu
              </a>
              <a
                href="https://github.com/Brijesh03032001/RetailForecastAI"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-white/5"
              >
                <FaGithub className="size-4" aria-hidden />
                GitHub
              </a>
              <a
                href="https://linkedin.com/in/brijeshkumar03"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-white/5"
              >
                <FaLinkedin className="size-4" aria-hidden />
                LinkedIn
              </a>
            </div>
          </div>
          <div className="h-72 md:h-full">
            <SplineScene scene="/bye.splinecode" className="h-full w-full" />
          </div>
        </div>
      </LiquidGlassCard>
    </div>
  );
}
