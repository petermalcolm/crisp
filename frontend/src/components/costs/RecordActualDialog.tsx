import { useState } from "react";
import { useActualCostPreview, useRecordActual } from "../../api/actualCosts";
import { formatDollars } from "../../lib/currency";
import type {
  ActualCostPreview,
  RecurrenceMode,
} from "../../types/actualCost";
import { Modal } from "../shared/Modal";

const inputClasses =
  "w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950";

export function RecordActualDialog({
  componentId,
  componentName,
  year,
  onClose,
}: {
  componentId: string;
  componentName: string;
  year: number;
  onClose: () => void;
}) {
  const { data: preview, isLoading, isError, error } = useActualCostPreview(
    componentId,
    year,
  );

  return (
    <Modal title={`Record actual cost — ${componentName}, ${year}`} onClose={onClose}>
      {isLoading && (
        <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {isError && (
        <>
          <p className="text-sm text-red-600 dark:text-red-400">
            {(error as Error).message}
          </p>
          <CloseButton onClose={onClose} />
        </>
      )}
      {preview && <RecordActualForm preview={preview} onClose={onClose} />}
    </Modal>
  );
}

function CloseButton({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex justify-end">
      <button
        type="button"
        onClick={onClose}
        className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300"
      >
        Close
      </button>
    </div>
  );
}

function RecordActualForm({
  preview,
  onClose,
}: {
  preview: ActualCostPreview;
  onClose: () => void;
}) {
  const record = useRecordActual();
  const [cost, setCost] = useState(preview.estimated_cost.toFixed(2));
  const [comment, setComment] = useState("");
  const [mode, setMode] = useState<RecurrenceMode>("keep");
  const [otherEstimate, setOtherEstimate] = useState("");

  const parsedCost = cost.trim() === "" ? NaN : Number(cost);
  const parsedOther = otherEstimate.trim() === "" ? NaN : Number(otherEstimate);
  const costOk = Number.isFinite(parsedCost) && parsedCost >= 0;
  const recurrenceOk =
    mode === "other"
      ? Number.isFinite(parsedOther) && parsedOther > 0
      : mode === "actual"
        ? costOk && parsedCost > 0
        : true;
  const canSubmit = costOk && recurrenceOk && !record.isPending;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    record.mutate(
      {
        component_id: preview.component_id,
        year: preview.year,
        cost: parsedCost,
        comment: comment.trim() || null,
        recurrence:
          mode === "other"
            ? { mode, estimate: parsedOther }
            : { mode },
      },
      { onSuccess: onClose },
    );
  }

  const name = preview.component_name;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Estimated for {preview.year}: {formatDollars(preview.estimated_cost, 2)}
      </p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <label className="flex flex-col gap-1 text-sm">
          Actual amount spent ($)
          <input
            autoFocus
            required
            type="number"
            min={0}
            step="0.01"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            className={inputClasses}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm sm:col-span-2">
          Comment (optional)
          <input
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className={inputClasses}
          />
        </label>
      </div>

      {preview.backfill.length > 0 && (
        <div className="space-y-1 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:bg-amber-900/30 dark:text-amber-200">
          <p className="font-medium">
            Earlier occurrences have no actual recorded
          </p>
          <p>
            {name} also came due in{" "}
            {preview.backfill.map((b) => b.year).join(", ")} with nothing
            recorded. Saving will backfill {preview.backfill.length === 1 ? "it" : "them"}{" "}
            with the estimate{preview.backfill.length === 1 ? "" : "s"} below.
            Cancel if you'd rather record the earlier {preview.backfill.length === 1 ? "year" : "years"} by
            hand first.
          </p>
          <ul className="list-inside list-disc">
            {preview.backfill.map((b) => (
              <li key={b.year}>
                {b.year}: {formatDollars(b.cost, 2)}
              </li>
            ))}
          </ul>
        </div>
      )}

      <fieldset className="space-y-2">
        <legend className="text-sm font-medium">
          Update recurring cost of {name} to match this value?
        </legend>
        <RecurrenceOption
          checked={mode === "actual"}
          onSelect={() => setMode("actual")}
          label="Yes"
          detail="Make the recurring cost the actual cost, inflation-adjusted going forward."
        />
        <RecurrenceOption
          checked={mode === "keep"}
          onSelect={() => setMode("keep")}
          label="No, keep estimate"
          detail="Leave the recurring cost as it is on the Components page."
        />
        <RecurrenceOption
          checked={mode === "other"}
          onSelect={() => setMode("other")}
          label="Other"
          detail="Enter a new recurring estimate by hand."
        />
        {mode === "other" && (
          <label className="ml-6 flex flex-col gap-1 text-sm">
            New recurring estimate ($)
            <input
              required
              type="number"
              min={0.01}
              step="0.01"
              value={otherEstimate}
              onChange={(e) => setOtherEstimate(e.target.value)}
              className={`${inputClasses} max-w-48`}
            />
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Entered the same way as Estimated cost on the Components page.
            </span>
          </label>
        )}
        {mode === "actual" && Number.isFinite(parsedCost) && parsedCost <= 0 && (
          <p className="ml-6 text-xs text-red-600 dark:text-red-400">
            A $0 actual can't set the recurring cost — pick another option.
          </p>
        )}
      </fieldset>

      <p className="text-sm text-slate-500 dark:text-slate-400">
        {name} will next come due in {preview.new_initial_year} (
        {preview.expected_life_years}-year life after {preview.year}).
      </p>

      {record.isError && (
        <p className="text-sm text-red-600 dark:text-red-400">
          {(record.error as Error).message}
        </p>
      )}

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onClose}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!canSubmit}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          Record actual
        </button>
      </div>
    </form>
  );
}

function RecurrenceOption({
  checked,
  onSelect,
  label,
  detail,
}: {
  checked: boolean;
  onSelect: () => void;
  label: string;
  detail: string;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-2 text-sm">
      <input
        type="radio"
        name="recurrence"
        checked={checked}
        onChange={onSelect}
        className="mt-1"
      />
      <span>
        <span className="font-medium">{label}</span>
        <span className="block text-slate-500 dark:text-slate-400">{detail}</span>
      </span>
    </label>
  );
}
