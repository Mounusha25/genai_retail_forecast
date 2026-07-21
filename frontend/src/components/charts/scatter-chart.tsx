"use client";

import * as d3 from "d3";
import { useRef, useState } from "react";
import { chartColor } from "@/lib/chart-theme";
import { ChartTooltip, type TooltipState } from "./chart-tooltip";

export type ScatterDatum = { label: string; x: number; y: number; category: string };

const W = 640;
const MARGIN = { top: 16, right: 16, bottom: 40, left: 56 };

export function ScatterChart({
  data,
  categoryColors,
  xLabel,
  yLabel,
  height = 320,
}: {
  data: ScatterDatum[];
  categoryColors: Record<string, string>;
  xLabel: string;
  yLabel: string;
  height?: number;
}) {
  const H = height;
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState>(null);

  const x = d3
    .scaleLinear()
    .domain([0, (d3.max(data, (d) => d.x) ?? 1) * 1.05])
    .range([MARGIN.left, W - MARGIN.right]);
  const y = d3
    .scaleLinear()
    .domain([0, (d3.max(data, (d) => d.y) ?? 1) * 1.1])
    .nice()
    .range([H - MARGIN.bottom, MARGIN.top]);

  const xTicks = x.ticks(5);
  const yTicks = y.ticks(5);
  const categories = [...new Set(data.map((d) => d.category))];

  return (
    <div ref={containerRef} className="relative">
      <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1">
        {categories.map((cat) => (
          <div key={cat} className="flex items-center gap-1.5 text-xs text-neutral-300">
            <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: categoryColors[cat] }} />
            {cat}
          </div>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Scatter chart">
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={MARGIN.left} x2={W - MARGIN.right} y1={y(t)} y2={y(t)} stroke={chartColor.gridline} strokeWidth={1} />
            <text x={MARGIN.left - 8} y={y(t)} dy="0.32em" textAnchor="end" fontSize={11} fill={chartColor.mutedInk}>
              {d3.format("~s")(t)}
            </text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text key={t} x={x(t)} y={H - MARGIN.bottom + 18} textAnchor="middle" fontSize={11} fill={chartColor.mutedInk}>
            {d3.format("~s")(t)}
          </text>
        ))}
        <text x={(W + MARGIN.left - MARGIN.right) / 2} y={H - 4} textAnchor="middle" fontSize={11} fill={chartColor.mutedInk}>
          {xLabel}
        </text>
        <text
          x={-(H / 2)}
          y={14}
          textAnchor="middle"
          fontSize={11}
          fill={chartColor.mutedInk}
          transform="rotate(-90)"
        >
          {yLabel}
        </text>

        {data.map((d) => {
          const isHovered = tooltip?.title === d.label;
          return (
            <g key={d.label}>
              <circle
                cx={x(d.x)}
                cy={y(d.y)}
                r={12}
                fill="transparent"
                onPointerMove={(evt) => {
                  const rect = containerRef.current?.getBoundingClientRect();
                  const px = rect ? evt.clientX - rect.left : x(d.x);
                  const py = rect ? evt.clientY - rect.top : y(d.y);
                  setTooltip({
                    x: px,
                    y: py,
                    title: d.label,
                    rows: [
                      { label: xLabel, value: d3.format(",.0f")(d.x), color: categoryColors[d.category] },
                      { label: yLabel, value: d3.format(",.0f")(d.y), color: categoryColors[d.category] },
                    ],
                  });
                }}
                onPointerLeave={() => setTooltip(null)}
              />
              <circle
                cx={x(d.x)}
                cy={y(d.y)}
                r={isHovered ? 6 : 4}
                fill={categoryColors[d.category]}
                stroke={chartColor.surface}
                strokeWidth={2}
                opacity={isHovered ? 1 : 0.8}
                className="pointer-events-none transition-all duration-150"
              />
            </g>
          );
        })}
      </svg>
      <ChartTooltip tooltip={tooltip} />
    </div>
  );
}
