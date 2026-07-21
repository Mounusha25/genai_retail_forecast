"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { LiquidGlassCard } from "@/components/liquid-glass-card";

export function ChartModal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm sm:p-8"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-4xl">
        <LiquidGlassCard className="px-6 py-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-neutral-200">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="rounded-md p-1.5 text-neutral-400 transition-colors hover:bg-white/10 hover:text-white"
            >
              <X className="size-4" />
            </button>
          </div>
          <div className="mt-4">{children}</div>
        </LiquidGlassCard>
      </div>
    </div>
  );
}
