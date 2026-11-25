import type { ProjectionYear } from "../../types/report";

const W = 760;
const H = 300;
const M = { top: 16, right: 16, bottom: 36, left: 72 };

function niceStep(rough: number): number {
  if (rough <= 0) return 1;
  const pow = 10 ** Math.floor(Math.log10(rough));
  const n = rough / pow;
  return ([1, 2, 2.5, 5, 10].find((s) => n <= s) ?? 10) * pow;
}

function axisLabel(v: number): string {
  const sign = v < 0 ? "-" : "";
  const a = Math.abs(v);
  if (a >= 1_000_000) return `${sign}$${parseFloat((a / 1_000_000).toFixed(2))}M`;
  if (a >= 1000) return `${sign}$${Math.round(a / 1000)}k`;
  return `${sign}$${Math.round(a)}`;
}

/** Reserve balance and fully funded balance (January 1) against the year's
 * planned spending. Plain SVG, black/gray only so it survives a grayscale
 * printout: line styles, not colour, tell the series apart. */
export function ProjectionChart({ years }: { years: ProjectionYear[] }) {
  if (years.length === 0) return null;

  const balances = years.map((y) => y.start_balance ?? 0);
  const dataMax = Math.max(
    ...years.map((y) => y.ffb),
    ...balances,
    ...years.map((y) => y.costs),
  );
  const dataMin = Math.min(0, ...balances);
  // Round tick step (1/2/2.5/5 x 10^n) giving about 4 intervals above zero.
  const step = niceStep(dataMax / 4);
  const top = Math.ceil(dataMax / step) * step;
  const bottom = Math.floor(dataMin / step) * step;
  const plotW = W - M.left - M.right;
  const plotH = H - M.top - M.bottom;

  const x = (i: number) => M.left + (plotW * (i + 0.5)) / years.length;
  const y = (v: number) => M.top + plotH * (1 - (v - bottom) / (top - bottom));
  const barW = Math.max(2, (plotW / years.length) * 0.6);

  const line = (values: (number | null)[]) =>
    values
      .map((v, i) => (v === null ? null : `${x(i).toFixed(1)},${y(v).toFixed(1)}`))
      .filter((p): p is string => p !== null)
      .join(" ");

  const ticks: number[] = [];
  for (let t = bottom; t <= top + step / 2; t += step) ticks.push(t);
  const labelEvery = years.length > 16 ? 5 : 1;

  return (
    <figure>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Reserve balance and fully funded balance versus planned spending"
        className="w-full"
      >
        {ticks.map((t) => (
          <g key={t}>
            <line x1={M.left} x2={W - M.right} y1={y(t)} y2={y(t)} stroke="#d1d5db" strokeWidth={0.5} />
            <text x={M.left - 6} y={y(t) + 3} textAnchor="end" fontSize={10} fill="#374151">
              {axisLabel(t)}
            </text>
          </g>
        ))}
        {years.map((yr, i) => (
          <g key={yr.year}>
            <rect
              x={x(i) - barW / 2}
              y={y(yr.costs)}
              width={barW}
              height={Math.max(0, y(0) - y(yr.costs))}
              fill="#9ca3af"
            />
            {(yr.year - years[0].year) % labelEvery === 0 && (
              <text x={x(i)} y={H - M.bottom + 14} textAnchor="middle" fontSize={10} fill="#374151">
                {yr.year}
              </text>
            )}
          </g>
        ))}
        <polyline
          points={line(years.map((yr) => yr.ffb))}
          fill="none" stroke="#111827" strokeWidth={1.5} strokeDasharray="5 3"
        />
        <polyline
          points={line(years.map((yr) => yr.start_balance))}
          fill="none" stroke="#111827" strokeWidth={2}
        />
        <line x1={M.left} x2={W - M.right} y1={y(0)} y2={y(0)} stroke="#111827" strokeWidth={0.75} />
      </svg>
      <figcaption className="mt-1 flex flex-wrap gap-x-5 text-xs text-slate-700">
        <span><b>━</b> Reserve balance (Jan 1)</span>
        <span><b>╌</b> Fully funded balance (Jan 1)</span>
        <span><span className="inline-block h-2.5 w-2.5 bg-gray-400 align-middle" /> Planned spending in year</span>
      </figcaption>
    </figure>
  );
}
