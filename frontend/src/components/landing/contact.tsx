import { Mail } from "lucide-react";
import { FaGithub, FaLinkedin } from "react-icons/fa6";
import { LiquidGlassCard } from "@/components/liquid-glass-card";

const EMAIL = "bkumar25@asu.edu";

export function Contact() {
  return (
    <section id="contact" className="mx-auto w-full max-w-5xl px-6 py-12 sm:px-10 md:py-16">
      <LiquidGlassCard className="liquid-glass-interactive px-8 py-10 text-center sm:px-12 sm:py-14">
        <h2 className="text-2xl font-semibold text-white sm:text-3xl">Questions about the approach?</h2>
        <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-neutral-400">
          Happy to walk through a design decision, the data pipeline, or the model choices behind
          RetailForecastAI.
        </p>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <a
            href={`mailto:${EMAIL}`}
            className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-medium text-black transition-colors hover:bg-neutral-200"
          >
            <Mail className="size-4" aria-hidden />
            {EMAIL}
          </a>
          <a
            href="https://github.com/Brijesh03032001/RetailForecastAI"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5"
          >
            <FaGithub className="size-4" aria-hidden />
            GitHub
          </a>
          <a
            href="https://linkedin.com/in/brijeshkumar03"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5"
          >
            <FaLinkedin className="size-4" aria-hidden />
            LinkedIn
          </a>
        </div>
      </LiquidGlassCard>
    </section>
  );
}
