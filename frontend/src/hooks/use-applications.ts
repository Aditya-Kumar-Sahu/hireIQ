"use client";

import { useQuery } from "@tanstack/react-query";

import { getApplication, getSimilarJobsForApplication, listApplications } from "@/lib/api";

export function useApplications(
  token: string | null,
  searchParams?: { job_id?: string; status?: string; page?: number; limit?: number },
) {
  return useQuery({
    queryKey: ["applications", token, searchParams],
    queryFn: () => listApplications(token, searchParams),
    enabled: Boolean(token),
  });
}

export function useApplication(token: string | null, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["applications", "detail", token, applicationId],
    queryFn: () => getApplication(token, applicationId!),
    enabled: Boolean(token && applicationId),
  });
}

export function useSimilarJobsForApplication(token: string | null, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["applications", "similar-jobs", token, applicationId],
    queryFn: () => getSimilarJobsForApplication(token, applicationId!),
    enabled: Boolean(token && applicationId),
  });
}
