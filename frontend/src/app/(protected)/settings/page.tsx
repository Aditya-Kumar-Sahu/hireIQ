"use client";

import { useEffect, useState } from "react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getIntegrations } from "@/lib/api";
import type { IntegrationStatus } from "@/lib/types";

function StatusBadge({ enabled }: { enabled: boolean }) {
  return <Badge variant={enabled ? "success" : "warning"}>{enabled ? "Configured" : "Preview mode"}</Badge>;
}

export default function SettingsPage() {
  const { token, user } = useSession();
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    async function load() {
      setError(null);
      try {
        const response = await getIntegrations(token);
        if (!cancelled) {
          setIntegrationStatus(response);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load integrations");
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="eyebrow">Settings</p>
        <h1 className="section-title">Workspace configuration</h1>
        <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
          Check which integrations are running live, confirm the recruiter identity tied to this
          workspace, and verify the frontend is pointed at the correct backend.
        </p>
      </section>

      {error ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <CardTitle className="text-xl">Unable to load settings</CardTitle>
          <CardDescription>{error}</CardDescription>
        </Card>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <p className="eyebrow">Account</p>
          <CardTitle className="mt-2 text-3xl">Recruiter identity</CardTitle>
          <div className="mt-6 space-y-4 rounded-[1.3rem] border border-[color:var(--line)] bg-white/75 p-5">
            <div>
              <p className="text-sm text-[color:var(--muted)]">Email</p>
              <p className="mt-1 text-base font-semibold">{user?.email ?? "Unknown"}</p>
            </div>
            <div>
              <p className="text-sm text-[color:var(--muted)]">Role</p>
              <p className="mt-1 text-base font-semibold">{user?.role ?? "Unknown"}</p>
            </div>
            <div>
              <p className="text-sm text-[color:var(--muted)]">Company ID</p>
              <p className="mt-1 break-all text-sm font-semibold">{user?.company_id ?? "Unknown"}</p>
            </div>
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Integrations</p>
          <CardTitle className="mt-2 text-3xl">Backend delivery status</CardTitle>
          <div className="mt-6 grid gap-3">
            {[
              {
                label: "OpenAI reasoning + embeddings",
                enabled: integrationStatus?.openai_enabled ?? false,
              },
              {
                label: "Google Calendar scheduling",
                enabled: integrationStatus?.google_calendar_enabled ?? false,
              },
              {
                label: "Resend outbound email",
                enabled: integrationStatus?.resend_enabled ?? false,
              },
              {
                label: "SSE application feed",
                enabled: integrationStatus?.sse_enabled ?? true,
              },
            ].map((item) => (
              <div
                key={item.label}
                className="flex items-center justify-between gap-4 rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 px-4 py-4"
              >
                <div>
                  <p className="font-semibold">{item.label}</p>
                  <p className="mt-1 text-sm text-[color:var(--muted)]">
                    {item.enabled
                      ? "Running against live provider credentials."
                      : "Gracefully falling back to preview-safe local behavior."}
                  </p>
                </div>
                <StatusBadge enabled={item.enabled} />
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}
