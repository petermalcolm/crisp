export interface BackfillItem {
  year: number;
  cost: number;
}

export interface ActualCostPreview {
  component_id: string;
  component_name: string;
  year: number;
  estimated_cost: number;
  expected_life_years: number;
  new_initial_year: number;
  backfill: BackfillItem[];
}

export type RecurrenceMode = "actual" | "keep" | "other";

export interface RecordActualInput {
  component_id: string;
  year: number;
  cost: number;
  comment: string | null;
  recurrence: { mode: RecurrenceMode; estimate?: number };
}

export interface EditActualInput {
  componentId: string;
  year: number;
  cost: number;
  comment: string | null;
}
