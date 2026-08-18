import { useState } from "react";
import { useIsMainBranch } from "../api/branches";
import { useCategories } from "../api/categories";
import {
  useComponents,
  useCreateComponent,
  useDeleteComponent,
  useUpdateComponent,
} from "../api/components";
import { ComponentForm } from "../components/shared/ComponentForm";
import { ReadOnlyBanner } from "../components/shared/ReadOnlyBanner";
import type { ComponentInput } from "../types/component";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

type Mode = "idle" | "adding" | { editingId: string };

export function ComponentsListPage() {
  const { data: components, isLoading, isError, error } = useComponents();
  const { data: categories } = useCategories();
  const createComponent = useCreateComponent();
  const updateComponent = useUpdateComponent();
  const deleteComponent = useDeleteComponent();

  const [mode, setMode] = useState<Mode>("idle");
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const isMainBranch = useIsMainBranch();

  const categoryNameByCode = new Map(
    categories?.map((c) => [c.code, c.name]) ?? [],
  );

  function handleCreate(input: ComponentInput) {
    createComponent.mutate(input, { onSuccess: () => setMode("idle") });
  }

  function handleUpdate(id: string, input: ComponentInput) {
    updateComponent.mutate(
      { id, input },
      { onSuccess: () => setMode("idle") },
    );
  }

  function handleConfirmDelete(id: string) {
    deleteComponent.mutate(id, { onSuccess: () => setConfirmDeleteId(null) });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Components</h1>
        {mode === "idle" && !isMainBranch && (
          <button
            onClick={() => setMode("adding")}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          >
            Add component
          </button>
        )}
      </div>

      {isMainBranch && <ReadOnlyBanner />}

      {mode === "adding" && (
        <ComponentForm
          submitLabel="Add"
          onSubmit={handleCreate}
          onCancel={() => setMode("idle")}
          isSubmitting={createComponent.isPending}
        />
      )}

      {isLoading && (
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {isError && (
        <p className="text-red-600 dark:text-red-400">
          Failed to load components: {(error as Error).message}
        </p>
      )}

      {components && components.length === 0 && mode === "idle" && (
        <p className="text-slate-500 dark:text-slate-400">
          No components yet. Add one to get started.
        </p>
      )}

      {components && components.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-100 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              <tr>
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Category</th>
                <th className="px-3 py-2 font-medium">Estimated cost</th>
                <th className="px-3 py-2 font-medium">Initial year</th>
                <th className="px-3 py-2 font-medium">Expected life</th>
                <th className="px-3 py-2 font-medium">Notes</th>
                <th className="px-3 py-2 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {components.map((component) =>
                typeof mode === "object" && mode.editingId === component.id ? (
                  <tr key={component.id}>
                    <td colSpan={7} className="p-2">
                      <ComponentForm
                        initial={component}
                        submitLabel="Save"
                        onSubmit={(input) => handleUpdate(component.id, input)}
                        onCancel={() => setMode("idle")}
                        isSubmitting={updateComponent.isPending}
                      />
                    </td>
                  </tr>
                ) : (
                  <tr
                    key={component.id}
                    className="border-b border-slate-100 last:border-0 dark:border-slate-800"
                  >
                    <td className="px-3 py-2 font-medium">
                      {component.name}
                    </td>
                    <td className="px-3 py-2 text-slate-500 dark:text-slate-400">
                      {(component.category_code &&
                        categoryNameByCode.get(component.category_code)) ||
                        "—"}
                    </td>
                    <td className="px-3 py-2">
                      {currencyFormatter.format(component.estimated_cost)}
                    </td>
                    <td className="px-3 py-2">{component.initial_year}</td>
                    <td className="px-3 py-2">
                      {component.expected_life_years} yrs
                    </td>
                    <td className="px-3 py-2 text-slate-500 dark:text-slate-400">
                      {component.notes || "—"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {confirmDeleteId === component.id ? (
                        <span className="inline-flex items-center gap-3">
                          <span className="text-slate-500 dark:text-slate-400">
                            Delete?
                          </span>
                          <button
                            onClick={() => handleConfirmDelete(component.id)}
                            disabled={deleteComponent.isPending}
                            className="text-sm font-medium text-red-600 hover:underline disabled:opacity-50 dark:text-red-400"
                          >
                            Confirm
                          </button>
                          <button
                            onClick={() => setConfirmDeleteId(null)}
                            className="text-sm font-medium text-slate-600 hover:underline dark:text-slate-300"
                          >
                            Cancel
                          </button>
                        </span>
                      ) : isMainBranch ? (
                        <span className="text-sm text-slate-400 dark:text-slate-600">
                          read-only
                        </span>
                      ) : (
                        <>
                          <button
                            onClick={() => setMode({ editingId: component.id })}
                            className="mr-3 text-sm font-medium text-slate-600 hover:underline dark:text-slate-300"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setConfirmDeleteId(component.id)}
                            className="text-sm font-medium text-red-600 hover:underline dark:text-red-400"
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
