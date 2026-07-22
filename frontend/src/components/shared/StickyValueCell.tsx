import { useEffect, useState } from "react";

/**
 * An editable cell for a "sticky" per-year value: solid/dark when this year
 * has an explicit override, light/italic when the value is inherited from
 * an earlier year. Typing a new value and committing it creates a real
 * override for this year, which becomes the new anchor for later years.
 * Clearing the field removes the override, reverting to the inherited value.
 */
export function StickyValueCell({
  value,
  isExplicit,
  sourceYear,
  onCommit,
  suffix,
  scale = 1,
  decimals = 2,
  isPending,
}: {
  value: number | null;
  isExplicit: boolean;
  sourceYear: number | null;
  onCommit: (value: number | null) => void;
  suffix?: string;
  scale?: number;
  decimals?: number;
  isPending?: boolean;
}) {
  const displayValue = value === null ? "" : (value * scale).toFixed(decimals);
  const [draft, setDraft] = useState(displayValue);
  const [focused, setFocused] = useState(false);

  useEffect(() => {
    if (!focused) setDraft(displayValue);
  }, [displayValue, focused]);

  function commit() {
    setFocused(false);
    const trimmed = draft.trim();
    if (trimmed === "") {
      if (value !== null) onCommit(null);
      else setDraft(displayValue);
      return;
    }
    const parsed = Number(trimmed);
    if (Number.isNaN(parsed)) {
      setDraft(displayValue);
      return;
    }
    const raw = parsed / scale;
    if (raw !== value) onCommit(raw);
    else setDraft(displayValue);
  }

  return (
    <span className="inline-flex items-center gap-1">
      <input
        value={draft}
        onFocus={() => setFocused(true)}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") (e.target as HTMLInputElement).blur();
          if (e.key === "Escape") {
            setDraft(displayValue);
            (e.target as HTMLInputElement).blur();
          }
        }}
        disabled={isPending}
        title={
          !isExplicit && sourceYear !== null
            ? `Carried from ${sourceYear} — type to override`
            : undefined
        }
        placeholder={!isExplicit && value !== null ? undefined : "—"}
        className={
          "w-16 rounded border px-1.5 py-1 text-right text-sm outline-none disabled:opacity-50 " +
          (isExplicit
            ? "border-slate-300 bg-white font-medium text-slate-900 focus:border-slate-500 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            : "border-dashed border-slate-200 bg-transparent italic text-slate-400 focus:border-slate-400 dark:border-slate-700 dark:text-slate-500")
        }
      />
      {suffix && (
        <span className="text-xs text-slate-400 dark:text-slate-500">
          {suffix}
        </span>
      )}
    </span>
  );
}
