import { useState } from "react";
import { useDeleteActual, useEditActual } from "../../api/actualCosts";
import { Modal } from "../shared/Modal";

const inputClasses =
  "w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950";

export function EditActualDialog({
  componentId,
  componentName,
  year,
  initialCost,
  initialComment,
  onClose,
}: {
  componentId: string;
  componentName: string;
  year: number;
  initialCost: number;
  initialComment: string | null;
  onClose: () => void;
}) {
  const edit = useEditActual();
  const remove = useDeleteActual();
  const [cost, setCost] = useState(initialCost.toFixed(2));
  const [comment, setComment] = useState(initialComment ?? "");
  const [confirmingRemove, setConfirmingRemove] = useState(false);

  const parsedCost = cost.trim() === "" ? NaN : Number(cost);
  const canSave = Number.isFinite(parsedCost) && parsedCost >= 0 && !edit.isPending;
  const error = edit.error ?? remove.error;

  function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!canSave) return;
    edit.mutate(
      { componentId, year, cost: parsedCost, comment: comment.trim() || null },
      { onSuccess: onClose },
    );
  }

  function handleRemove() {
    remove.mutate({ componentId, year }, { onSuccess: onClose });
  }

  return (
    <Modal title={`Actual cost — ${componentName}, ${year}`} onClose={onClose}>
      <form onSubmit={handleSave} className="space-y-4">
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

        {confirmingRemove && (
          <div className="space-y-2 rounded-md bg-red-50 px-3 py-2 text-sm text-red-900 dark:bg-red-900/30 dark:text-red-200">
            <p>
              Remove this actual? {componentName} goes back to a scheduled
              estimate for {year} where its schedule allows. A recurring-cost
              change made when it was recorded isn't undone — adjust that on
              the Components page if needed.
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleRemove}
                disabled={remove.isPending}
                className="font-medium underline disabled:opacity-50"
              >
                Yes, remove it
              </button>
              <button
                type="button"
                onClick={() => setConfirmingRemove(false)}
                className="underline"
              >
                Keep it
              </button>
            </div>
          </div>
        )}

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400">
            {(error as Error).message}
          </p>
        )}

        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={() => setConfirmingRemove(true)}
            className="text-sm font-medium text-red-600 hover:underline dark:text-red-400"
          >
            Remove actual
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSave}
              className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
            >
              Save
            </button>
          </div>
        </div>
      </form>
    </Modal>
  );
}
