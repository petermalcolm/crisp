import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { YearCostRow } from "../types/costs";

export function useCostsProjection() {
  return useQuery({
    queryKey: ["projections", "costs"],
    queryFn: () => apiFetch<YearCostRow[]>("/projections/costs"),
  });
}
