import type { ReactNode } from "react";

export function LiquidGlassCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`liquid-glass ${className}`}>
      <span aria-hidden className="lg-blur lg-blur-1" />
      <span aria-hidden className="lg-blur lg-blur-2" />
      <span aria-hidden className="lg-blur lg-blur-3" />
      <div className="liquid-glass-content">{children}</div>
    </div>
  );
}
