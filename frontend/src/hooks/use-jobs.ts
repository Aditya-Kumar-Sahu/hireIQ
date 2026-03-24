"use client";

import { useQuery } from "@tanstack/react-query";

import { getJob, listJobs } from "@/lib/api";

export function useJobs(
  token: string | null,
  searchParams?: { status?: string; page?: number; limit?: number },
) {
  return useQuery({
    queryKey: ["jobs", token, searchParams],
    queryFn: () => listJobs(token, searchParams),
    enabled: Boolean(token),
  });
}

export function useJob(token: string | null, jobId: string | undefined) {
  return useQuery({
    queryKey: ["jobs", "detail", token, jobId],
    queryFn: () => getJob(token, jobId!),
    enabled: Boolean(token && jobId),
  });
}
