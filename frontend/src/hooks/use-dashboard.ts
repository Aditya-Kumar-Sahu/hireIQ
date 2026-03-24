"use client";

import { useQuery } from "@tanstack/react-query";

import { getDashboardActivity, getDashboardStats } from "@/lib/api";

export function useDashboardStats(token: string | null) {
  return useQuery({
    queryKey: ["dashboard", "stats", token],
    queryFn: () => getDashboardStats(token),
    enabled: Boolean(token),
  });
}

export function useDashboardActivity(token: string | null, limit = 12) {
  return useQuery({
    queryKey: ["dashboard", "activity", token, limit],
    queryFn: () => getDashboardActivity(token, limit),
    enabled: Boolean(token),
  });
}
