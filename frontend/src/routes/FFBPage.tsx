import { useFFBProjection } from "../api/ffb";
import { EstimateBadge } from "../components/shared/EstimateBadge";
import type { YearFFBRow } from "../types/ffb";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function percentFundedClasses(percentFunded: number | null): string {
  if (percentFunded === null) return "text-slate-400 dark:text-slate-500";
  if (percentFunded >= 1) return "text-emerald-600 dark:text-emerald-400";
  if (percentFunded >= 0.7) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

function formatPercent(percentFunded: number | null): string {
  if (percentFunded === null) return "—";
  return `${(percentFunded * 100).toFixed(0)}%`;
}

function formatBalance(balance: number | null): string {
  if (balance === null) return "—";
  return currencyFormatter.format(balance);
}

export function FFBPage() {
  const { data, isLoading, isError, error } = useFFBProjection();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Fully Funded Balance</h1>

      {isLoading && (
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {isError && (
        <p className="text-red-600 dark:text-red-400">
          Failed to load FFB projection: {(error as Error).message}
        </p>
      )}
      {data && data.every((row) => row.actual_balance === null) && (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
          No current reserve balance has been set yet. Set one in Income/Expenses
          Parameters to see actual balance and percent funded.
        </p>
      )}

      {data && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              <tr>
                <th className="px-3 py-2 font-medium">Year</th>
                <th className="px-3 py-2 font-medium"></th>
                <th className="px-3 py-2 font-medium text-right">
                  FFB Target
                </th>
                <th className="px-3 py-2 font-medium text-right">
                  Actual Balance
                </th>
                <th className="px-3 py-2 font-medium text-right">
                  % Funded
                </th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <FFBRow key={row.year} row={row} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FFBRow({ row }: { row: YearFFBRow }) {
  return (
    <tr className="border-b border-slate-100 last:border-0 dark:border-slate-800">
      <td className="px-3 py-2 font-medium">{row.year}</td>
      <td className="px-3 py-2">
        <EstimateBadge isEstimate={row.is_estimate} />
      </td>
      <td className="px-3 py-2 text-right">
        {currencyFormatter.format(row.ffb_target)}
      </td>
      <td className="px-3 py-2 text-right">
        {formatBalance(row.actual_balance)}
      </td>
      <td
        className={`px-3 py-2 text-right font-semibold ${percentFundedClasses(row.percent_funded)}`}
      >
        {formatPercent(row.percent_funded)}
      </td>
    </tr>
  );
}
