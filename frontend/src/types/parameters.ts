export interface ResolvedField {
  value: number | null;
  is_explicit: boolean;
  source_year: number | null;
}

export interface YearParameters {
  year: number;
  num_contributors: number | null;
  inflation_rate: ResolvedField;
  interest_rate: ResolvedField;
  yoy_contribution_change_pct: ResolvedField;
  total_annual_contribution: ResolvedField;
  current_reserve_balance: number | null;
  notes: string | null;
}

export interface YearParameterPatch {
  num_contributors?: number | null;
  inflation_rate?: number | null;
  interest_rate?: number | null;
  yoy_contribution_change_pct?: number | null;
  total_annual_contribution?: number | null;
  current_reserve_balance?: number | null;
  notes?: string | null;
}

export interface SurpriseContribution {
  id: string;
  year: number;
  amount: number;
  description: string | null;
}

export type SurpriseContributionInput = Omit<SurpriseContribution, "id">;
