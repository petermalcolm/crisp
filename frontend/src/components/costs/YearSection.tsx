import type { CostLineItem, YearCostRow } from "../../types/costs";
import { EstimateBadge } from "../shared/EstimateBadge";
import { ItemPill } from "./ItemPill";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function YearSection({
  row,
  canEdit,
  onPillClick,
}: {
  row: YearCostRow;
  canEdit: boolean;
  onPillClick: (item: CostLineItem, year: number) => void;
}) {
  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-800">
      <header className="flex items-center justify-between bg-slate-100 px-4 py-2 dark:bg-slate-900">
        <h2 className="text-base font-semibold">{row.year}</h2>
        <EstimateBadge isEstimate={row.is_estimate} />
      </header>
      {row.line_items.length > 0 ? (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {row.line_items.map((item) => (
            <li
              key={item.component_id}
              className="flex items-center justify-between gap-3 px-4 py-2 text-sm"
            >
              <span className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                <span>{item.component_name}</span>
                <ItemPill
                  isActual={item.is_actual}
                  canEdit={canEdit}
                  label={`${item.is_actual ? "Edit actual cost" : "Record actual cost"} for ${item.component_name}, ${row.year}`}
                  onClick={() => onPillClick(item, row.year)}
                />
                {item.is_actual && item.comment && (
                  <span className="text-xs italic text-slate-500 dark:text-slate-400">
                    {item.comment}
                  </span>
                )}
              </span>
              <span className={item.is_actual ? "font-medium" : undefined}>
                {currencyFormatter.format(item.cost)}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="px-4 py-2 text-sm text-slate-400 dark:text-slate-500">
          No costs this year
        </p>
      )}
      <footer className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold dark:border-slate-800 dark:bg-slate-900/50">
        <span>Total</span>
        <span>{currencyFormatter.format(row.total)}</span>
      </footer>
    </section>
  );
}
