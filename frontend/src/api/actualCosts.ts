import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { apiFetch } from "./client";
import type {
  ActualCostPreview,
  EditActualInput,
  RecordActualInput,
} from "../types/actualCost";

// Recording moves a component's schedule and can change its estimate, so
// everything derived from costs and components has to refetch.
function refreshAfterChange(queryClient: QueryClient) {
  queryClient.invalidateQueries({ queryKey: ["projections"] });
  queryClient.invalidateQueries({ queryKey: ["components"] });
}

export function useActualCostPreview(componentId: string, year: number) {
  return useQuery({
    queryKey: ["actual-cost-preview", componentId, year],
    queryFn: () =>
      apiFetch<ActualCostPreview>(
        `/actual-costs/preview?component_id=${encodeURIComponent(componentId)}&year=${year}`,
      ),
    gcTime: 0,
  });
}

export function useRecordActual() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RecordActualInput) =>
      apiFetch<unknown>("/actual-costs", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => refreshAfterChange(queryClient),
  });
}

export function useEditActual() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ componentId, year, cost, comment }: EditActualInput) =>
      apiFetch<unknown>(
        `/actual-costs/${encodeURIComponent(componentId)}/${year}`,
        { method: "PUT", body: JSON.stringify({ cost, comment }) },
      ),
    onSuccess: () => refreshAfterChange(queryClient),
  });
}

export function useDeleteActual() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ componentId, year }: { componentId: string; year: number }) =>
      apiFetch<void>(
        `/actual-costs/${encodeURIComponent(componentId)}/${year}`,
        { method: "DELETE" },
      ),
    onSuccess: () => refreshAfterChange(queryClient),
  });
}
