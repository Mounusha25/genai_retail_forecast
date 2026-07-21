import {
  SiApachespark,
  SiDocker,
  SiD3,
  SiFastapi,
  SiGooglebigquery,
  SiLangchain,
  SiNextdotjs,
  SiPostgresql,
  SiPydantic,
  SiPython,
  SiSqlalchemy,
  SiTailwindcss,
  SiTypescript,
} from "react-icons/si";
import { LiquidGlassCard } from "@/components/liquid-glass-card";

const STACK = [
  { name: "Python", Icon: SiPython },
  { name: "FastAPI", Icon: SiFastapi },
  { name: "Pydantic", Icon: SiPydantic },
  { name: "PostgreSQL", Icon: SiPostgresql },
  { name: "SQLAlchemy", Icon: SiSqlalchemy },
  { name: "Apache Spark", Icon: SiApachespark },
  { name: "BigQuery ML", Icon: SiGooglebigquery },
  { name: "LangChain", Icon: SiLangchain },
  { name: "Docker", Icon: SiDocker },
  { name: "Next.js", Icon: SiNextdotjs },
  { name: "TypeScript", Icon: SiTypescript },
  { name: "Tailwind CSS", Icon: SiTailwindcss },
  { name: "D3.js", Icon: SiD3 },
];

export function TechStack() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-12 sm:px-10 md:py-16">
      <h2 className="text-center text-2xl font-semibold text-white sm:text-3xl">Built with</h2>
      <p className="mt-2 text-center text-sm text-neutral-400">The real stack behind the pipeline, not a toy demo.</p>

      <LiquidGlassCard className="mt-8 px-6 py-8 sm:px-10">
        <div className="grid grid-cols-3 gap-x-6 gap-y-8 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-7">
          {STACK.map(({ name, Icon }) => (
            <div key={name} className="group flex flex-col items-center gap-2 text-center">
              <div className="flex size-12 items-center justify-center rounded-xl border border-transparent transition-all duration-300 group-hover:border-white/15 group-hover:bg-white/5">
                <Icon className="size-7 text-neutral-400 transition-colors duration-300 group-hover:text-white" aria-hidden />
              </div>
              <span className="text-xs text-neutral-400 transition-colors duration-300 group-hover:text-neutral-200">{name}</span>
            </div>
          ))}
        </div>
      </LiquidGlassCard>
    </section>
  );
}
