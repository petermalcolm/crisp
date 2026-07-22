export interface Component {
  id: string;
  name: string;
  estimated_cost: number;
  initial_year: number;
  expected_life_years: number;
  notes: string | null;
}

export type ComponentInput = Omit<Component, "id">;
