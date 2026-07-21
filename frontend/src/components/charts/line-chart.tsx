"use client";

import * as d3 from "d3";
import { useMemo, useRef, useState } from "react";
import { chartColor } from "@/lib/chart-theme";
import { ChartTooltip, type TooltipState } from "./chart-tooltip";

export type LineSeriesPoint = {
  x: Date;
  y: number;
  ciLower?: number | null;
  ciUpper?: number | null;
};

export type LineSeries = {
  id: string;
  label: string;
  color?: string;
  data: LineSeriesPoint[];
};

const W = 720;
const MARGIN = { top: 16, right: 16, bottom: 28, left: 48 };

export function LineChart({
  series,
  valueFormat,
  height = 280,
}: {
  series: LineSeries[];
  valueFormat?: (n: number) => string;
  height?: number;
}) {
  const H = height;
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState>(null);
  const [hoverDate, setHoverDate] = useState<Date | null>(null);
  const fmt = valueFormat ?? ((n: number) => d3.format(",.0f")(n));

  const colored = useMemo(
    () => series.map((s, i) => ({ ...s, color: s.color ?? chartColor.categorical[i % chartColor.categorical.length] })),
    [series],
  );

  const allPoints = colored.flatMap((s) => s.data);
  const hasCi = colored.length === 1 && colored[0].data.some((d) => d.ciLower != null && d.ciUpper != null);

  const x = d3
    .scaleTime()
    .domain(d3.extent(allPoints, (d) => d.x) as [Date, Date])
    .range([MARGIN.left, W - MARGIN.right]);

  const yMax = d3.max(allPoints, (d) => Math.max(d.y, d.ciUpper ?? d.y)) ?? 1;
  const yMin = Math.min(0, d3.min(allPoints, (d) => Math.min(d.y, d.ciLower ?? d.y)) ?? 0);
  const y = d3
    .scaleLinear()
    .domain([yMin, yMax])
    .nice()
    .range([H - MARGIN.bottom, MARGIN.top]);

  const line = d3
    .line<LineSeriesPoint>()
    .x((d) => x(d.x))
    .y((d) => y(d.y))
    .curve(d3.curveMonotoneX);

  const area = d3
    .area<LineSeriesPoint>()
    .x((d) => x(d.x))
    .y0((d) => y(d.ciLower ?? d.y))
    .y1((d) => y(d.ciUpper ?? d.y))
    .curve(d3.curveMonotoneX);

  const yTicks = y.ticks(5);
  const xTicks = x.ticks(Math.min(6, allPoints.length));

  function handleMove(evt: React.PointerEvent<SVGRectElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const scaleX = W / rect.width;
    const px = (evt.clientX - rect.left) * scaleX;
    const cursorDate = x.invert(px);

    const nearest = d3.least(colored[0]?.data ?? [], (d) => Math.abs(d.x.getTime() - cursorDate.getTime()));
    if (!nearest) return;

    const rows = colored.map((s) => {
      const point = d3.least(s.data, (d) => Math.abs(d.x.getTime() - nearest.x.getTime()));
      return { label: s.label, value: point ? fmt(point.y) : "—", color: s.color };
    });

    setHoverDate(nearest.x);
    setTooltip({
      x: x(nearest.x) / scaleX,
      y: y(nearest.y) / scaleX,
      title: d3.timeFormat("%b %d, %Y")(nearest.x),
      rows,
    });
  }

  return (
    <div className="relative">
      {colored.length > 1 && (
        <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1">
          {colored.map((s) => (
            <div key={s.id} className="flex items-center gap-1.5 text-xs text-neutral-300">
              <span className="inline-block h-[2px] w-3" style={{ backgroundColor: s.color }} />
              {s.label}
            </div>
          ))}
        </div>
      )}
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Line chart">
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={MARGIN.left} x2={W - MARGIN.right} y1={y(t)} y2={y(t)} stroke={chartColor.gridline} strokeWidth={1} />
            <text x={MARGIN.left - 8} y={y(t)} dy="0.32em" textAnchor="end" fontSize={12} fill={chartColor.mutedInk}>
              {d3.format("~s")(t)}
            </text>
          </g>
        ))}
        {xTicks.map((t) => (
          <text
            key={t.getTime()}
            x={x(t)}
            y={H - MARGIN.bottom + 16}
            textAnchor="middle"
            fontSize={12}
            fill={chartColor.mutedInk}
          >
            {d3.timeFormat("%b %d")(t)}
          </text>
        ))}

        {hasCi && <path d={area(colored[0].data) ?? undefined} fill={colored[0].color} opacity={0.1} />}

        {colored.map((s) => (
          <path key={s.id} d={line(s.data) ?? undefined} fill="none" stroke={s.color} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        ))}

        {hoverDate && (
          <line
            x1={x(hoverDate)}
            x2={x(hoverDate)}
            y1={MARGIN.top}
            y2={H - MARGIN.bottom}
            stroke={chartColor.axis}
            strokeWidth={1}
          />
        )}
        {hoverDate &&
          colored.map((s) => {
            const nearest = d3.least(s.data, (d) => Math.abs(d.x.getTime() - hoverDate.getTime()));
            return nearest ? (
              <circle key={s.id} cx={x(nearest.x)} cy={y(nearest.y)} r={4} fill={s.color} stroke={chartColor.surface} strokeWidth={2} />
            ) : null;
          })}

        <rect
          x={MARGIN.left}
          y={MARGIN.top}
          width={W - MARGIN.left - MARGIN.right}
          height={H - MARGIN.top - MARGIN.bottom}
          fill="transparent"
          onPointerMove={handleMove}
          onPointerLeave={() => {
            setTooltip(null);
            setHoverDate(null);
          }}
        />
      </svg>
      <ChartTooltip tooltip={tooltip} />
    </div>
  );
}
