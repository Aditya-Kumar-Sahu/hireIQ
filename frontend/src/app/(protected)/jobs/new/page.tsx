"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { AlertCircle } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createJob } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const { token } = useSession();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [seniority, setSeniority] = useState("mid");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const job = await createJob(token, {
        title,
        description,
        requirements,
        seniority,
      });
      router.replace(`/jobs/${job.id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create job");
    } finally {
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
            <Input value={title} onChange={(event) => setTitle(event.target.value)} required />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Description</span>
            <Textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              required
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Requirements</span>
            <Textarea
              value={requirements}
              onChange={(event) => setRequirements(event.target.value)}
              required
            />
          </label>
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Seniority</span>
            <select
              className="h-12 w-full rounded-2xl border border-[color:var(--line)] bg-white/80 px-4 text-sm outline-none transition focus:border-[color:var(--accent)] focus:ring-2 focus:ring-[rgba(193,92,47,0.16)]"
              value={seniority}
              onChange={(event) => setSeniority(event.target.value)}
            >
              <option value="junior">Junior</option>
              <option value="mid">Mid</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
            </select>
          </label>
          {error ? (
            <div className="flex items-center gap-3 rounded-2xl bg-[rgba(180,35,24,0.1)] px-4 py-3 text-sm text-[color:var(--danger)]">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button data-testid="job-create-submit" disabled={loading} type="submit">
              {loading ? "Creating..." : "Create job"}
            </Button>
            <Button type="button" variant="secondary" onClick={() => router.back()}>
              Cancel
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
