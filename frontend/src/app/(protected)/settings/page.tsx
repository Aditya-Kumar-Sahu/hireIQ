"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  disconnectGoogleCalendar,
  getApiErrorMessage,
  getGoogleCalendarAuthorizationUrl,
} from "@/lib/api";
import { useIntegrations } from "@/hooks/use-meta";

function StatusBadge({ enabled }: { enabled: boolean }) {
  return (
    <Badge variant={enabled ? "success" : "warning"}>
      {enabled ? "Configured" : "Preview mode"}
    </Badge>
  );
}

export default function SettingsPage() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { token, user } = useSession();
  const integrationsQuery = useIntegrations(token);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const connectMutation = useMutation({
    mutationFn: () => getGoogleCalendarAuthorizationUrl(token),
  });
  const disconnectMutation = useMutation({
    mutationFn: () => disconnectGoogleCalendar(token),
  });

  useEffect(() => {
    const googleState = searchParams.get("google");
    const reason = searchParams.get("reason");
    if (googleState === "connected") {
      setNotice("Google Calendar is now connected to this workspace.");
    } else if (googleState === "error") {
      setNotice(reason ? `Google Calendar connection failed: ${reason}` : "Google Calendar connection failed.");
    } else if (googleState === "disconnected") {
      setNotice("Google Calendar has been disconnected.");
    }
  }, [searchParams]);

  async function handleConnectGoogleCalendar() {
    setError(null);
    try {
      const response = await connectMutation.mutateAsync();
      window.location.assign(response.authorization_url);
    } catch (connectError) {
      setError(
        getApiErrorMessage(connectError, "Unable to start Google Calendar connection", {
          401: "Your session expired. Please log in again.",
        }),
      );
    }
  }

  async function handleDisconnectGoogleCalendar() {
    setError(null);
    try {
      await disconnectMutation.mutateAsync();
      await queryClient.invalidateQueries({ queryKey: ["meta", "integrations"] });
      setNotice("Google Calendar has been disconnected.");
    } catch (disconnectError) {
      setError(
        getApiErrorMessage(disconnectError, "Unable to disconnect Google Calendar", {
          401: "Your session expired. Please log in again.",
        }),
      );
    }
  }

  const integrationStatus = integrationsQuery.data;
  const isLoading = integrationsQuery.isLoading;
  const activeError = error
    ?? (integrationsQuery.error
      ? getApiErrorMessage(integrationsQuery.error, "Unable to load integrations", {
          401: "Your session expired. Please log in again.",
        })
      : null);

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="eyebrow">Settings</p>
        <h1 className="section-title">Workspace configuration</h1>
        <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
          Check which integrations are running live, connect Google Calendar for scheduling, and
          hand the ATS team the webhook URL for inbound delivery events.
        </p>
      </section>

      {notice ? (
        <Card className="border-[rgba(17,118,89,0.14)] bg-[rgba(239,252,247,0.9)]">
          <CardTitle className="text-xl">Integration update</CardTitle>
          <CardDescription>{notice}</CardDescription>
        </Card>
      ) : null}

      {activeError ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <CardTitle className="text-xl">Unable to load settings</CardTitle>
          <CardDescription>{activeError}</CardDescription>
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
            {isLoading && !integrationStatus ? (
              Array.from({ length: 5 }, (_, index) => <Skeleton key={index} className="h-28 w-full" />)
            ) : (
              <>
                <div className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 px-4 py-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold">Google Calendar scheduling</p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        {integrationStatus?.google_calendar_connected_email
                          ? `Connected as ${integrationStatus.google_calendar_connected_email}.`
                          : "Authorize a recruiter calendar so the scheduler can create live interview events."}
                      </p>
                    </div>
                    <StatusBadge enabled={integrationStatus?.google_calendar_enabled ?? false} />
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    {integrationStatus?.google_calendar_enabled ? (
                      <Button
                        data-testid="google-calendar-disconnect"
                        disabled={disconnectMutation.isPending}
                        type="button"
                        variant="secondary"
                        onClick={handleDisconnectGoogleCalendar}
                      >
                        Disconnect Google Calendar
                      </Button>
                    ) : (
                      <Button
                        data-testid="google-calendar-connect"
                        disabled={connectMutation.isPending}
                        type="button"
                        onClick={handleConnectGoogleCalendar}
                      >
                        Connect Google Calendar
                      </Button>
                    )}
                  </div>
                </div>

                {[
                  {
                    label: "Google Gemini reasoning + embeddings",
                    enabled: integrationStatus?.gemini_enabled ?? false,
                    detail: "Screening and semantic ranking automatically fall back when the Gemini key is absent.",
                  },
                  {
                    label: "Resend outbound email",
                    enabled: integrationStatus?.resend_enabled ?? false,
                    detail: "Live interview and offer emails switch to preview-safe metadata without credentials.",
                  },
                  {
                    label: "Cloudflare R2 resume storage",
                    enabled: integrationStatus?.resume_storage_enabled ?? false,
                    detail: "Multipart PDF uploads persist the original resume for later download when configured.",
                  },
                  {
                    label: "SSE application feed",
                    enabled: integrationStatus?.sse_enabled ?? true,
                    detail: "Live pipeline progress stays available even when providers fall back to preview mode.",
                  },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="flex items-center justify-between gap-4 rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 px-4 py-4"
                  >
                    <div>
                      <p className="font-semibold">{item.label}</p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">{item.detail}</p>
                    </div>
                    <StatusBadge enabled={item.enabled} />
                  </div>
                ))}

                <div className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 px-4 py-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold">ATS webhooks</p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        Share this endpoint with your ATS so inbound application and status events are
                        signature-verified and logged.
                      </p>
                    </div>
                    <StatusBadge enabled={integrationStatus?.ats_webhooks_enabled ?? false} />
                  </div>
                  <div className="mt-4 rounded-2xl border border-[color:var(--line)] bg-[rgba(247,243,236,0.8)] px-4 py-3">
                    <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
                      Webhook URL
                    </p>
                    <p className="mt-2 break-all text-sm font-semibold">
                      {integrationStatus?.ats_webhook_url ?? "Loading..."}
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
