import { useEffect, useState } from "react";
import { useIsMainBranch } from "../../api/branches";
import { usePutReportSettings } from "../../api/report";
import type { ReportSettings } from "../../types/report";

const inputClasses =
  "w-full rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900";

function parseNumber(text: string): number | null {
  const cleaned = text.replace(/[$,\s]/g, "");
  if (cleaned === "") return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}

interface Draft {
  association_name: string;
  association_address: string;
  prepared_by: string;
  study_reference: string;
  basis_statement: string;
  financial_disclosures: string;
  budget_year: string;
  operating: string;
  reserves: string;
  window_start: string;
  window_end: string;
}

function toDraft(s: ReportSettings): Draft {
  return {
    association_name: s.association_name,
    association_address: s.association_address,
    prepared_by: s.prepared_by,
    study_reference: s.study_reference,
    basis_statement: s.basis_statement,
    financial_disclosures: s.financial_disclosures,
    budget_year: s.budget?.year.toString() ?? "",
    operating: s.budget?.operating.toString() ?? "",
    reserves: s.budget?.reserves.toString() ?? "",
    window_start: s.window_start?.toString() ?? "",
    window_end: s.window_end?.toString() ?? "",
  };
}

/** Returns the settings to save, or an error message. */
function fromDraft(d: Draft): ReportSettings | string {
  const budgetParts = [d.budget_year, d.operating, d.reserves];
  const anyBudget = budgetParts.some((p) => p.trim() !== "");
  let budget: ReportSettings["budget"] = null;
  if (anyBudget) {
    const year = parseNumber(d.budget_year);
    const operating = parseNumber(d.operating);
    const reserves = parseNumber(d.reserves);
    if (year === null || operating === null || reserves === null) {
      return "Budget needs a year, an operating amount and a reserves amount (or clear all three).";
    }
    budget = { year, operating, reserves };
  }
  return {
    association_name: d.association_name.trim(),
    association_address: d.association_address.trim(),
    prepared_by: d.prepared_by.trim(),
    study_reference: d.study_reference.trim(),
    basis_statement: d.basis_statement.trim(),
    financial_disclosures: d.financial_disclosures.trim(),
    budget,
    window_start: parseNumber(d.window_start),
    window_end: parseNumber(d.window_end),
  };
}

function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: React.ReactNode;
  hint?: string;
}) {
  return (
    <label className="block space-y-1 text-sm">
      <span className="font-medium">{label}</span>
      {children}
      {hint && (
        <span className="block text-xs text-slate-500 dark:text-slate-400">
          {hint}
        </span>
      )}
    </label>
  );
}

export function ReportSettingsForm({ settings }: { settings: ReportSettings }) {
  const isMainBranch = useIsMainBranch();
  const put = usePutReportSettings();
  const [draft, setDraft] = useState<Draft>(() => toDraft(settings));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setDraft(toDraft(settings)), [settings]);

  function set<K extends keyof Draft>(key: K, value: string) {
    setDraft((d) => ({ ...d, [key]: value }));
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const result = fromDraft(draft);
    if (typeof result === "string") {
      setError(result);
      return;
    }
    setError(null);
    put.mutate(result);
  }

  const disabled = isMainBranch || put.isPending;

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Association name">
          <input className={inputClasses} value={draft.association_name} disabled={disabled}
            onChange={(e) => set("association_name", e.target.value)} />
        </Field>
        <Field label="Prepared by">
          <input className={inputClasses} value={draft.prepared_by} disabled={disabled}
            placeholder="e.g. Board of Directors"
            onChange={(e) => set("prepared_by", e.target.value)} />
        </Field>
        <Field label="Address">
          <textarea className={inputClasses} rows={2} value={draft.association_address} disabled={disabled}
            onChange={(e) => set("association_address", e.target.value)} />
        </Field>
        <Field label="Independent reserve study reference">
          <textarea className={inputClasses} rows={2} value={draft.study_reference} disabled={disabled}
            placeholder="e.g. Reserve study by [vendor], dated October 11, 2024"
            onChange={(e) => set("study_reference", e.target.value)} />
        </Field>
      </div>

      <fieldset className="space-y-2 rounded border border-slate-200 p-3 dark:border-slate-800">
        <legend className="px-1 text-sm font-medium">Adopted annual budget</legend>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Budget year">
            <input className={inputClasses} inputMode="numeric" value={draft.budget_year} disabled={disabled}
              onChange={(e) => set("budget_year", e.target.value)} />
          </Field>
          <Field label="Operating ($)">
            <input className={inputClasses} inputMode="decimal" value={draft.operating} disabled={disabled}
              onChange={(e) => set("operating", e.target.value)} />
          </Field>
          <Field label="Reserves ($)">
            <input className={inputClasses} inputMode="decimal" value={draft.reserves} disabled={disabled}
              onChange={(e) => set("reserves", e.target.value)} />
          </Field>
        </div>
      </fieldset>

      <Field label="Basis of preparation">
        <textarea className={inputClasses} rows={4} value={draft.basis_statement} disabled={disabled}
          onChange={(e) => set("basis_statement", e.target.value)} />
      </Field>
      <Field label="Financial disclosures (loans, special assessments, etc.)">
        <textarea className={inputClasses} rows={2} value={draft.financial_disclosures} disabled={disabled}
          onChange={(e) => set("financial_disclosures", e.target.value)} />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="First year of report" hint="Blank = current year">
          <input className={inputClasses} inputMode="numeric" value={draft.window_start} disabled={disabled}
            onChange={(e) => set("window_start", e.target.value)} />
        </Field>
        <Field label="Last year of report" hint="Blank = 29 years after the first year">
          <input className={inputClasses} inputMode="numeric" value={draft.window_end} disabled={disabled}
            onChange={(e) => set("window_end", e.target.value)} />
        </Field>
      </div>

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {put.isError && (
        <p className="text-sm text-red-600 dark:text-red-400">
          {(put.error as Error).message}
        </p>
      )}
      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={disabled}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          Save settings
        </button>
        {put.isSuccess && !put.isPending && (
          <span className="text-sm text-emerald-600 dark:text-emerald-400">Saved</span>
        )}
      </div>
    </form>
  );
}
