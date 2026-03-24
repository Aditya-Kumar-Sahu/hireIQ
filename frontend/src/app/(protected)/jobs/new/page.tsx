"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useSession } from "@/components/providers/session-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createJob, getApiErrorMessage } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const { token } = useSession();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [seniority, setSeniority] = useState("mid");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    setStatusMessage("Creating the role and generating its semantic embedding...");
    const slowRequestTimer = window.setTimeout(() => {
      setStatusMessage(
        "Still working. HireIQ is embedding the role so semantic matching is ready immediately after creation.",
      );
    }, 1200);
    try {
      const job = await createJob(token, {
        title,
        description,
        requirements,
        seniority,
      });
      router.replace(`/jobs/${job.id}`);
    } catch (submitError) {
      setError(
        getApiErrorMessage(submitError, "Unable to create job", {
          401: "Your session expired. Please log in again.",
          422: "Please review the job fields and try again.",
          500: "The backend hit an error while creating this role. Please try again.",
        }),
      );
    } finally {
      window.clearTimeout(slowRequestTimer);
      setStatusMessage(null);
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="eyebrow">Create Job</p>
        <h1 className="section-title">Open a new hiring lane</h1>
        <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
          Once the role is created, HireIQ will embed it automatically and you can start matching
          candidate resumes right away.
        </p>
      </section>

      <Card className="max-w-4xl">
        <form className="grid gap-5" onSubmit={handleSubmit}>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Role title</span>
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              required
              disabled={loading}
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Description</span>
            <Textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              required
              disabled={loading}
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Requirements</span>
            <Textarea
              value={requirements}
              onChange={(event) => setRequirements(event.target.value)}
              required
              disabled={loading}
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Seniority</span>
            <select
              className="h-12 rounded-2xl border border-[color:var(--line)] bg-white/80 px-4 text-sm outline-none"
              value={seniority}
              onChange={(event) => setSeniority(event.target.value)}
              disabled={loading}
            >
              <option value="junior">Junior</option>
              <option value="mid">Mid</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
            </select>
          </label>
          {statusMessage ? (
            <p className="rounded-2xl border border-[color:var(--line)] bg-white/75 px-4 py-3 text-sm text-[color:var(--muted)]">
              {statusMessage}
            </p>
          ) : null}
          {error ? (
            <p className="rounded-2xl bg-[rgba(180,35,24,0.1)] px-4 py-3 text-sm text-[color:var(--danger)]">
              {error}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button data-testid="job-create-submit" disabled={loading} type="submit">
              {loading ? "Creating..." : "Create job"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => router.back()} disabled={loading}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
