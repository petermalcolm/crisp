import { useCostsProjection } from "../api/costs";
import { YearSection } from "../components/costs/YearSection";

export function CostsPage() {
  const { data, isLoading, isError, error } = useCostsProjection();

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Costs</h1>

      {isLoading && (
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {isError && (
        <p className="text-red-600 dark:text-red-400">
          Failed to load costs: {(error as Error).message}
        </p>
      )}

      {data && (
        <div className="space-y-3">
          {data.map((row) => (
            <YearSection key={row.year} row={row} />
          ))}
        </div>
      )}
    </div>
  );
}
