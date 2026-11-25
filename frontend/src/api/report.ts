import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { ReportData, ReportSettings } from "../types/report";

// Under "projections" so any edit that invalidates projections refreshes the
// report too.
const reportKey = ["projections", "report"];
const settingsKey = ["report-settings"];

export function useReport() {
  return useQuery({
    queryKey: reportKey,
    queryFn: () => apiFetch<ReportData>("/report"),
  });
}

export function useReportSettings() {
  return useQuery({
    queryKey: settingsKey,
    queryFn: () => apiFetch<ReportSettings>("/report-settings"),
  });
}

export function usePutReportSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: ReportSettings) =>
      apiFetch<ReportSettings>("/report-settings", {
        method: "PUT",
        body: JSON.stringify(settings),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKey });
      queryClient.invalidateQueries({ queryKey: reportKey });
    },
  });
}
