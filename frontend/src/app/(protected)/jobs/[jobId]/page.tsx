"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { createApplication, listApplications, listCandidates, getJob, updateJob } from "@/lib/api";
import type { Application, Candidate, Job, JobStatus } from "@/lib/types";
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

export default function JobDetailPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = typeof params.jobId === "string" ? params.jobId : params.jobId?.[0];
  const router = useRouter();
  const { token } = useSession();
  const [job, setJob] = useState<Job | null>(null);
  const [applications, setApplications] = useState<Application[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [statusValue, setStatusValue] = useState<JobStatus>("draft");
  const [error, setError] = useState<string | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const currentJobId = jobId;
    if (!token || !currentJobId) {
      return;
    }
    const resolvedJobId: string = currentJobId;

    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [jobData, applicationData, candidateData] = await Promise.all([
          getJob(token, resolvedJobId),
          listApplications(token, { job_id: resolvedJobId, limit: 100 }),
          listCandidates(token, { limit: 100 }),
        ]);
        if (!cancelled) {
          setJob(jobData);
          setStatusValue(jobData.status);
          setApplications(applicationData.items);
          setCandidates(candidateData.items);
          setSelectedCandidateId(candidateData.items[0]?.id ?? "");
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load role board");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [jobId, token]);

  if (loading) {
    return <p className="text-sm text-[color:var(--muted)]">Loading role board...</p>;
  }

  if (!job) {
    return (
      <Card>
        <CardTitle className="text-2xl">Role not found</CardTitle>
        <CardDescription>{error ?? "This job could not be loaded."}</CardDescription>
      </Card>
    );
  }

  async function handleCreateApplication(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token || !selectedCandidateId || !job) {
      return;
    }
    const currentJobId = job.id;

    setSubmissionError(null);
    try {
      const application = await createApplication(token, {
        job_id: currentJobId,
        candidate_id: selectedCandidateId,
      });
      router.push(`/applications/${application.id}`);
    } catch (submitError) {
      setSubmissionError(
        submitError instanceof Error ? submitError.message : "Unable to submit application",
      );
    }
  }

  async function handleStatusUpdate() {
    if (!token || !job) {
      return;
    }
    const currentJobId = job.id;

    try {
      const updatedJob = await updateJob(token, currentJobId, { status: statusValue });
      setJob(updatedJob);
    } catch (updateError) {
      setError(updateError instanceof Error ? updateError.message : "Unable to update role");
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
                  onChange={(event) => setStatusValue(event.target.value as JobStatus)}
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                </select>
                <Button type="button" variant="secondary" onClick={handleStatusUpdate}>
                  Save status
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
                onChange={(event) => setSelectedCandidateId(event.target.value)}
              >
                {candidates.map((candidate) => (
                  <option key={candidate.id} value={candidate.id}>
                    {candidate.name} / {candidate.email}
                  </option>
                ))}
              </select>
              {submissionError ? (
                <p className="mt-3 rounded-2xl bg-[rgba(180,35,24,0.1)] px-4 py-3 text-sm text-[color:var(--danger)]">
                  {submissionError}
                </p>
              ) : null}
              <div className="mt-4 flex flex-wrap gap-3">
                <Button data-testid="application-create-submit" disabled={!selectedCandidateId} type="submit">
                  Create application
                </Button>
                <Link href="/candidates">
                  <Button type="button" variant="secondary">
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
