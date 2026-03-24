"use client";

import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, Radar, Users } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getApiErrorMessage } from "@/lib/api";
import { useDashboardActivity, useDashboardStats } from "@/hooks/use-dashboard";
import { useJobs } from "@/hooks/use-jobs";
import { formatDate, titleCase } from "@/lib/utils";

function MetricSkeleton() {
  return (
    <Card>
      <Skeleton className="h-4 w-24" />
      <Skeleton className="mt-4 h-10 w-24" />
      <Skeleton className="mt-3 h-4 w-40" />
    </Card>
  );
}

export default function DashboardPage() {
  const { token } = useSession();
  const statsQuery = useDashboardStats(token);
  const activityQuery = useDashboardActivity(token, 10);
  const jobsQuery = useJobs(token, { limit: 5 });

  const error = statsQuery.error ?? activityQuery.error ?? jobsQuery.error;
  const isLoading = statsQuery.isLoading || activityQuery.isLoading || jobsQuery.isLoading;
  const stats = statsQuery.data;
  const activity = activityQuery.data ?? [];
  const jobs = jobsQuery.data?.items ?? [];

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
          <CardTitle className="text-xl">Unable to load dashboard</CardTitle>
          <CardDescription>
            {getApiErrorMessage(error, "Unable to load dashboard", {
              401: "Your session expired. Please log in again.",
            })}
          </CardDescription>
        </Card>
      ) : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {isLoading || !stats ? (
          Array.from({ length: 4 }, (_, index) => <MetricSkeleton key={index} />)
        ) : (
          [
            {
              label: "Open jobs",
              value: stats.active_jobs,
              description: `${stats.total_jobs} total jobs tracked`,
              icon: BriefcaseBusiness,
            },
            {
              label: "Candidate profiles",
              value: stats.total_candidates,
              description: "Profiles available for semantic matching",
              icon: Users,
            },
            {
              label: "Applications",
              value: stats.total_applications,
              description: "Tracked across the pipeline",
              icon: Radar,
            },
            {
              label: "Average score",
              value: stats.average_score.toFixed(2),
              description: `${stats.offered_count} offered or hired candidates`,
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
          })
        )}
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="eyebrow">Recent activity</p>
              <CardTitle className="mt-2 text-3xl">Latest pipeline movement</CardTitle>
            </div>
            <Badge>{activity.length} events</Badge>
          </div>
          <div className="mt-6 grid gap-3">
            {isLoading ? (
              Array.from({ length: 4 }, (_, index) => (
                <div
                  key={index}
                  className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4"
                >
                  <Skeleton className="h-5 w-40" />
                  <Skeleton className="mt-3 h-4 w-56" />
                </div>
              ))
            ) : activity.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No activity yet. Create a job, add a candidate, and submit the first profile to
                see the orchestration flow here.
              </p>
            ) : (
              activity.map((item) => {
                const href =
                  item.application_id
                    ? `/applications/${item.application_id}`
                    : item.job_id
                      ? `/jobs/${item.job_id}`
                      : "/dashboard";
                return (
                  <Link
                    key={`${item.type}-${item.id}`}
                    href={href}
                    className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4 transition hover:border-[color:var(--accent)]"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="text-base font-semibold">{item.title}</p>
                        <p className="mt-1 text-sm text-[color:var(--muted)]">{item.description}</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-[color:var(--muted-soft)]">
                          {formatDate(item.timestamp)}
                        </p>
                      </div>
                      {item.status ? <Badge>{titleCase(item.status)}</Badge> : null}
                    </div>
                  </Link>
                );
              })
            )}
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Jobs snapshot</p>
          <CardTitle className="mt-2 text-3xl">Roles needing attention</CardTitle>
          <div className="mt-6 grid gap-3">
            {isLoading ? (
              Array.from({ length: 4 }, (_, index) => (
                <div
                  key={index}
                  className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4"
                >
                  <Skeleton className="h-5 w-36" />
                  <Skeleton className="mt-3 h-4 w-28" />
                </div>
              ))
            ) : jobs.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No jobs have been posted yet. Create the first role to start the recruiter workflow.
              </p>
            ) : (
              jobs.map((job) => (
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
