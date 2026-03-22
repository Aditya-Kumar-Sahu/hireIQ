"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, BriefcaseBusiness, Plus } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { listApplications, listJobs } from "@/lib/api";
import type { Application, Job } from "@/lib/types";
import { titleCase } from "@/lib/utils";

export default function JobsPage() {
  const { token } = useSession();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [jobsResponse, applicationsResponse] = await Promise.all([
          listJobs(token, { limit: 100 }),
          listApplications(token, { limit: 200 }),
        ]);
        if (!cancelled) {
          setJobs(jobsResponse.items);
          setApplications(applicationsResponse.items);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load jobs");
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

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="space-y-3">
          <p className="eyebrow">Jobs</p>
          <h1 className="section-title">Role management and kanban entry points</h1>
          <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
            Create roles, review open headcount, and jump into the application board for any job to
            move candidates through the pipeline.
          </p>
        </div>
        <Link href="/jobs/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Create job
          </Button>
        </Link>
      </section>

      {error ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <CardTitle className="text-xl">Unable to load jobs</CardTitle>
          <CardDescription>{error}</CardDescription>
        </Card>
      ) : null}

      {loading ? (
        <p className="text-sm text-[color:var(--muted)]">Loading jobs...</p>
      ) : jobs.length === 0 ? (
        <Card>
          <CardTitle className="text-2xl">No jobs yet</CardTitle>
          <CardDescription>
            Post the first role to unlock candidate matching, applications, and the agent pipeline.
          </CardDescription>
        </Card>
      ) : (
        <section className="grid gap-4 xl:grid-cols-2">
          {jobs.map((job) => {
            const relatedApplications = applications.filter(
              (application) => application.job_id === job.id,
            );
            return (
              <Link key={job.id} href={`/jobs/${job.id}`}>
                <Card className="h-full transition hover:border-[color:var(--accent)]">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="eyebrow">Role</p>
                      <CardTitle className="mt-2 text-3xl">{job.title}</CardTitle>
                      <CardDescription className="mt-3">
                        {job.description.slice(0, 160)}
                        {job.description.length > 160 ? "..." : ""}
                      </CardDescription>
                    </div>
                    <div className="rounded-2xl bg-white/75 p-3 text-[color:var(--accent)]">
                      <BriefcaseBusiness className="h-5 w-5" />
                    </div>
                  </div>

                  <div className="mt-6 flex flex-wrap gap-2">
                    <Badge>{titleCase(job.status)}</Badge>
                    <Badge>{titleCase(job.seniority)}</Badge>
                    <Badge>{job.has_embedding ? "Embedded" : "Pending embed"}</Badge>
                  </div>

                  <div className="mt-6 grid gap-3 rounded-[1.25rem] border border-[color:var(--line)] bg-white/70 p-4 sm:grid-cols-3">
                    <div>
                      <p className="text-sm text-[color:var(--muted)]">Applications</p>
                      <p className="mt-1 text-2xl font-semibold">{relatedApplications.length}</p>
                    </div>
                    <div>
                      <p className="text-sm text-[color:var(--muted)]">Offered</p>
                      <p className="mt-1 text-2xl font-semibold">
                        {
                          relatedApplications.filter((application) =>
                            ["offered", "hired"].includes(application.status),
                          ).length
                        }
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-[color:var(--muted)]">Live board</p>
                      <p className="mt-1 text-2xl font-semibold">Kanban</p>
                    </div>
                  </div>

                  <div className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[color:var(--accent-strong)]">
                    Open role board
                    <ArrowRight className="h-4 w-4" />
                  </div>
                </Card>
              </Link>
            );
          })}
        </section>
      )}
    </div>
  );
}
