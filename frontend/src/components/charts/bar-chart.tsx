"use client";

import * as d3 from "d3";
import { useMemo, useRef, useState } from "react";
import { chartColor } from "@/lib/chart-theme";
import { ChartTooltip, type TooltipState } from "./chart-tooltip";

export type BarDatum = { label: string; value: number };

const MARGIN = { top: 16, right: 16, bottom: 32, left: 56 };
const BAR_MAX_THICKNESS = 24;
const GAP = 2;

export function BarChart({
  data,
  color,
  valueFormat,
  height = 260,
}: {
  data: BarDatum[];
  color?: string;
  valueFormat?: (n: number) => string;
  height?: number;
}) {
  const H = height;
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const [width, setWidth] = useState(720);
  const fmt = valueFormat ?? ((n: number) => d3.format(",.0f")(n));
  const barColor = color ?? chartColor.categorical[0];

  const x = useMemo(
    () =>
      d3
        .scaleBand()
        .domain(data.map((d) => d.label))
        .range([MARGIN.left, width - MARGIN.right])
        .padding(0.25),
    [data, width],
  );

  const yMax = d3.max(data, (d) => d.value) ?? 1;
  const y = d3
    .scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([H - MARGIN.bottom, MARGIN.top]);

  const barWidth = Math.min(x.bandwidth(), BAR_MAX_THICKNESS) - GAP;
  const yTicks = y.ticks(5);

  function handleResize(node: HTMLDivElement | null) {
    containerRef.current = node;
    if (node) setWidth(node.getBoundingClientRect().width);
  }

  return (
    <div className="relative" ref={handleResize}>
      <svg viewBox={`0 0 ${width} ${H}`} className="w-full" role="img" aria-label="Bar chart">
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={MARGIN.left} x2={width - MARGIN.right} y1={y(t)} y2={y(t)} stroke={chartColor.gridline} strokeWidth={1} />
            <text x={MARGIN.left - 8} y={y(t)} dy="0.32em" textAnchor="end" fontSize={12} fill={chartColor.mutedInk}>
              {d3.format("~s")(t)}
            </text>
          </g>
        ))}
        {data.map((d) => {
          const bx = (x(d.label) ?? 0) + (x.bandwidth() - barWidth) / 2;
          const barH = H - MARGIN.bottom - y(d.value);
          const isHovered = tooltip?.title === d.label;
          return (
            <g key={d.label}>
              <rect
                x={bx}
                y={y(d.value)}
                width={barWidth}
                height={barH}
                rx={4}
                fill={barColor}
                opacity={isHovered ? 1 : 0.85}
                onPointerMove={() =>
                  setTooltip({
                    x: bx + barWidth / 2,
                    y: y(d.value),
                    title: d.label,
                    rows: [{ label: "Value", value: fmt(d.value), color: barColor }],
                  })
                }
                onPointerLeave={() => setTooltip(null)}
              />
              <text x={bx + barWidth / 2} y={H - MARGIN.bottom + 16} textAnchor="middle" fontSize={12} fill={chartColor.mutedInk}>
                {d.label.length > 10 ? `${d.label.slice(0, 9)}…` : d.label}
              </text>
            </g>
          );
        })}
      </svg>
      <ChartTooltip tooltip={tooltip} />
    </div>
  );
}
