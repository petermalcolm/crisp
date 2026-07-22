export interface YearFFBRow {
  year: number;
  is_estimate: boolean;
  ffb_target: number;
  actual_balance: number | null;
  percent_funded: number | null;
}
