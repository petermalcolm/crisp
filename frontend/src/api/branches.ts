import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { BranchesState } from "../types/branches";

const branchesKey = ["branches"];

export function useBranches() {
  return useQuery({
    queryKey: branchesKey,
    queryFn: () => apiFetch<BranchesState>("/branches"),
  });
}

export function useIsMainBranch() {
  const { data } = useBranches();
  // Default to read-only while branch state is still loading/unknown, so
  // editable controls never flash briefly before settling.
  return data ? data.current === "main" : true;
}

export function useCreateBranch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiFetch<BranchesState>("/branches", {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

export function useCheckoutBranch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiFetch<BranchesState>("/branches/checkout", {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
    onSuccess: () => queryClient.invalidateQueries(),
  });
}

export function useMergeBranch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiFetch<BranchesState>(`/branches/${encodeURIComponent(name)}/merge`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: () => queryClient.invalidateQueries(),
  });
}
