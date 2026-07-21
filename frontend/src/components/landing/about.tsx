import { LiquidGlassCard } from "@/components/liquid-glass-card";

const SKILLS = [
  "Data engineering (ETL, Beam)",
  "Feature engineering (PySpark)",
  "ML forecasting (BigQuery ML)",
  "Retrieval-augmented generation",
  "Backend API design (FastAPI)",
  "Full-stack product (Next.js)",
];

export function About() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-12 sm:px-10 md:py-16">
      <LiquidGlassCard className="liquid-glass-interactive px-8 py-10 sm:px-12 sm:py-12">
        <p className="text-xs font-medium tracking-wide text-neutral-400 uppercase">About the builder</p>
        <h2 className="mt-3 text-2xl font-semibold text-white sm:text-3xl">Brijesh Kumar — M.S. Computer Science, Arizona State University</h2>
        <p className="mt-4 max-w-2xl text-base leading-relaxed text-neutral-300">
          I built RetailForecastAI to go past course-project scope and ship a complete,
          production-shaped ML system end to end — real retail data in, a trained forecasting
          model, and an AI-generated summary a business user could actually read — on the same
          kind of stack (BigQuery ML, PySpark, FastAPI, Next.js) production teams run.
        </p>

        <div className="mt-8 flex flex-wrap gap-2">
          {SKILLS.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-neutral-300"
            >
              {skill}
            </span>
          ))}
        </div>
      </LiquidGlassCard>
    </section>
  );
}
