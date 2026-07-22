import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type {
  SurpriseContribution,
  SurpriseContributionInput,
  YearParameterPatch,
  YearParameters,
} from "../types/parameters";

const parametersKey = ["parameters"];
const surpriseKey = ["surprise-contributions"];

export function useYearParameters() {
  return useQuery({
    queryKey: parametersKey,
    queryFn: () => apiFetch<YearParameters[]>("/parameters"),
  });
}

export function usePatchYearParameters() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      year,
      patch,
    }: {
      year: number;
      patch: YearParameterPatch;
    }) =>
      apiFetch<YearParameters>(`/parameters/${year}`, {
        method: "PATCH",
        body: JSON.stringify(patch),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: parametersKey });
      queryClient.invalidateQueries({ queryKey: ["projections"] });
    },
  });
}

export function useSurpriseContributions() {
  return useQuery({
    queryKey: surpriseKey,
    queryFn: () => apiFetch<SurpriseContribution[]>("/surprise-contributions"),
  });
}

export function useCreateSurpriseContribution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SurpriseContributionInput) =>
      apiFetch<SurpriseContribution>("/surprise-contributions", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: surpriseKey });
      queryClient.invalidateQueries({ queryKey: ["projections"] });
    },
  });
}

export function useDeleteSurpriseContribution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiFetch<void>(`/surprise-contributions/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: surpriseKey });
      queryClient.invalidateQueries({ queryKey: ["projections"] });
    },
  });
}
