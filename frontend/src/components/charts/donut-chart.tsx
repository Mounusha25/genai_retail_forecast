"use client";

import * as d3 from "d3";
import { useRef, useState } from "react";
import { chartColor } from "@/lib/chart-theme";
import { ChartTooltip, type TooltipState } from "./chart-tooltip";

export type DonutDatum = { label: string; value: number; color?: string };

const SIZE = 220;
const RADIUS = SIZE / 2;
const INNER_RADIUS = RADIUS * 0.6;

export function DonutChart({ data, compact = false }: { data: DonutDatum[]; compact?: boolean }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const total = data.reduce((sum, d) => sum + d.value, 0);

  const colored = data.map((d, i) => ({ ...d, color: d.color ?? chartColor.categorical[i % chartColor.categorical.length] }));
  const pie = d3.pie<DonutDatum>().value((d) => d.value).sort(null).padAngle(0.015);
  const arcs = pie(colored);
  const arcGen = d3.arc<d3.PieArcDatum<DonutDatum>>().innerRadius(INNER_RADIUS).outerRadius(RADIUS).cornerRadius(5);

  return (
    <div ref={containerRef} className="relative flex items-center justify-center gap-6">
      <div className="relative shrink-0">
        <div
          className="absolute inset-0 rounded-full opacity-30 blur-2xl"
          style={{ background: `radial-gradient(circle, ${colored[0]?.color ?? chartColor.categorical[0]}, transparent 70%)` }}
          aria-hidden
        />
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className={compact ? "relative w-40 sm:w-48" : "relative w-56"}
          role="img"
          aria-label="Store tier distribution"
        >
          <g transform={`translate(${RADIUS}, ${RADIUS})`}>
            {arcs.map((arc, i) => (
              <path
                key={arc.data.label}
                d={arcGen(arc) ?? undefined}
                fill={colored[i].color}
                opacity={tooltip && tooltip.title !== arc.data.label ? 0.45 : 1}
                className="transition-opacity duration-200"
                onPointerMove={(evt) => {
                  const rect = containerRef.current?.getBoundingClientRect();
                  const x = rect ? evt.clientX - rect.left : RADIUS;
                  const y = rect ? evt.clientY - rect.top : RADIUS;
                  setTooltip({
                    x,
                    y,
                    title: arc.data.label,
                    rows: [
                      { label: "Stores", value: `${arc.data.value}`, color: colored[i].color },
                      { label: "Share", value: `${((arc.data.value / total) * 100).toFixed(1)}%`, color: colored[i].color },
                    ],
                  });
                }}
                onPointerLeave={() => setTooltip(null)}
              />
            ))}
            <text textAnchor="middle" dy="-0.15em" fontSize={30} fontWeight={600} fill={chartColor.primaryInk}>
              {total}
            </text>
            <text textAnchor="middle" dy="1.5em" fontSize={12} fill={chartColor.mutedInk}>
              stores
            </text>
          </g>
        </svg>
      </div>

      <div className="flex flex-col justify-center gap-3">
        {colored.map((d) => (
          <div key={d.label} className="flex items-center gap-2.5">
            <span className="inline-block size-3 shrink-0 rounded-full" style={{ backgroundColor: d.color }} />
            <div>
              <p className={`font-medium text-neutral-200 ${compact ? "text-sm" : "text-base"}`}>{d.label}</p>
              <p className="text-xs text-neutral-500">
                {d.value} stores · {((d.value / total) * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        ))}
      </div>
      <ChartTooltip tooltip={tooltip} />
    </div>
  );
}
