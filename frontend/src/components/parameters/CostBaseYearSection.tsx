import { useEffect, useState } from "react";
import { useIsMainBranch } from "../../api/branches";
import { usePutStudySettings, useStudySettings } from "../../api/studySettings";

/** The year component estimates are denominated in. Separate from the
 * reserve-balance year so re-anchoring the balance doesn't change what the
 * estimates mean. */
export function CostBaseYearSection() {
  const { data } = useStudySettings();
  const put = usePutStudySettings();
  const isMainBranch = useIsMainBranch();
  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (data) setDraft(data.cost_base_year?.toString() ?? "");
  }, [data]);

  if (!data) return null;

  function commit() {
    const trimmed = draft.trim();
    const next = trimmed === "" ? null : Number.parseInt(trimmed, 10);
    if (next !== null && Number.isNaN(next)) return;
    if (next === data!.cost_base_year) return;
    put.mutate(next);
  }

  const implicit = data.cost_base_year === null;

  return (
    <section className="space-y-2 rounded-lg border border-slate-200 p-4 dark:border-slate-800">
      <h2 className="text-base font-semibold">Estimate dollars</h2>
      <p className="text-sm text-slate-600 dark:text-slate-400">
        Component costs are in dollars of this year and are inflated forward
        from it. The Reserve Balance above is the balance on January 1 of its
        year.
      </p>
      <label className="flex items-center gap-2 text-sm">
        <span>Cost base year</span>
        <input
          type="number"
          className="w-24 rounded border border-slate-300 bg-white px-2 py-1 dark:border-slate-700 dark:bg-slate-900"
          value={draft}
          placeholder={data.effective_cost_base_year.toString()}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
          disabled={isMainBranch || put.isPending}
        />
      </label>
      {implicit && (
        <p className="text-sm text-amber-700 dark:text-amber-400">
          Not set: using {data.effective_cost_base_year}
          {data.balance_year !== null ? ", the Reserve Balance year" : ""}. Set
          this explicitly before moving the Reserve Balance to a later year, or
          estimates will be treated as that year&rsquo;s dollars.
        </p>
      )}
    </section>
  );
}
