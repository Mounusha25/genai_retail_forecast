import Link from "next/link";
import { LiquidGlassCard } from "@/components/liquid-glass-card";
import { SplineScene } from "@/components/landing/spline-scene";
import { AmbientBackground } from "@/components/landing/ambient-background";
import { HowItWorks } from "@/components/landing/how-it-works";
import { Results } from "@/components/landing/results";
import { Features } from "@/components/landing/features";
import { TechStack } from "@/components/landing/tech-stack";
import { About } from "@/components/landing/about";
import { Contact } from "@/components/landing/contact";
import { Footer } from "@/components/landing/footer";

export default function Home() {
  return (
    <div className="relative flex flex-1 flex-col bg-neutral-950">
      <AmbientBackground />

      <div className="relative z-10 flex flex-col lg:w-1/2">
        <div className="relative flex min-h-[70vh] flex-col justify-center px-6 py-16 sm:px-10 lg:min-h-screen lg:py-24">
          <span className="mb-6 inline-flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-300">
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-1.5 rounded-full bg-emerald-400" />
            </span>
            Live pipeline · real Rossmann dataset
          </span>

          <LiquidGlassCard className="w-full px-8 py-10 sm:px-10 sm:py-12">
            <p className="text-xs font-medium tracking-wide text-neutral-400 uppercase">Retail demand forecasting</p>
            <h1 className="mt-3 bg-gradient-to-r from-white via-white to-neutral-400 bg-clip-text text-4xl font-semibold text-transparent sm:text-5xl">
              RetailForecastAI
            </h1>
            <p className="mt-4 text-base leading-relaxed text-neutral-300">
              30-day demand forecasts and AI-generated executive summaries for 1,115 Rossmann
              stores — powered by BigQuery ML ARIMA_PLUS, PySpark feature engineering, and a
              FastAPI backend.
            </p>

            <div className="mt-8 grid grid-cols-3 divide-x divide-white/10 border-y border-white/10 py-5">
              <div className="px-2 text-center first:pl-0 last:pr-0">
                <p className="text-2xl font-semibold text-white">1,115</p>
                <p className="mt-1 text-xs text-neutral-500">Stores forecasted</p>
              </div>
              <div className="px-2 text-center first:pl-0 last:pr-0">
                <p className="text-2xl font-semibold text-white">30-day</p>
                <p className="mt-1 text-xs text-neutral-500">Forecast horizon</p>
              </div>
              <div className="px-2 text-center first:pl-0 last:pr-0">
                <p className="text-2xl font-semibold text-white">80%</p>
                <p className="mt-1 text-xs text-neutral-500">Confidence interval</p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="rounded-full bg-white px-6 py-3 text-sm font-medium text-black transition-colors hover:bg-neutral-200"
              >
                Open dashboard
              </Link>
              <a
                href="https://github.com/Brijesh03032001/RetailForecastAI"
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5"
              >
                View on GitHub
              </a>
            </div>
          </LiquidGlassCard>

          <div className="mt-10 hidden items-center gap-2 text-xs text-neutral-500 lg:flex">
            <span className="h-8 w-px animate-pulse bg-gradient-to-b from-transparent via-white/30 to-transparent" />
            Scroll to explore
          </div>
        </div>

        {/* Spline scene: in-flow on mobile, fixed to the right half from lg up */}
        <div className="relative z-10 h-[50vh] w-full lg:fixed lg:inset-y-0 lg:right-0 lg:h-full lg:w-1/2">
          <SplineScene scene="/scene.splinecode" className="h-full w-full" />
        </div>

        <div id="how-it-works">
          <HowItWorks />
        </div>
        <div id="results">
          <Results />
        </div>
        <div id="features">
          <Features />
        </div>
        <div id="stack">
          <TechStack />
        </div>
        <div id="about">
          <About />
        </div>
        <Contact />
        <Footer />
      </div>
    </div>
  );
}
