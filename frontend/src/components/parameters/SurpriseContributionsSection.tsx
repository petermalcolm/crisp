import { useState, type FormEvent } from "react";
import { useIsMainBranch } from "../../api/branches";
import {
  useCreateSurpriseContribution,
  useDeleteSurpriseContribution,
  useSurpriseContributions,
} from "../../api/parameters";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function SurpriseContributionsSection() {
  const { data, isLoading } = useSurpriseContributions();
  const create = useCreateSurpriseContribution();
  const remove = useDeleteSurpriseContribution();
  const isMainBranch = useIsMainBranch();

  const [year, setYear] = useState(new Date().getFullYear());
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const parsed = Number(amount);
    if (Number.isNaN(parsed) || parsed === 0) return;
    create.mutate(
      { year, amount: parsed, description: description.trim() || null },
      {
        onSuccess: () => {
          setAmount("");
          setDescription("");
        },
      },
    );
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Surprise Contributions</h2>
      <form
        onSubmit={handleSubmit}
        className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900"
      >
        <label className="flex flex-col gap-1 text-xs text-slate-500 dark:text-slate-400">
          Year
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-24 rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-950"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-slate-500 dark:text-slate-400">
          Amount ($)
          <input
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-32 rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-950"
          />
        </label>
        <label className="flex min-w-[160px] flex-1 flex-col gap-1 text-xs text-slate-500 dark:text-slate-400">
          Description
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-950"
          />
        </label>
        <button
          type="submit"
          disabled={create.isPending || isMainBranch}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        >
          Add
        </button>
      </form>

      {isLoading && (
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {data && data.length > 0 && (
        <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200 dark:divide-slate-800 dark:border-slate-800">
          {data.map((c) => (
            <li
              key={c.id}
              className="flex items-center justify-between px-4 py-2 text-sm"
            >
              <span className="flex items-center gap-3">
                <span className="font-medium">{c.year}</span>
                <span>{currencyFormatter.format(c.amount)}</span>
                {c.description && (
                  <span className="text-slate-500 dark:text-slate-400">
                    {c.description}
                  </span>
                )}
              </span>
              {!isMainBranch && (
                <button
                  onClick={() => remove.mutate(c.id)}
                  className="text-sm font-medium text-red-600 hover:underline dark:text-red-400"
                >
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {data && data.length === 0 && (
        <p className="text-slate-500 dark:text-slate-400">
          No surprise contributions recorded.
        </p>
      )}
    </section>
  );
}
