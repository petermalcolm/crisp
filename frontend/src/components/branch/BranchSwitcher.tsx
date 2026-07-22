import { useState, type FormEvent } from "react";
import {
  useBranches,
  useCheckoutBranch,
  useCreateBranch,
  useMergeBranch,
} from "../../api/branches";

export function BranchSwitcher() {
  const { data, isLoading } = useBranches();
  const checkout = useCheckoutBranch();
  const createBranch = useCreateBranch();
  const merge = useMergeBranch();

  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [showMergeConfirm, setShowMergeConfirm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !data) return null;

  function handleCheckout(name: string) {
    if (name === data!.current) return;
    setError(null);
    checkout.mutate(name, { onError: (e) => setError((e as Error).message) });
  }

  function handleCreate(e: FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setError(null);
    createBranch.mutate(newName.trim(), {
      onSuccess: () => {
        setShowCreate(false);
        setNewName("");
      },
      onError: (e) => setError((e as Error).message),
    });
  }

  function handleMerge() {
    setError(null);
    merge.mutate(data!.current, {
      onSuccess: () => setShowMergeConfirm(false),
      onError: (e) => setError((e as Error).message),
    });
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={data.current}
        onChange={(e) => handleCheckout(e.target.value)}
        disabled={checkout.isPending}
        className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm disabled:opacity-50 dark:border-slate-700 dark:bg-slate-950"
      >
        {data.branches.map((b) => (
          <option key={b} value={b}>
            {b}
          </option>
        ))}
      </select>

      <button
        onClick={() => setShowCreate(true)}
        className="rounded-md border border-slate-300 px-2 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
      >
        + Forecast
      </button>

      {data.current !== "main" && (
        <button
          onClick={() => setShowMergeConfirm(true)}
          className="rounded-md bg-emerald-600 px-2 py-1.5 text-sm font-medium text-white hover:bg-emerald-500"
        >
          Merge to main
        </button>
      )}

      {error && (
        <span className="text-sm text-red-600 dark:text-red-400">
          {error}
        </span>
      )}

      {showCreate && (
        <div
          className="fixed inset-0 z-10 flex items-center justify-center bg-black/30"
          onClick={() => setShowCreate(false)}
        >
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleCreate}
            className="w-80 space-y-3 rounded-lg bg-white p-4 shadow-lg dark:bg-slate-900"
          >
            <h2 className="text-base font-semibold">New forecast branch</h2>
            <input
              autoFocus
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g. higher-inflation-2027"
              className="w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-950"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createBranch.isPending}
                className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
              >
                Create
              </button>
            </div>
          </form>
        </div>
      )}

      {showMergeConfirm && (
        <div
          className="fixed inset-0 z-10 flex items-center justify-center bg-black/30"
          onClick={() => setShowMergeConfirm(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-96 space-y-3 rounded-lg bg-white p-4 shadow-lg dark:bg-slate-900"
          >
            <h2 className="text-base font-semibold">
              Merge "{data.current}" into main?
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              This squash-merges every change on this forecast branch into
              main as a single commit, making it permanent.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowMergeConfirm(false)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={handleMerge}
                disabled={merge.isPending}
                className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                Merge
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
