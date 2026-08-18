import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { Category } from "../types/category";

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => apiFetch<Category[]>("/categories"),
  });
}
