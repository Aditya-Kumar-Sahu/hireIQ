"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Activity, ExternalLink, Mail, TimerReset } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { getApiErrorMessage, getApplication, getSimilarJobsForApplication } from "@/lib/api";
import type { ApplicationDetail, SimilarJobResult } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";

type StreamEvent = {
  event: string;
  timestamp: string;
  data: Record<string, unknown>;
};

function getString(value: unknown) {
  return typeof value === "string" ? value : null;
}

function getNumber(value: unknown) {
  return typeof value === "number" ? value : null;
}

function getRecord(value: unknown) {
  return isRecord(value) ? value : null;
}

function getRecordArray(value: unknown) {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatStructuredKey(key: string) {
  return titleCase(key.replace(/\./g, " ").replace(/_/g, " "));
}

function formatTokenCount(tokens: number | null | undefined) {
  return typeof tokens === "number" ? `${tokens} tokens` : "Usage unavailable";
}

function StructuredValue({
  value,
  depth = 0,
}: {
  value: unknown;
  depth?: number;
}) {
  if (value === null || value === undefined) {
    return <span className="text-sm text-[color:var(--muted)]">None</span>;
  }

  if (typeof value === "string") {
    return <p className="break-words text-sm leading-7 text-[color:var(--foreground)]">{value}</p>;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return <p className="text-sm font-medium text-[color:var(--foreground)]">{String(value)}</p>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-sm text-[color:var(--muted)]">None</span>;
    }

    const primitiveItems = value.every(
      (item) =>
        item === null ||
        item === undefined ||
        typeof item === "string" ||
        typeof item === "number" ||
        typeof item === "boolean",
    );

    if (primitiveItems) {
      return (
        <div className="flex flex-wrap gap-2">
          {value.map((item, index) => (
            <Badge key={`${String(item)}-${index}`} variant="default">
              {String(item)}
            </Badge>
          ))}
        </div>
      );
    }

    return (
      <div className="grid gap-3">
        {value.map((item, index) => (
          <div
            key={index}
            className="rounded-2xl border border-[color:var(--line)] bg-[rgba(255,255,255,0.72)] p-3"
          >
            <StructuredValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (isRecord(value)) {
    const entries = Object.entries(value);
    if (entries.length === 0) {
      return <span className="text-sm text-[color:var(--muted)]">None</span>;
    }

    return (
      <div className="grid gap-3">
        {entries.map(([key, entryValue]) => (
          <div
            key={key}
            className="rounded-2xl border border-[color:var(--line)] bg-[rgba(255,255,255,0.58)] p-3"
          >
            <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
              {formatStructuredKey(key)}
            </p>
            <div className="mt-2">
              <StructuredValue value={entryValue} depth={depth + 1} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <p className="text-sm text-[color:var(--foreground)]">{String(value)}</p>;
}

function CollapsibleSection({
  title,
  subtitle,
  defaultOpen = false,
  children,
}: {
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  return (
    <details
      className="rounded-[1.15rem] border border-[color:var(--line)] bg-[rgba(247,243,236,0.72)]"
      open={defaultOpen}
    >
      <summary className="cursor-pointer list-none px-4 py-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">{title}</p>
            {subtitle ? (
              <p className="mt-1 text-xs uppercase tracking-[0.14em] text-[color:var(--muted-soft)]">
                {subtitle}
              </p>
            ) : null}
          </div>
          <span className="text-xs uppercase tracking-[0.14em] text-[color:var(--muted-soft)]">
            Toggle
          </span>
        </div>
      </summary>
      <div className="border-t border-[color:var(--line)] px-4 py-4">{children}</div>
    </details>
  );
}

function TimelineEventCard({ event }: { event: StreamEvent }) {
  const status = getString(event.data.status);
  const stage = getString(event.data.stage);
  const agentName = getString(event.data.agent_name);
  const errorMessage = getString(event.data.error);

  let body: ReactNode = <StructuredValue value={event.data} />;

  if (event.event === "queued" || event.event === "pipeline_started") {
    body = (
      <div className="flex flex-wrap gap-2">
        {status ? <Badge>{titleCase(status)}</Badge> : null}
        {getString(event.data.application_id) ? (
          <Badge variant="default">Application queued</Badge>
        ) : null}
      </div>
    );
  } else if (event.event === "stage") {
    body = (
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl border border-[color:var(--line)] bg-[rgba(247,243,236,0.68)] p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
            Stage
          </p>
          <p className="mt-2 text-sm font-semibold">{stage ? titleCase(stage) : "Unknown"}</p>
        </div>
        <div className="rounded-2xl border border-[color:var(--line)] bg-[rgba(247,243,236,0.68)] p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
            Agent
          </p>
          <p className="mt-2 text-sm font-semibold">
            {agentName ? titleCase(agentName) : "Pipeline"}
          </p>
        </div>
        {status ? (
          <div className="sm:col-span-2">
            <Badge variant={status === "completed" ? "success" : status === "failed" ? "danger" : "default"}>
              {titleCase(status)}
            </Badge>
          </div>
        ) : null}
      </div>
    );
  } else if (event.event === "complete") {
    body = (
      <div className="flex flex-wrap gap-2">
        <Badge variant="success">Pipeline completed</Badge>
        {status ? <Badge>{titleCase(status)}</Badge> : null}
      </div>
    );
  } else if (event.event === "failed") {
    body = (
      <div className="grid gap-3">
        <Badge variant="danger">Pipeline failed</Badge>
        {errorMessage ? (
          <p className="text-sm leading-7 text-[color:var(--foreground)]">{errorMessage}</p>
        ) : (
          <StructuredValue value={event.data} />
        )}
      </div>
    );
  }

  return (
    <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
      <div className="flex items-center justify-between gap-3">
        <Badge>{titleCase(event.event)}</Badge>
        <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
          {formatDate(event.timestamp)}
        </p>
      </div>
      <div className="mt-3">{body}</div>
    </div>
  );
}

function AgentOutputSections({
  agentName,
  output,
}: {
  agentName: string;
  output: Record<string, unknown>;
}) {
  const sections: ReactNode[] = [];
  const similarJobs = getRecordArray(output.similar_jobs);
  const questionProvenance = getRecordArray(output.question_provenance);
  const calendarEvent = getRecord(output.calendar_event);
  const emailDelivery = getRecord(output.email_delivery);
  const proposedSlots = Array.isArray(output.proposed_slots) ? output.proposed_slots : [];
  const hiddenKeys = new Set([
    "similar_jobs",
    "question_provenance",
    "calendar_event",
    "email_delivery",
    "proposed_slots",
  ]);

  const summaryEntries = Object.entries(output).filter(([key]) => !hiddenKeys.has(key));

  if (summaryEntries.length > 0) {
    sections.push(
      <div key={`${agentName}-summary`} className="grid gap-3">
        {summaryEntries.map(([key, value]) => (
          <div
            key={key}
            className="rounded-2xl border border-[color:var(--line)] bg-[rgba(247,243,236,0.68)] p-3"
          >
            <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
              {formatStructuredKey(key)}
            </p>
            <div className="mt-2">
              <StructuredValue value={value} />
            </div>
          </div>
        ))}
      </div>,
    );
  }

  if (similarJobs.length > 0) {
    sections.push(
      <CollapsibleSection
        key={`${agentName}-similar-jobs`}
        title="Similar jobs"
        subtitle={`${similarJobs.length} match${similarJobs.length === 1 ? "" : "es"}`}
      >
        <div className="grid gap-3">
          {similarJobs.map((job, index) => (
            <div
              key={`${getString(job.job_id) ?? index}`}
              className="rounded-2xl border border-[color:var(--line)] bg-white/75 p-3"
            >
              <p className="font-semibold">{getString(job.title) ?? "Untitled role"}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {getString(job.job_id) ? <Badge variant="default">{getString(job.job_id)}</Badge> : null}
                {getNumber(job.similarity_score) !== null ? (
                  <Badge variant="success">{getNumber(job.similarity_score)?.toFixed(2)}</Badge>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </CollapsibleSection>,
    );
  }

  if (questionProvenance.length > 0) {
    sections.push(
      <CollapsibleSection
        key={`${agentName}-question-provenance`}
        title="Question provenance"
        subtitle={`${questionProvenance.length} generated prompt trail${questionProvenance.length === 1 ? "" : "s"}`}
      >
        <div className="grid gap-3">
          {questionProvenance.map((item, index) => (
            <div
              key={`${getString(item.question) ?? index}`}
              className="rounded-2xl border border-[color:var(--line)] bg-white/75 p-3"
            >
              <p className="text-sm font-semibold">{getString(item.question) ?? "Generated question"}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {getString(item.derived_from) ? (
                  <Badge variant="default">{titleCase(getString(item.derived_from) ?? "")}</Badge>
                ) : null}
                {getString(item.source_value) ? (
                  <Badge variant="default">{getString(item.source_value)}</Badge>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </CollapsibleSection>,
    );
  }

  if (calendarEvent || emailDelivery || proposedSlots.length > 0) {
    sections.push(
      <CollapsibleSection key={`${agentName}-delivery`} title="Delivery metadata" subtitle="Provider payloads">
        <div className="grid gap-3">
          {calendarEvent ? (
            <div className="rounded-2xl border border-[color:var(--line)] bg-white/75 p-3">
              <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
                Calendar event
              </p>
              <div className="mt-2">
                <StructuredValue value={calendarEvent} />
              </div>
            </div>
          ) : null}
          {emailDelivery ? (
            <div className="rounded-2xl border border-[color:var(--line)] bg-white/75 p-3">
              <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
                Email delivery
              </p>
              <div className="mt-2">
                <StructuredValue value={emailDelivery} />
              </div>
            </div>
          ) : null}
          {proposedSlots.length > 0 ? (
            <div className="rounded-2xl border border-[color:var(--line)] bg-white/75 p-3">
              <p className="text-[11px] uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
                Proposed slots
              </p>
              <div className="mt-2">
                <StructuredValue value={proposedSlots} />
              </div>
            </div>
          ) : null}
        </div>
      </CollapsibleSection>,
    );
  }

  return <div className="grid gap-3">{sections}</div>;
}

export default function ApplicationDetailPage() {
  const params = useParams<{ applicationId: string }>();
  const applicationId =
    typeof params.applicationId === "string"
      ? params.applicationId
      : params.applicationId?.[0];
  const { token } = useSession();
  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [similarJobs, setSimilarJobs] = useState<SimilarJobResult[]>([]);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLoadingPane, setShowLoadingPane] = useState(false);
  const [streamStatus, setStreamStatus] = useState<
    "connecting" | "live" | "reconnecting" | "complete" | "failed"
  >("connecting");
  const terminalStreamEvent = useRef(false);

  useEffect(() => {
    const currentId = applicationId;
    if (!token || !currentId) {
      return;
    }
    const resolvedId: string = currentId;

    let cancelled = false;
    let loadingTimer: number | undefined;
    async function load() {
      setLoading(true);
      setShowLoadingPane(false);
      setError(null);
      loadingTimer = window.setTimeout(() => {
        if (!cancelled) {
          setShowLoadingPane(true);
        }
      }, 250);
      try {
        const [applicationResponse, similarJobsResponse] = await Promise.all([
          getApplication(token, resolvedId),
          getSimilarJobsForApplication(token, resolvedId),
        ]);
        if (!cancelled) {
          setApplication(applicationResponse);
          setSimilarJobs(similarJobsResponse);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            getApiErrorMessage(loadError, "Unable to load application", {
              401: "Your session expired. Please log in again.",
              404: "That application could not be found.",
            }),
          );
        }
      } finally {
        if (!cancelled) {
          if (loadingTimer) {
            window.clearTimeout(loadingTimer);
          }
          setShowLoadingPane(false);
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [applicationId, token]);

  useEffect(() => {
    const currentId = applicationId;
    if (!currentId) {
      return;
    }
    const resolvedId: string = currentId;

    const source = new EventSource(`/api/applications/${resolvedId}/status`);
    const eventNames = ["queued", "pipeline_started", "stage", "complete", "failed"];

    const handler = (incoming: Event) => {
      const message = incoming as MessageEvent<string>;
      try {
        const payload = JSON.parse(message.data) as StreamEvent;
        setEvents((current) => {
          if (
            current.some(
              (item) =>
                item.event === payload.event &&
                item.timestamp === payload.timestamp &&
                JSON.stringify(item.data) === JSON.stringify(payload.data),
            )
          ) {
            return current;
          }
          return [...current, payload];
        });
        if (payload.event === "complete" || payload.event === "failed") {
          terminalStreamEvent.current = true;
          setStreamStatus(payload.event);
          source.close();
        }
      } catch {
        // Ignore malformed events and keep the stream alive.
      }
    };

    source.onopen = () => {
      if (!terminalStreamEvent.current) {
        setStreamStatus("live");
      }
    };
    eventNames.forEach((name) => source.addEventListener(name, handler));
    source.onerror = () => {
      if (terminalStreamEvent.current) {
        return;
      }
      setStreamStatus("reconnecting");
    };

    return () => {
      terminalStreamEvent.current = false;
      eventNames.forEach((name) => source.removeEventListener(name, handler));
      source.close();
    };
  }, [applicationId]);

  if (loading && !application && showLoadingPane) {
    return (
      <Card>
        <CardTitle className="text-2xl">Loading application...</CardTitle>
        <CardDescription>
          {error ?? "Fetching screening results, similar jobs, and the live pipeline feed."}
        </CardDescription>
      </Card>
    );
  }

  if (loading && !application) {
    return <div className="min-h-[40vh]" aria-hidden="true" />;
  }

  if (!application) {
    return (
      <Card>
        <CardTitle className="text-2xl">Application unavailable</CardTitle>
        <CardDescription>{error ?? "This application could not be loaded."}</CardDescription>
      </Card>
    );
  }

  const screenerOutput = application.agent_runs.find((run) => run.agent_name === "cv_screener")?.output;
  const schedulerOutput = application.agent_runs.find((run) => run.agent_name === "scheduler")?.output;
  const offerWriterOutput = application.agent_runs.find((run) => run.agent_name === "offer_writer")?.output;
  const schedulerCalendarEvent =
    schedulerOutput?.calendar_event && typeof schedulerOutput.calendar_event === "object"
      ? (schedulerOutput.calendar_event as Record<string, unknown>)
      : null;
  const schedulerEmailDelivery =
    schedulerOutput?.email_delivery && typeof schedulerOutput.email_delivery === "object"
      ? (schedulerOutput.email_delivery as Record<string, unknown>)
      : null;
  const offerEmailDelivery =
    offerWriterOutput?.email_delivery && typeof offerWriterOutput.email_delivery === "object"
      ? (offerWriterOutput.email_delivery as Record<string, unknown>)
      : null;
  const assessmentQuestions = Array.isArray(application.assessment_result?.questions)
    ? (application.assessment_result.questions as string[])
    : [];
  const questionProvenance = Array.isArray(application.assessment_result?.question_provenance)
    ? (application.assessment_result.question_provenance as Array<Record<string, unknown>>)
    : [];

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div className="space-y-3">
          <p className="eyebrow">Application Detail</p>
          <h1 className="section-title">
            {application.candidate?.name ?? "Candidate"} / {application.job?.title ?? "Role"}
          </h1>
          <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
            Follow the live SSE timeline, inspect agent reasoning, and review the interview and
            offer delivery metadata tied to this application.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge>{titleCase(application.status)}</Badge>
          <Badge>{application.score?.toFixed(2) ?? "Pending score"}</Badge>
          <Badge>{formatDate(application.updated_at)}</Badge>
        </div>
      </section>

      {error ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <CardTitle className="text-xl">Application issue</CardTitle>
          <CardDescription>{error}</CardDescription>
        </Card>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <p className="eyebrow">Screening</p>
          <CardTitle className="mt-2 text-3xl">Fit summary and signals</CardTitle>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
              <p className="text-sm font-semibold text-[color:var(--muted)]">Summary</p>
              <p className="mt-3 text-sm leading-7">
                {application.screening_notes ?? "Screening summary will appear after the screener finishes."}
              </p>
            </div>
            <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
              <p className="text-sm font-semibold text-[color:var(--muted)]">Strengths</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(screenerOutput?.strengths as string[] | undefined)?.map((item) => (
                  <Badge key={item} variant="success">
                    {item}
                  </Badge>
                )) ?? <span className="text-sm text-[color:var(--muted)]">Pending</span>}
              </div>
            </div>
            <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
              <p className="text-sm font-semibold text-[color:var(--muted)]">Risks</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(screenerOutput?.risks as string[] | undefined)?.map((item) => (
                  <Badge key={item} variant="warning">
                    {item}
                  </Badge>
                )) ?? <span className="text-sm text-[color:var(--muted)]">Pending</span>}
              </div>
            </div>
            <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
              <p className="text-sm font-semibold text-[color:var(--muted)]">Evidence</p>
              <ul className="mt-3 space-y-2 text-sm text-[color:var(--foreground)]">
                {(screenerOutput?.evidence as string[] | undefined)?.map((item) => (
                  <li key={item}>{item}</li>
                )) ?? <li className="text-[color:var(--muted)]">Pending</li>}
              </ul>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Live SSE Feed</p>
              <CardTitle className="mt-2 text-3xl">Pipeline activity</CardTitle>
            </div>
            <div className="flex items-center gap-2">
                <Badge
                  variant={
                  streamStatus === "live" || streamStatus === "complete"
                    ? "success"
                    : streamStatus === "reconnecting"
                      ? "warning"
                      : "default"
                }
              >
                {streamStatus === "live"
                  ? "Live"
                  : streamStatus === "complete"
                    ? "Complete"
                  : streamStatus === "reconnecting"
                    ? "Reconnecting"
                    : "Connecting"}
              </Badge>
              <div className="rounded-2xl bg-white/80 p-3 text-[color:var(--accent)]">
                <Activity className="h-5 w-5" />
              </div>
            </div>
          </div>
          <div className="mt-6 max-h-[72vh] grid gap-3 overflow-y-auto pr-2">
            {events.length === 0 ? (
              <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
                <p className="text-sm text-[color:var(--muted)]">
                  {streamStatus === "failed"
                    ? "The pipeline reported a failure. Open the failed stage below for details."
                    : streamStatus === "reconnecting"
                    ? "The live feed hit a temporary interruption. EventSource is retrying automatically."
                    : "Waiting for stream events. This endpoint replays history, so refreshing the page is safe even after the pipeline completes."}
                </p>
              </div>
            ) : (
              events.map((event) => <TimelineEventCard key={`${event.event}-${event.timestamp}`} event={event} />)
            )}
          </div>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card>
          <p className="eyebrow">Assessment</p>
          <CardTitle className="mt-2 text-3xl">Interview question set</CardTitle>
          <div className="mt-6 space-y-4">
            {assessmentQuestions.map((question, index) => (
              <div
                key={question}
                className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4"
              >
                <p className="font-semibold">
                  Q{index + 1}. {question}
                </p>
                <p className="mt-2 text-sm text-[color:var(--muted)]">
                  Provenance:{" "}
                  {(questionProvenance[index]?.derived_from as string | undefined) ?? "Pending"}
                  {" / "}
                  {(questionProvenance[index]?.source_value as string | undefined) ?? "Pending"}
                </p>
              </div>
            ))}
            {assessmentQuestions.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                Assessment questions will appear once the assessor stage completes.
              </p>
            ) : null}
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Scheduling + Offer</p>
          <CardTitle className="mt-2 text-3xl">Delivered artifacts</CardTitle>
          <div className="mt-6 grid gap-4">
            <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--muted)]">
                <TimerReset className="h-4 w-4" />
                Scheduled interview
              </div>
              <p className="mt-3 text-base font-semibold">{formatDate(application.scheduled_at)}</p>
              {typeof schedulerCalendarEvent?.html_link === "string" ? (
                <Link
                  className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[color:var(--accent-strong)]"
                  href={schedulerCalendarEvent.html_link}
                  target="_blank"
                >
                  Open calendar event
                  <ExternalLink className="h-4 w-4" />
                </Link>
              ) : null}
            </div>

            <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--muted)]">
                <Mail className="h-4 w-4" />
                Offer email
              </div>
              <p className="mt-3 text-sm leading-7">
                {application.offer_text ?? "Offer note pending."}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {typeof schedulerEmailDelivery?.mode === "string" ? (
                  <Badge>{titleCase(schedulerEmailDelivery.mode)} interview delivery</Badge>
                ) : null}
                {typeof offerEmailDelivery?.mode === "string" ? (
                  <Badge>{titleCase(offerEmailDelivery.mode)} offer delivery</Badge>
                ) : null}
              </div>
            </div>
          </div>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <p className="eyebrow">Similar jobs</p>
          <CardTitle className="mt-2 text-3xl">Nearby role matches</CardTitle>
          <div className="mt-6 grid gap-3">
            {similarJobs.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">No similar jobs returned for this application.</p>
            ) : (
              similarJobs.map((match) => (
                <Link
                  key={match.job.id}
                  href={`/jobs/${match.job.id}`}
                  className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4 transition hover:border-[color:var(--accent)]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">{match.job.title}</p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        {titleCase(match.job.seniority)} / {titleCase(match.job.status)}
                      </p>
                    </div>
                    <Badge>{match.similarity_score.toFixed(2)}</Badge>
                  </div>
                </Link>
              ))
            )}
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Agent runs</p>
          <CardTitle className="mt-2 text-3xl">Execution log</CardTitle>
          <div className="mt-6 max-h-[72vh] grid gap-3 overflow-y-auto pr-2">
            {application.agent_runs.map((run) => (
              <div
                key={run.id}
                className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold">{titleCase(run.agent_name)}</p>
                    <p className="mt-1 text-sm text-[color:var(--muted)]">
                      {titleCase(run.status)} / {run.duration_ms ?? 0} ms / {run.tokens_used ?? 0} tokens
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {run.used_fallback ? <Badge variant="warning">Fallback used</Badge> : null}
                    <Badge>{titleCase(run.status)}</Badge>
                  </div>
                </div>
                {run.used_fallback ? (
                  <p className="mt-3 rounded-2xl border border-[color:var(--line)] bg-[rgba(255,245,230,0.9)] px-4 py-3 text-sm text-[color:var(--foreground)]">
                    Live provider output was unavailable for this run, so the UI is showing a deterministic fallback result.
                    {run.error_message ? ` Provider error: ${run.error_message}` : ""}
                  </p>
                ) : null}
                {run.output ? (
                  <div className="mt-3">
                    <AgentOutputSections agentName={run.agent_name} output={run.output} />
                  </div>
                ) : null}
                <p className="mt-3 text-xs uppercase tracking-[0.16em] text-[color:var(--muted-soft)]">
                  {formatTokenCount(run.tokens_used)}
                </p>
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}
