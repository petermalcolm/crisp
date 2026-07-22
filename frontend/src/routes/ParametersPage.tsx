import { useEffect, useState } from "react";
import { useIsMainBranch } from "../api/branches";
import { usePatchYearParameters, useYearParameters } from "../api/parameters";
import { SurpriseContributionsSection } from "../components/parameters/SurpriseContributionsSection";
import { ReadOnlyBanner } from "../components/shared/ReadOnlyBanner";
import { StickyValueCell } from "../components/shared/StickyValueCell";
import type { YearParameterPatch, YearParameters } from "../types/parameters";

export function ParametersPage() {
  const { data, isLoading, isError, error } = useYearParameters();
  const patch = usePatchYearParameters();
  const isMainBranch = useIsMainBranch();

  function commit(
    year: number,
    field: keyof YearParameterPatch,
    value: number | string | null,
  ) {
    patch.mutate({
      year,
      patch: { [field]: value } as unknown as YearParameterPatch,
    });
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Income/Expenses Parameters</h1>

      {isMainBranch && <ReadOnlyBanner />}

      {isLoading && (
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {isError && (
        <p className="text-red-600 dark:text-red-400">
          Failed to load parameters: {(error as Error).message}
        </p>
      )}

      {data && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              <tr>
                <th className="px-3 py-2 font-medium">Year</th>
                <th className="px-3 py-2 font-medium">Contributors</th>
                <th className="px-3 py-2 font-medium">Inflation</th>
                <th className="px-3 py-2 font-medium">Interest</th>
                <th className="px-3 py-2 font-medium">YoY Contribution Δ</th>
                <th className="px-3 py-2 font-medium">Total Contribution</th>
                <th className="px-3 py-2 font-medium">Reserve Balance</th>
                <th className="px-3 py-2 font-medium">Notes</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <ParametersRow
                  key={row.year}
                  row={row}
                  onCommit={commit}
                  isPending={patch.isPending || isMainBranch}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      <SurpriseContributionsSection />
    </div>
  );
}

function ParametersRow({
  row,
  onCommit,
  isPending,
}: {
  row: YearParameters;
  onCommit: (
    year: number,
    field: keyof YearParameterPatch,
    value: number | string | null,
  ) => void;
  isPending: boolean;
}) {
  return (
    <tr className="border-b border-slate-100 last:border-0 dark:border-slate-800">
      <td className="px-3 py-2 align-top font-medium">{row.year}</td>
      <td className="px-3 py-2 align-top">
        <PlainNumberCell
          value={row.num_contributors}
          onCommit={(v) => onCommit(row.year, "num_contributors", v)}
          isPending={isPending}
        />
      </td>
      <td className="px-3 py-2 align-top">
        <StickyValueCell
          value={row.inflation_rate.value}
          isExplicit={row.inflation_rate.is_explicit}
          sourceYear={row.inflation_rate.source_year}
          onCommit={(v) => onCommit(row.year, "inflation_rate", v)}
          suffix="%"
          scale={100}
          isPending={isPending}
        />
      </td>
      <td className="px-3 py-2 align-top">
        <StickyValueCell
          value={row.interest_rate.value}
          isExplicit={row.interest_rate.is_explicit}
          sourceYear={row.interest_rate.source_year}
          onCommit={(v) => onCommit(row.year, "interest_rate", v)}
          suffix="%"
          scale={100}
          isPending={isPending}
        />
      </td>
      <td className="px-3 py-2 align-top">
        <StickyValueCell
          value={row.yoy_contribution_change_pct.value}
          isExplicit={row.yoy_contribution_change_pct.is_explicit}
          sourceYear={row.yoy_contribution_change_pct.source_year}
          onCommit={(v) =>
            onCommit(row.year, "yoy_contribution_change_pct", v)
          }
          suffix="%"
          scale={100}
          isPending={isPending}
        />
      </td>
      <td className="px-3 py-2 align-top">
        <StickyValueCell
          value={row.total_annual_contribution.value}
          isExplicit={row.total_annual_contribution.is_explicit}
          sourceYear={row.total_annual_contribution.source_year}
          onCommit={(v) =>
            onCommit(row.year, "total_annual_contribution", v)
          }
          suffix="$"
          decimals={0}
          isPending={isPending}
        />
      </td>
      <td className="px-3 py-2 align-top">
        <PlainNumberCell
          value={row.current_reserve_balance}
          onCommit={(v) => onCommit(row.year, "current_reserve_balance", v)}
          isPending={isPending}
          width="w-24"
        />
      </td>
      <td className="px-3 py-2 align-top">
        <PlainTextCell
          value={row.notes}
          onCommit={(v) => onCommit(row.year, "notes", v)}
          isPending={isPending}
        />
      </td>
    </tr>
  );
}

function PlainNumberCell({
  value,
  onCommit,
  isPending,
  width = "w-20",
}: {
  value: number | null;
  onCommit: (value: number | null) => void;
  isPending?: boolean;
  width?: string;
}) {
  const [draft, setDraft] = useState(value === null ? "" : String(value));
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) setDraft(value === null ? "" : String(value));
  }, [value, focused]);

  function commit() {
    setFocused(false);
    const trimmed = draft.trim();
    if (trimmed === "") {
      if (value !== null) onCommit(null);
      return;
    }
    const parsed = Number(trimmed);
    if (Number.isNaN(parsed)) {
      setDraft(value === null ? "" : String(value));
      return;
    }
    if (parsed !== value) onCommit(parsed);
  }

  return (
    <input
      value={draft}
      onFocus={() => setFocused(true)}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
      }}
      disabled={isPending}
      className={`${width} rounded border border-slate-300 px-1.5 py-1 text-right text-sm disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950`}
    />
  );
}

function PlainTextCell({
  value,
  onCommit,
  isPending,
}: {
  value: string | null;
  onCommit: (value: string | null) => void;
  isPending?: boolean;
}) {
  const [draft, setDraft] = useState(value ?? "");
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) setDraft(value ?? "");
  }, [value, focused]);

  function commit() {
    setFocused(false);
    const trimmed = draft.trim();
    const next = trimmed === "" ? null : trimmed;
    if (next !== value) onCommit(next);
  }

  return (
    <input
      value={draft}
      onFocus={() => setFocused(true)}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
      }}
      disabled={isPending}
      className="w-40 rounded border border-slate-300 px-1.5 py-1 text-sm disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950"
    />
  );
}
