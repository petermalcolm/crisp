export interface CostLineItem {
  component_id: string;
  component_name: string;
  cost: number;
}

export interface YearCostRow {
  year: number;
  is_estimate: boolean;
  line_items: CostLineItem[];
  total: number;
}
