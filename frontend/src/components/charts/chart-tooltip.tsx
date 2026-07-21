"use client";

export type TooltipState = {
  x: number;
  y: number;
  title: string;
  rows: { label: string; value: string; color: string }[];
} | null;

export function ChartTooltip({ tooltip }: { tooltip: TooltipState }) {
  if (!tooltip) return null;
  return (
    <div
      className="pointer-events-none absolute z-10 rounded-lg border border-white/10 bg-neutral-900/95 px-3 py-2 text-xs shadow-lg"
      style={{ left: tooltip.x, top: tooltip.y, transform: "translate(-50%, -110%)" }}
    >
      <div className="mb-1 font-medium text-white">{tooltip.title}</div>
      {tooltip.rows.map((row) => (
        <div key={row.label} className="flex items-center gap-2 whitespace-nowrap text-neutral-300">
          <span className="inline-block h-[2px] w-3" style={{ backgroundColor: row.color }} />
          <span className="text-neutral-400">{row.label}</span>
          <span className="ml-auto font-medium text-white">{row.value}</span>
        </div>
      ))}
    </div>
  );
}
