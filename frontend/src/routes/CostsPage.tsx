import { useState } from "react";
import { useIsMainBranch } from "../api/branches";
import { useCostsProjection } from "../api/costs";
import { EditActualDialog } from "../components/costs/EditActualDialog";
import { RecordActualDialog } from "../components/costs/RecordActualDialog";
import { YearSection } from "../components/costs/YearSection";
import { ReadOnlyBanner } from "../components/shared/ReadOnlyBanner";
import type { CostLineItem } from "../types/costs";

type Dialog =
  | { kind: "record"; item: CostLineItem; year: number }
  | { kind: "edit"; item: CostLineItem; year: number };

export function CostsPage() {
  const { data, isLoading, isError, error } = useCostsProjection();
  const isMainBranch = useIsMainBranch();
  const [dialog, setDialog] = useState<Dialog | null>(null);

  function handlePillClick(item: CostLineItem, year: number) {
    setDialog({ kind: item.is_actual ? "edit" : "record", item, year });
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Costs</h1>

      {isMainBranch && <ReadOnlyBanner />}

      {isLoading && (
        <p className="text-slate-500 dark:text-slate-400">Loading…</p>
      )}
      {isError && (
        <p className="text-red-600 dark:text-red-400">
          Failed to load costs: {(error as Error).message}
        </p>
      )}

      {data && (
        <div className="space-y-3">
          {data.map((row) => (
            <YearSection
              key={row.year}
              row={row}
              canEdit={!isMainBranch}
              onPillClick={handlePillClick}
            />
          ))}
        </div>
      )}

      {dialog?.kind === "record" && (
        <RecordActualDialog
          componentId={dialog.item.component_id}
          componentName={dialog.item.component_name}
          year={dialog.year}
          onClose={() => setDialog(null)}
        />
      )}
      {dialog?.kind === "edit" && (
        <EditActualDialog
          componentId={dialog.item.component_id}
          componentName={dialog.item.component_name}
          year={dialog.year}
          initialCost={dialog.item.cost}
          initialComment={dialog.item.comment}
          onClose={() => setDialog(null)}
        />
      )}
    </div>
  );
}
