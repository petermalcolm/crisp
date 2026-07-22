import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { YearFFBRow } from "../types/ffb";

export function useFFBProjection() {
  return useQuery({
    queryKey: ["projections", "ffb"],
    queryFn: () => apiFetch<YearFFBRow[]>("/projections/ffb"),
  });
}
