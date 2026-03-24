"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useApplications } from "@/hooks/use-applications";
import { useCandidates } from "@/hooks/use-candidates";
import { useJob } from "@/hooks/use-jobs";
import {
  createApplication,
  getApiErrorMessage,
  updateJob,
} from "@/lib/api";
import type { Application, Candidate, JobStatus } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";

const columns: Array<{ status: Application["status"]; label: string }> = [
  { status: "submitted", label: "Submitted" },
  { status: "screening", label: "Screening" },
  { status: "assessed", label: "Assessed" },
  { status: "scheduled", label: "Scheduled" },
  { status: "offered", label: "Offered" },
  { status: "hired", label: "Hired" },
  { status: "rejected", label: "Rejected" },
];

const EMPTY_CANDIDATES: Candidate[] = [];

export default function JobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = typeof params.jobId === "string" ? params.jobId : params.jobId?.[0];
  const router = useRouter();
  const queryClient = useQueryClient();
  const { token } = useSession();
  const jobQuery = useJob(token, jobId);
  const applicationsQuery = useApplications(token, jobId ? { job_id: jobId, limit: 100 } : undefined);
  const candidatesQuery = useCandidates(token, { limit: 100 });
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [statusValue, setStatusValue] = useState<JobStatus>("draft");
  const [error, setError] = useState<string | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [submissionStatusMessage, setSubmissionStatusMessage] = useState<string | null>(null);

  const createApplicationMutation = useMutation({
    mutationFn: (input: { job_id: string; candidate_id: string }) => createApplication(token, input),
  });
  const updateJobMutation = useMutation({
    mutationFn: (status: JobStatus) => updateJob(token, jobId!, { status }),
  });

  const job = jobQuery.data;
  const applications = applicationsQuery.data?.items ?? [];
  const candidates = candidatesQuery.data?.items ?? EMPTY_CANDIDATES;
  const loading = jobQuery.isLoading || applicationsQuery.isLoading || candidatesQuery.isLoading;
  const queryError = jobQuery.error ?? applicationsQuery.error ?? candidatesQuery.error;

  useEffect(() => {
    if (job?.status) {
      setStatusValue(job.status);
    }
  }, [job?.status]);

  useEffect(() => {
    if (!selectedCandidateId && candidates[0]?.id) {
      setSelectedCandidateId(candidates[0].id);
    }
  }, [candidates, selectedCandidateId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Card>
          <Skeleton className="h-4 w-20" />
          <Skeleton className="mt-4 h-12 w-72" />
          <Skeleton className="mt-4 h-20 w-full" />
        </Card>
        <Card>
          <Skeleton className="h-8 w-40" />
          <div className="mt-6 grid gap-4 xl:grid-cols-4">
            {Array.from({ length: 4 }, (_, index) => (
              <Skeleton key={index} className="h-40 w-full" />
            ))}
          </div>
        </Card>
      </div>
    );
  }

  if (!job) {
    return (
      <Card>
        <CardTitle className="text-2xl">Role not found</CardTitle>
        <CardDescription>
          {getApiErrorMessage(queryError, "This job could not be loaded.", {
            401: "Your session expired. Please log in again.",
            404: "This role could not be found.",
          })}
        </CardDescription>
      </Card>
    );
  }

  async function handleCreateApplication(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCandidateId || !jobId) {
      return;
    }

    setSubmissionError(null);
    setSubmissionStatusMessage("Creating the application and opening the recruiter workflow...");
    const slowRequestTimer = window.setTimeout(() => {
      setSubmissionStatusMessage(
        "Still working. HireIQ is saving the application and preparing the live pipeline view.",
      );
    }, 1200);

    try {
      const application = await createApplicationMutation.mutateAsync({
        job_id: jobId,
        candidate_id: selectedCandidateId,
      });
      await queryClient.invalidateQueries({ queryKey: ["applications"] });
      setSubmissionStatusMessage("Application created. Opening the live application view...");
      router.push(`/applications/${application.id}`);
    } catch (submitError) {
      setSubmissionError(
        getApiErrorMessage(submitError, "Unable to submit application", {
          401: "Your session expired. Please log in again.",
          404: "The selected candidate or role could not be found.",
          409: "That candidate has already been submitted to this role.",
          422: "Please review the application inputs and try again.",
        }),
      );
    } finally {
      window.clearTimeout(slowRequestTimer);
      setSubmissionStatusMessage(null);
    }
  }

  async function handleStatusUpdate() {
    setError(null);
    try {
      await updateJobMutation.mutateAsync(statusValue);
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (updateError) {
      setError(
        getApiErrorMessage(updateError, "Unable to update role", {
          401: "Your session expired. Please log in again.",
          404: "This role no longer exists.",
          422: "Please review the selected status and try again.",
        }),
      );
    }
  }

  return (
    <div className="space-y-8">
      <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="eyebrow">Role detail</p>
              <CardTitle className="mt-2 text-4xl">{job.title}</CardTitle>
              <CardDescription className="mt-3 max-w-2xl">{job.description}</CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge>{titleCase(job.status)}</Badge>
              <Badge>{titleCase(job.seniority)}</Badge>
              <Badge>{job.has_embedding ? "Embedded" : "Pending embed"}</Badge>
            </div>
          </div>

          <div className="mt-6 rounded-[1.3rem] border border-[color:var(--line)] bg-white/75 p-5">
            <p className="text-sm font-semibold text-[color:var(--muted)]">Requirements</p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-7">{job.requirements}</p>
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Actions</p>
          <CardTitle className="mt-2 text-3xl">Keep the pipeline moving</CardTitle>

          <div className="mt-6 space-y-5">
            <div className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4">
              <p className="text-sm font-semibold">Update role status</p>
              <div className="mt-3 flex flex-wrap gap-3">
                <select
                  className="h-11 min-w-[180px] rounded-2xl border border-[color:var(--line)] bg-white/90 px-4 text-sm outline-none"
                  value={statusValue}
                  disabled={updateJobMutation.isPending}
                  onChange={(event) => setStatusValue(event.target.value as JobStatus)}
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                </select>
                <Button type="button" variant="secondary" onClick={handleStatusUpdate} disabled={updateJobMutation.isPending}>
                  {updateJobMutation.isPending ? "Saving..." : "Save status"}
                </Button>
              </div>
            </div>

            <form
              className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4"
              onSubmit={handleCreateApplication}
            >
              <p className="text-sm font-semibold">Submit candidate to this role</p>
              <p className="mt-1 text-sm text-[color:var(--muted)]">
                Pick an existing candidate profile and launch the agent pipeline immediately.
              </p>
              <select
                className="mt-4 h-11 w-full rounded-2xl border border-[color:var(--line)] bg-white/90 px-4 text-sm outline-none"
                value={selectedCandidateId}
                disabled={createApplicationMutation.isPending}
                onChange={(event) => setSelectedCandidateId(event.target.value)}
              >
                {candidates.map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.name} / {candidate.email}
                  </option>
                ))}
              </select>
              {submissionStatusMessage ? (
                <p className="mt-3 rounded-2xl border border-[color:var(--line)] bg-white/75 px-4 py-3 text-sm text-[color:var(--muted)]">
                  {submissionStatusMessage}
                </p>
              ) : null}
              {submissionError ? (
                <p className="mt-3 rounded-2xl bg-[rgba(180,35,24,0.1)] px-4 py-3 text-sm text-[color:var(--danger)]">
                  {submissionError}
                </p>
              ) : null}
              <div className="mt-4 flex flex-wrap gap-3">
                <Button
                  data-testid="application-create-submit"
                  disabled={!selectedCandidateId || createApplicationMutation.isPending}
                  type="submit"
                >
                  {createApplicationMutation.isPending ? "Creating application..." : "Create application"}
                </Button>
                <Link href="/candidates">
                  <Button type="button" variant="secondary" disabled={createApplicationMutation.isPending}>
                    Add new candidate
                  </Button>
                </Link>
              </div>
            </form>
          </div>
        </Card>
      </section>

      {error ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <CardTitle className="text-xl">Role board warning</CardTitle>
          <CardDescription>{error}</CardDescription>
        </Card>
      ) : null}

      <section className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="eyebrow">Kanban</p>
            <h2 className="text-3xl font-semibold">Application board</h2>
          </div>
          <p className="text-sm text-[color:var(--muted)]">
            {applications.length} applications tracked / created {formatDate(job.created_at)}
          </p>
        </div>

        <div className="grid gap-4 xl:grid-cols-4">
          {columns.map((column) => {
            const items = applications.filter((application) => application.status === column.status);
            return (
              <Card key={column.status} className="h-full">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold">{column.label}</p>
                    <p className="text-sm text-[color:var(--muted)]">{items.length} cards</p>
                  </div>
                  <Badge>{items.length}</Badge>
                </div>

                <div className="mt-4 grid gap-3">
                  {items.length === 0 ? (
                    <div className="rounded-[1.2rem] border border-dashed border-[color:var(--line)] px-4 py-5 text-sm text-[color:var(--muted)]">
                      Nothing in this stage yet.
                    </div>
                  ) : (
                    items.map((application) => (
                      <Link
                        key={application.id}
                        href={`/applications/${application.id}`}
                        className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4 transition hover:border-[color:var(--accent)]"
                      >
                        <p className="font-semibold">
                          {application.candidate?.name ?? "Candidate"}
                        </p>
                        <p className="mt-1 text-sm text-[color:var(--muted)]">
                          Score {application.score?.toFixed(2) ?? "Pending"}
                        </p>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-[color:var(--muted-soft)]">
                          {formatDate(application.updated_at)}
                        </p>
                      </Link>
                    ))
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
