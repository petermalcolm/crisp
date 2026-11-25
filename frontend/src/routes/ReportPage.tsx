import { useIsMainBranch } from "../api/branches";
import { useReport } from "../api/report";
import { ReportDocument } from "../components/report/ReportDocument";
import { ReportSettingsForm } from "../components/report/ReportSettingsForm";
import { ReadOnlyBanner } from "../components/shared/ReadOnlyBanner";

export function ReportPage() {
  const { data, isLoading, isError, error } = useReport();
  const isMainBranch = useIsMainBranch();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <h1 className="text-xl font-semibold">Lender Report</h1>
        <button
          onClick={() => window.print()}
          disabled={!data}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900"
        >
          Print / Save as PDF
        </button>
      </div>

      {isLoading && <p className="text-slate-500 dark:text-slate-400">Loading…</p>}
      {isError && (
        <p className="text-red-600 dark:text-red-400">
          Failed to load report: {(error as Error).message}
        </p>
      )}

      {data && (
        <>
          <div className="space-y-4 print:hidden">
            {data.warnings.length > 0 && (
              <ul className="space-y-1 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:bg-amber-900/30 dark:text-amber-200">
                {data.warnings.map((w) => (
                  <li key={w.code}>⚠ {w.message}</li>
                ))}
              </ul>
            )}
            <details className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
              <summary className="cursor-pointer text-sm font-semibold">
                Report settings
              </summary>
              <div className="mt-4 space-y-3">
                {isMainBranch && <ReadOnlyBanner />}
                <ReportSettingsForm settings={data.settings} />
              </div>
            </details>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              In the print dialog choose “Save as PDF”, and turn off “Headers
              and footers”. For a lender, generate the report from{" "}
              <strong>main</strong>.
            </p>
          </div>
          <ReportDocument report={data} />
        </>
      )}
    </div>
  );
}
