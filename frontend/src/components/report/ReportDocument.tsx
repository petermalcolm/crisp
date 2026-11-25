import { formatDollars } from "../../lib/currency";
import type {
  Extreme,
  ReportData,
  ScheduleYear,
} from "../../types/report";
import { ProjectionChart } from "./ProjectionChart";

const pct = (v: number | null | undefined, digits = 1) =>
  v === null || v === undefined ? "—" : `${(v * 100).toFixed(digits)}%`;
const usd = (v: number | null | undefined) =>
  v === null || v === undefined ? "—" : formatDollars(v);

function describeRate(values: number[]): string {
  if (values.length === 0) return "—";
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  return lo === hi ? `${pct(lo)} per year` : `${pct(lo)} to ${pct(hi)} per year`;
}

/** Escape text for use inside a double-quoted CSS string. */
function cssString(text: string): string {
  return text.replace(/[\\"]/g, "\\$&").replace(/[\r\n]+/g, " ");
}

const TERM_TITLES: Record<ScheduleYear["term"], string> = {
  near: "Near term",
  mid: "Mid term",
  long: "Long term",
};

const th = "border-b border-slate-400 px-2 py-1 text-left font-semibold";
const thr = `${th} text-right`;
const td = "border-b border-slate-200 px-2 py-1";
const tdr = `${td} text-right tabular-nums`;

function Section({
  id,
  title,
  children,
  pageBreak = false,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
  pageBreak?: boolean;
}) {
  return (
    <section id={id} className={`mt-8 ${pageBreak ? "report-page-break" : ""}`}>
      <h2 className="mb-3 border-b-2 border-slate-800 pb-1 text-xl font-bold">
        {title}
      </h2>
      {children}
    </section>
  );
}

function ExtremeCells({
  extreme,
  format,
}: {
  extreme: Extreme | null;
  format: (v: number) => string;
}) {
  if (!extreme) return <td className={tdr} colSpan={1}>—</td>;
  return (
    <td className={tdr}>
      {format(extreme.value)}{" "}
      <span className="text-slate-500">({extreme.year})</span>
    </td>
  );
}

export function ReportDocument({ report }: { report: ReportData }) {
  const { meta, settings, at_a_glance: glance, summary, projection } = report;
  const windowLabel = `${meta.window_start}–${meta.window_end}`;
  const budget = glance.budget;
  const specialPlanned = summary.total_special_contributions;

  const stamp = `${settings.association_name || "Reserve fund report"} · generated ${
    meta.generated_on
  } from ${meta.branch}${meta.data_commit ? ` @ ${meta.data_commit}` : ""}`;

  const contributions = projection.map((p) => p.contribution);
  const inflation = projection.map((p) => p.inflation_rate);
  const interest = projection.map((p) => p.interest_rate);

  return (
    <article className="report-paper relative mx-auto max-w-[8.5in] bg-white p-8 text-[13px] leading-snug text-slate-900 shadow print:max-w-none print:p-0 print:shadow-none">
      {meta.is_draft && (
        <div
          aria-hidden
          className="pointer-events-none fixed inset-0 z-10 flex items-center justify-center"
        >
          <span className="-rotate-30 select-none text-6xl font-black tracking-widest text-red-600/15 print:text-red-600/20">
            DRAFT — FORECAST SCENARIO
          </span>
        </div>
      )}

      {/* Cover */}
      <header>
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-600">
          {settings.association_name || "[Association name]"}
        </p>
        <h1 className="mt-1 text-3xl font-bold">
          Reserve Fund Schedule and 30-Year Projection
        </h1>
        <p className="mt-1 text-lg">{windowLabel}</p>
        {settings.association_address && (
          <p className="mt-2 whitespace-pre-line text-slate-700">
            {settings.association_address}
          </p>
        )}
        <p className="mt-3 text-slate-700">
          {settings.prepared_by && <>Prepared by {settings.prepared_by}. </>}
          Dated {meta.generated_on}.
        </p>
        {meta.is_draft && (
          <p className="mt-3 rounded border border-red-600 px-3 py-2 font-semibold text-red-700">
            DRAFT: generated from forecast scenario “{meta.branch}”, not the
            association’s current record.
          </p>
        )}
        <h3 className="mt-4 font-semibold">Basis of preparation</h3>
        <p className="whitespace-pre-line">{settings.basis_statement}</p>
        {settings.study_reference && (
          <p className="mt-2">
            <span className="font-semibold">Independent reserve study: </span>
            {settings.study_reference}
          </p>
        )}
      </header>

      <nav className="mt-5 text-sm" aria-label="Contents">
        <h3 className="font-semibold">Contents</h3>
        <ol className="ml-5 list-decimal">
          <li>Reserve Fund at a Glance</li>
          <li>Schedule of Maintenance and Projects</li>
          <li>30-Year Financial Projection</li>
          <li>Assumptions</li>
        </ol>
        <p className="ml-1">Appendix A: Component Inventory</p>
      </nav>

      {/* 1. At a glance */}
      <Section id="glance" title="1. Reserve Fund at a Glance">
        <table className="w-full border-collapse">
          <tbody>
            <tr>
              <td className={td}>Reserve fund balance, January 1, {meta.window_start}</td>
              <td className={tdr}>{usd(glance.start_balance)}</td>
            </tr>
            <tr>
              <td className={td}>Fully funded balance, January 1, {meta.window_start}</td>
              <td className={tdr}>{usd(glance.start_ffb)}</td>
            </tr>
            <tr>
              <td className={td}>Reserve funding percent of fully funded balance</td>
              <td className={tdr}>{pct(glance.start_percent_funded)}</td>
            </tr>
            {budget && (
              <>
                <tr>
                  <td className={td}>{budget.year} operating budget</td>
                  <td className={tdr}>{usd(budget.operating)}</td>
                </tr>
                <tr>
                  <td className={td}>{budget.year} reserve contribution</td>
                  <td className={tdr}>{usd(budget.reserves)}</td>
                </tr>
                <tr>
                  <td className={td}>{budget.year} total budget</td>
                  <td className={tdr}>{usd(budget.total)}</td>
                </tr>
                <tr>
                  <td className={td}>Reserve contribution as a share of the total budget</td>
                  <td className={tdr}>{pct(budget.reserve_share)}</td>
                </tr>
              </>
            )}
            <tr>
              <td className={td}>Special assessments planned, {windowLabel}</td>
              <td className={tdr}>
                {specialPlanned > 0 ? usd(specialPlanned) : "None planned"}
              </td>
            </tr>
          </tbody>
        </table>
        {settings.financial_disclosures && (
          <p className="mt-2 whitespace-pre-line">{settings.financial_disclosures}</p>
        )}
      </Section>

      {/* 2. Schedule */}
      <Section id="schedule" title="2. Schedule of Maintenance and Projects" pageBreak>
        <p className="mb-3">
          Planned replacement and major repair of the association’s common
          components, {windowLabel}. Costs are projected in the dollars of the
          year of the work (estimates in {meta.cost_base_year} dollars,
          inflated at the assumed rate). Items marked “actual” have been
          completed or contracted at a known cost.
        </p>
        {(["near", "mid", "long"] as const).map((term) => {
          const years = report.schedule.filter((s) => s.term === term);
          if (years.length === 0) return null;
          return (
            <div key={term} className="mb-4">
              <h3 className="mb-1 text-base font-semibold">
                {TERM_TITLES[term]}: {years[0].year}–{years[years.length - 1].year}
              </h3>
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    <th className={th} style={{ width: "3.5rem" }}>Year</th>
                    <th className={th}>Component</th>
                    <th className={th}>Category</th>
                    <th className={thr}>Cost</th>
                  </tr>
                </thead>
                {years.map((y) => (
                  <tbody key={y.year} className="report-keep-together">
                    {y.items.map((item, i) => (
                      <tr key={i}>
                        <td className={td}>{i === 0 ? y.year : ""}</td>
                        <td className={td}>
                          {item.component_name}
                          {item.is_actual && (
                            <span className="ml-1 text-slate-500">(actual)</span>
                          )}
                        </td>
                        <td className={td}>{item.category_name ?? ""}</td>
                        <td className={tdr}>{usd(item.cost)}</td>
                      </tr>
                    ))}
                    {y.items.length > 1 && (
                      <tr className="font-semibold">
                        <td className={td} />
                        <td className={td} colSpan={2}>Total {y.year}</td>
                        <td className={tdr}>{usd(y.total)}</td>
                      </tr>
                    )}
                  </tbody>
                ))}
              </table>
            </div>
          );
        })}

        {report.completed_projects.length > 0 && (
          <div className="mt-4">
            <h3 className="mb-1 text-base font-semibold">
              Recently completed projects (actual cost)
            </h3>
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className={th} style={{ width: "3.5rem" }}>Year</th>
                  <th className={th}>Component</th>
                  <th className={th}>Category</th>
                  <th className={thr}>Cost</th>
                </tr>
              </thead>
              <tbody>
                {report.completed_projects.map((c, i) => (
                  <tr key={i}>
                    <td className={td}>{c.year}</td>
                    <td className={td}>{c.component_name}</td>
                    <td className={td}>{c.category_name ?? ""}</td>
                    <td className={tdr}>{usd(c.cost)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* 3. Projection */}
      <Section id="projection" title="3. 30-Year Financial Projection" pageBreak>
        <h3 className="mb-1 text-base font-semibold">
          Summary of the projection, {windowLabel}
        </h3>
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className={th}></th>
              <th className={thr}>Minimum (year)</th>
              <th className={thr}>Maximum (year)</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className={td}>Reserve fund balance (January 1)</td>
              <ExtremeCells extreme={summary.balance_min} format={usd} />
              <ExtremeCells extreme={summary.balance_max} format={usd} />
            </tr>
            <tr>
              <td className={td}>Annual reserve fund contribution</td>
              <ExtremeCells extreme={summary.contribution_min} format={usd} />
              <ExtremeCells extreme={summary.contribution_max} format={usd} />
            </tr>
            <tr>
              <td className={td}>Reserve funding percent of fully funded balance</td>
              <ExtremeCells extreme={summary.percent_funded_min} format={(v) => pct(v)} />
              <ExtremeCells extreme={summary.percent_funded_max} format={(v) => pct(v)} />
            </tr>
            <tr className="font-semibold">
              <td className={td}>Average annual reserve funding percent of fully funded balance</td>
              <td className={tdr} colSpan={2}>{pct(summary.percent_funded_avg)}</td>
            </tr>
          </tbody>
        </table>
        <p className="mt-2">
          Over {windowLabel} the plan contributes {usd(summary.total_contributions)} to
          the reserve fund and spends {usd(summary.total_costs)} on the projects
          scheduled above.{" "}
          {summary.first_shortfall_year === null
            ? "The projected reserve balance remains positive throughout."
            : `The projected reserve balance becomes negative in ${summary.first_shortfall_year}.`}
        </p>

        <div className="mt-4">
          <ProjectionChart years={projection} />
        </div>

        <h3 className="mb-1 mt-5 text-base font-semibold">Year-by-year projection</h3>
        <table className="w-full border-collapse text-[11px]">
          <thead>
            <tr>
              <th className={th}>Year</th>
              <th className={thr}>Balance Jan 1</th>
              <th className={thr}>Contribution</th>
              <th className={thr}>Special</th>
              <th className={thr}>Interest</th>
              <th className={thr}>Spending</th>
              <th className={thr}>Balance Dec 31</th>
              <th className={thr}>Fully funded</th>
              <th className={thr}>% funded</th>
            </tr>
          </thead>
          <tbody>
            {projection.map((p) => (
              <tr key={p.year}>
                <td className={td}>{p.year}</td>
                <td className={tdr}>{usd(p.start_balance)}</td>
                <td className={tdr}>{usd(p.contribution)}</td>
                <td className={tdr}>{p.special_contribution ? usd(p.special_contribution) : "—"}</td>
                <td className={tdr}>{usd(p.interest)}</td>
                <td className={tdr}>{usd(p.costs)}</td>
                <td className={tdr}>{usd(p.end_balance)}</td>
                <td className={tdr}>{usd(p.ffb)}</td>
                <td className={tdr}>{pct(p.percent_funded, 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      {/* 4. Assumptions */}
      <Section id="assumptions" title="4. Assumptions">
        <ul className="ml-5 list-disc space-y-1">
          <li>
            Component costs are estimated in {meta.cost_base_year} dollars and
            inflated at {describeRate(inflation)}.
          </li>
          <li>
            Interest earned on reserve balances: {describeRate(interest)}.
          </li>
          <li>
            Annual reserve contribution: {usd(contributions[0])} in{" "}
            {meta.window_start}, changing to {usd(contributions[contributions.length - 1])}{" "}
            by {meta.window_end}.
          </li>
          <li>
            Each component is replaced at the end of its expected useful life,
            and again after each further full life within the period.
          </li>
          <li>
            <b>Fully funded balance</b> is the reserve balance the association
            would hold if every component had been saved for evenly over its
            useful life: the sum, over all components, of replacement cost in
            that year’s dollars times the share of useful life already used.
            Balances and fully funded balances are stated at the start of
            each year (January 1).
          </li>
          <li>
            <b>Reserve funding percent</b> is the January 1 reserve balance
            divided by the January 1 fully funded balance.
          </li>
        </ul>
      </Section>

      {/* Appendix A */}
      <Section id="inventory" title="Appendix A: Component Inventory" pageBreak>
        <p className="mb-2">
          Costs are in {meta.cost_base_year} dollars. “Next” is the first scheduled
          replacement within {windowLabel}.
        </p>
        <table className="w-full border-collapse text-[11px]">
          <thead>
            <tr>
              <th className={th}>Component</th>
              <th className={th}>Category</th>
              <th className={thr}>Cost</th>
              <th className={thr}>Life (yrs)</th>
              <th className={thr}>Next</th>
            </tr>
          </thead>
          <tbody>
            {report.inventory.map((c, i) => (
              <tr key={i}>
                <td className={td}>{c.component_name}</td>
                <td className={td}>{c.category_name ?? ""}</td>
                <td className={tdr}>{usd(c.estimated_cost)}</td>
                <td className={tdr}>{c.expected_life_years}</td>
                <td className={tdr}>{c.next_year ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      {/* The same stamp is printed in the bottom margin of every page. */}
      <style>{`@page { @bottom-left { content: "${cssString(stamp)}"; width: 78%; text-align: left; font-size: 8pt; color: #6b7280; } }`}</style>
      <footer className="mt-8 border-t border-slate-300 pt-2 text-[10px] text-slate-500 print:hidden">
        {stamp}
      </footer>
    </article>
  );
}
