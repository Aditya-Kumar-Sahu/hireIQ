"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertCircle, ArrowRight, BriefcaseBusiness, Radar, Users } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { ListItemSkeleton } from "@/components/ui/skeleton";
import { listApplications, listCandidates, listJobs } from "@/lib/api";
import type { Application, Candidate, Job } from "@/lib/types";
import { formatDate, titleCase } from "@/lib/utils";

export default function DashboardPage() {
  const { token } = useSession();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [jobData, candidateData, applicationData] = await Promise.all([
          listJobs(token, { limit: 50 }),
          listCandidates(token, { limit: 50 }),
          listApplications(token, { limit: 100 }),
        ]);
        if (!cancelled) {
          setJobs(jobData.items);
          setCandidates(candidateData.items);
          setApplications(applicationData.items);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load dashboard");
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
  }, [token]);

  const activeJobs = jobs.filter((job) => job.status !== "closed").length;
  const offeredCount = applications.filter((application) =>
    ["offered", "hired"].includes(application.status),
  ).length;
  const averageScore =
    applications.filter((application) => application.score !== null).reduce((total, application) => {
      return total + (application.score ?? 0);
    }, 0) / Math.max(applications.filter((application) => application.score !== null).length, 1);

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <p className="eyebrow">Dashboard</p>
          <h1 className="section-title">Recruiter command center</h1>
          <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
            Watch the pipeline health, review recent candidate movement, and jump straight into the
            jobs and applications that need attention.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href="/jobs/new">
            <Button>Create a job</Button>
          </Link>
          <Link href="/candidates">
            <Button variant="secondary">Add candidates</Button>
          </Link>
        </div>
      </section>

      {error ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-[rgba(180,35,24,0.1)] p-2 text-[color:var(--danger)]">
              <AlertCircle className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-xl">Unable to load dashboard</CardTitle>
              <CardDescription>{error}</CardDescription>
            </div>
          </div>
        </Card>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {[
          {
            label: "Open jobs",
            value: activeJobs,
            description: "Live roles still accepting applicants",
            icon: BriefcaseBusiness,
          },
          {
            label: "Candidate profiles",
            value: candidates.length,
            description: "Profiles available for semantic matching",
            icon: Users,
          },
          {
            label: "Applications",
            value: applications.length,
            description: "Tracked across the pipeline",
            icon: Radar,
          },
          {
            label: "Average score",
            value: Number.isFinite(averageScore) ? averageScore.toFixed(2) : "0.00",
            description: `${offeredCount} offered or hired candidates`,
            icon: ArrowRight,
          },
        ].map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.label}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="eyebrow">{metric.label}</p>
                  <p className="mt-3 text-4xl font-semibold">{metric.value}</p>
                  <p className="mt-2 text-sm text-[color:var(--muted)]">{metric.description}</p>
                </div>
                <div className="rounded-2xl bg-white/80 p-3 text-[color:var(--accent)]">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Recent applications</p>
              <CardTitle className="mt-2 text-3xl">Latest pipeline movement</CardTitle>
            </div>
            <Badge>{applications.length} tracked</Badge>
          </div>
          <div className="mt-6 grid gap-3">
            {loading ? (
              <>
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
              </>
            ) : applications.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No applications yet. Create a job, add a candidate, and submit the first profile to
                see the orchestration flow here.
              </p>
            ) : (
              applications.slice(0, 6).map((application) => (
                <Link
                  key={application.id}
                  href={`/applications/${application.id}`}
                  className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4 transition hover:border-[color:var(--accent)]"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-base font-semibold">
                        {application.candidate?.name ?? "Candidate"} / {application.job?.title ?? "Role"}
                      </p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        Updated {formatDate(application.updated_at)}
                      </p>
                    </div>
                    <Badge>{titleCase(application.status)}</Badge>
                  </div>
                </Link>
              ))
            )}
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Jobs snapshot</p>
          <CardTitle className="mt-2 text-3xl">Roles needing attention</CardTitle>
          <div className="mt-6 grid gap-3">
            {loading ? (
              <>
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
              </>
            ) : jobs.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No jobs have been posted yet. Create the first role to start the recruiter workflow.
              </p>
            ) : (
              jobs.slice(0, 5).map((job) => (
                <Link
                  key={job.id}
                  href={`/jobs/${job.id}`}
                  className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4 transition hover:border-[color:var(--accent)]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">{job.title}</p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        {titleCase(job.seniority)} / {titleCase(job.status)}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[color:var(--muted)]" />
                  </div>
                </Link>
              ))
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
