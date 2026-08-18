import { useState, type FormEvent } from "react";
import { useCategories } from "../../api/categories";
import type { ComponentInput } from "../../types/component";

const emptyForm: ComponentInput = {
  name: "",
  estimated_cost: 0,
  initial_year: new Date().getFullYear(),
  expected_life_years: 1,
  category_code: null,
  notes: "",
};

const inputClasses =
  "rounded-md border border-slate-300 bg-white px-2 py-1.5 dark:border-slate-700 dark:bg-slate-950";

export function ComponentForm({
  initial,
  onSubmit,
  onCancel,
  submitLabel,
  isSubmitting,
}: {
  initial?: ComponentInput;
  onSubmit: (input: ComponentInput) => void;
  onCancel: () => void;
  submitLabel: string;
  isSubmitting?: boolean;
}) {
  const [form, setForm] = useState<ComponentInput>(initial ?? emptyForm);
  const { data: categories } = useCategories();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      notes: form.notes?.trim() ? form.notes : null,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-6 dark:border-slate-800 dark:bg-slate-900"
    >
      <label className="flex flex-col gap-1 text-sm sm:col-span-2">
        Name
        <input
          required
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className={inputClasses}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Category
        <select
          value={form.category_code ?? ""}
          onChange={(e) =>
            setForm({ ...form, category_code: e.target.value || null })
          }
          className={inputClasses}
        >
          <option value="">—</option>
          {categories?.map((c) => (
            <option key={c.code} value={c.code}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Estimated cost
        <input
          required
          type="number"
          min={0.01}
          step="0.01"
          value={form.estimated_cost}
          onChange={(e) =>
            setForm({ ...form, estimated_cost: Number(e.target.value) })
          }
          className={inputClasses}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Initial year
        <input
          required
          type="number"
          value={form.initial_year}
          onChange={(e) =>
            setForm({ ...form, initial_year: Number(e.target.value) })
          }
          className={inputClasses}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        Expected life (yrs)
        <input
          required
          type="number"
          min={1}
          step="1"
          value={form.expected_life_years}
          onChange={(e) =>
            setForm({ ...form, expected_life_years: Number(e.target.value) })
          }
          className={inputClasses}
        />
      </label>
      <label className="flex flex-col gap-1 text-sm sm:col-span-6">
        Notes
        <input
          value={form.notes ?? ""}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          className={inputClasses}
        />
      </label>
      <div className="flex gap-2 sm:col-span-6">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        >
          {submitLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
