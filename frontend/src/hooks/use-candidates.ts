"use client";

import { useQuery } from "@tanstack/react-query";

import { getCandidate, getSimilarJobsForCandidate, listCandidates, searchCandidates } from "@/lib/api";

export function useCandidates(
  token: string | null,
  searchParams?: { search?: string; page?: number; limit?: number },
) {
  return useQuery({
    queryKey: ["candidates", token, searchParams],
    queryFn: () => listCandidates(token, searchParams),
    enabled: Boolean(token),
  });
}

export function useCandidate(token: string | null, candidateId: string | undefined) {
  return useQuery({
    queryKey: ["candidates", "detail", token, candidateId],
    queryFn: () => getCandidate(token, candidateId!),
    enabled: Boolean(token && candidateId),
  });
}

export function useCandidateSearch(token: string | null, query: string, enabled: boolean) {
  return useQuery({
    queryKey: ["candidates", "search", token, query],
    queryFn: () => searchCandidates(token, query),
    enabled: Boolean(token && enabled && query.trim()),
  });
}

export function useSimilarJobsForCandidate(token: string | null, candidateId: string | undefined) {
  return useQuery({
    queryKey: ["candidates", "similar-jobs", token, candidateId],
    queryFn: () => getSimilarJobsForCandidate(token, candidateId!),
    enabled: Boolean(token && candidateId),
  });
}
