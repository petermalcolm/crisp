import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { StudySettings } from "../types/studySettings";

const studySettingsKey = ["study-settings"];

export function useStudySettings() {
  return useQuery({
    queryKey: studySettingsKey,
    queryFn: () => apiFetch<StudySettings>("/study-settings"),
  });
}

export function usePutStudySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (costBaseYear: number | null) =>
      apiFetch<StudySettings>("/study-settings", {
        method: "PUT",
        body: JSON.stringify({ cost_base_year: costBaseYear }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: studySettingsKey });
      queryClient.invalidateQueries({ queryKey: ["projections"] });
    },
  });
}
