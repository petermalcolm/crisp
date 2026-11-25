export interface Budget {
  year: number;
  operating: number;
  reserves: number;
}

export interface ReportSettings {
  association_name: string;
  association_address: string;
  prepared_by: string;
  study_reference: string;
  basis_statement: string;
  financial_disclosures: string;
  budget: Budget | null;
  window_start: number | null;
  window_end: number | null;
}

export interface Extreme {
  value: number;
  year: number;
}

export interface ReportSummary {
  balance_min: Extreme | null;
  balance_max: Extreme | null;
  contribution_min: Extreme | null;
  contribution_max: Extreme | null;
  percent_funded_min: Extreme | null;
  percent_funded_max: Extreme | null;
  percent_funded_avg: number | null;
  first_shortfall_year: number | null;
  total_contributions: number;
  total_special_contributions: number;
  total_costs: number;
}

export interface ProjectionYear {
  year: number;
  start_balance: number | null;
  interest: number | null;
  contribution: number;
  special_contribution: number;
  costs: number;
  end_balance: number | null;
  ffb: number;
  percent_funded: number | null;
  inflation_rate: number;
  interest_rate: number;
}

export interface ScheduleItem {
  component_name: string;
  category_code: string | null;
  category_name: string | null;
  cost: number;
  is_actual: boolean;
}

export interface ScheduleYear {
  year: number;
  term: "near" | "mid" | "long";
  total: number;
  items: ScheduleItem[];
}

export interface CompletedProject {
  year: number;
  component_name: string;
  category_name: string | null;
  cost: number;
}

export interface InventoryItem {
  component_name: string;
  category_name: string | null;
  estimated_cost: number;
  expected_life_years: number;
  next_year: number | null;
  occurrences_in_window: number;
}

export interface BudgetSummary {
  year: number;
  operating: number;
  reserves: number;
  total: number;
  reserve_share: number;
}

export interface ReportData {
  meta: {
    generated_on: string;
    branch: string;
    data_commit: string | null;
    is_draft: boolean;
    cost_base_year: number;
    balance_year: number | null;
    window_start: number;
    window_end: number;
  };
  settings: ReportSettings;
  at_a_glance: {
    start_balance: number | null;
    start_ffb: number;
    start_percent_funded: number | null;
    annual_contribution: number;
    budget: BudgetSummary | null;
  };
  summary: ReportSummary;
  projection: ProjectionYear[];
  schedule: ScheduleYear[];
  completed_projects: CompletedProject[];
  inventory: InventoryItem[];
  warnings: { code: string; message: string }[];
}
