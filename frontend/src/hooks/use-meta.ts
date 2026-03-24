"use client";

import { useQuery } from "@tanstack/react-query";

import { getIntegrations } from "@/lib/api";

export function useIntegrations(token: string | null) {
  return useQuery({
    queryKey: ["meta", "integrations", token],
    queryFn: () => getIntegrations(token),
    enabled: Boolean(token),
  });
}
