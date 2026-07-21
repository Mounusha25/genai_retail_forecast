import Link from "next/link";
import { FaGithub, FaLinkedin } from "react-icons/fa6";

const NAV_LINKS = [
  { title: "How it works", href: "#how-it-works" },
  { title: "Results", href: "#results" },
  { title: "Features", href: "#features" },
  { title: "Stack", href: "#stack" },
  { title: "About", href: "#about" },
  { title: "Contact", href: "#contact" },
  { title: "Dashboard", href: "/dashboard" },
];

const SOCIALS = [
  { title: "GitHub", href: "https://github.com/Brijesh03032001/RetailForecastAI", Icon: FaGithub },
  { title: "LinkedIn", href: "https://linkedin.com/in/brijeshkumar03", Icon: FaLinkedin },
];

export function Footer() {
  return (
    <footer className="px-6 pb-6 sm:px-10">
      <div className="liquid-glass liquid-glass-interactive overflow-hidden">
        <div className="liquid-glass-content px-8 py-10 sm:px-12 sm:py-12">
          <div className="grid grid-cols-1 gap-10 sm:grid-cols-[1.3fr_1fr_1fr] sm:gap-8">
            <div>
              <span className="text-lg font-semibold text-white">RetailForecastAI</span>
              <p className="mt-3 max-w-sm text-sm leading-relaxed text-neutral-400">
                30-day ML demand forecasts and AI-generated executive summaries for 1,115
                Rossmann stores — a portfolio-grade, production-shaped MLOps pipeline.
              </p>
              <Link
                href="/dashboard"
                className="mt-5 inline-flex items-center gap-1.5 rounded-full bg-white px-5 py-2.5 text-sm font-medium text-black transition-colors hover:bg-neutral-200"
              >
                Open dashboard
              </Link>
            </div>

            <div>
              <span className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Navigate</span>
              <ul className="mt-4 flex flex-col gap-3">
                {NAV_LINKS.map((link) => (
                  <li key={link.title}>
                    <Link href={link.href} className="text-sm text-neutral-400 transition-colors hover:text-white">
                      {link.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <span className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Connect</span>
              <ul className="mt-4 flex flex-col gap-3">
                {SOCIALS.map(({ title, href, Icon }) => (
                  <li key={title}>
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-sm text-neutral-400 transition-colors hover:text-white"
                    >
                      <Icon className="size-4" aria-hidden />
                      {title}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-10 flex flex-col gap-2 border-t border-white/10 pt-6 text-xs text-neutral-500 sm:flex-row sm:items-center sm:justify-between">
            <span>© {new Date().getFullYear()} Brijesh Kumar. Built with Next.js, FastAPI, and BigQuery ML.</span>
            <span>Real Rossmann dataset · 1,115 stores · not a synthetic demo</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
