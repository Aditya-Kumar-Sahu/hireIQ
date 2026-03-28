import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ArrowRight, Sparkles, Workflow } from "lucide-react";

import { TOKEN_COOKIE_NAME } from "@/lib/auth";

export default async function Home() {
  const cookieStore = await cookies();
  const hasToken = cookieStore.has(TOKEN_COOKIE_NAME);
  if (hasToken) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-screen px-6 py-10 md:px-12">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl flex-col justify-between gap-12 rounded-[2rem] border border-white/60 bg-white/55 p-8 shadow-[0_30px_120px_rgba(92,52,19,0.14)] backdrop-blur-xl md:p-12">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="eyebrow">HireIQ</p>
            <p className="text-sm text-[color:var(--muted)]">
              Autonomous recruiting workflow, built for teams who move fast.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-full border border-[color:var(--line)] px-4 py-2 text-sm font-medium text-[color:var(--muted)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
            >
              Log in
            </Link>
            <Link
              href="/signup"
              className="rounded-full bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[color:var(--accent-strong)]"
            >
              Start recruiting
            </Link>
          </div>
        </header>

        <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="space-y-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/70 px-4 py-2 text-sm text-[color:var(--muted)]">
              <Sparkles className="h-4 w-4 text-[color:var(--accent)]" />
              Resume screening, interview planning, scheduling, and offer drafting in one loop
            </div>
            <div className="space-y-5">
              <h1 className="max-w-3xl text-5xl font-semibold leading-[0.95] md:text-7xl">
                Recruit with live AI workflows, not scattered tabs.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted)]">
                HireIQ connects structured hiring data, semantic screening, CrewAI agents, and
                real-time status feeds so recruiters can move from job post to offer without losing
                context.
              </p>
            </div>
            <div className="flex flex-col gap-4 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[color:var(--accent)] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[color:var(--accent-strong)]"
              >
                Open recruiter workspace
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center rounded-full border border-[color:var(--line)] px-6 py-3 text-sm font-semibold text-[color:var(--foreground)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]"
              >
                Jump back into pipeline
              </Link>
            </div>
          </div>

          <div className="glass-panel rounded-[1.75rem] p-6">
            <div className="grid gap-4">
              <div className="rounded-[1.35rem] bg-[linear-gradient(135deg,#fff8ee_0%,#fff1e4_45%,#f5ddcb_100%)] p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="eyebrow">Application Pipeline</p>
                    <h2 className="mt-2 text-2xl font-semibold">Backend Engineer / Casey Miller</h2>
                  </div>
                  <div className="rounded-full bg-white/70 px-3 py-1 text-sm font-semibold text-[color:var(--accent-strong)]">
                    Offered
                  </div>
                </div>
                <div className="mt-4 grid gap-3">
                  {[
                    "CV screener matched FastAPI, PostgreSQL, and Docker",
                    "Assessor generated focused questions with skill-gap provenance",
                    "Scheduler created an interview slot and outreach email",
                    "Offer writer drafted and delivered the offer note",
                  ].map((item) => (
                    <div
                      key={item}
                      className="flex items-center gap-3 rounded-2xl bg-white/75 px-4 py-3 text-sm text-[color:var(--foreground)]"
                    >
                      <Workflow className="h-4 w-4 text-[color:var(--accent)]" />
                      {item}
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-[1.35rem] border border-[color:var(--line)] bg-white/75 p-5">
                  <p className="eyebrow">Semantic Screening</p>
                  <p className="mt-3 text-3xl font-semibold">0.92</p>
                  <p className="mt-2 text-sm text-[color:var(--muted)]">
                    Similar jobs, matched skills, and past application context all surfaced together.
                  </p>
                </div>
                <div className="rounded-[1.35rem] border border-[color:var(--line)] bg-white/75 p-5">
                  <p className="eyebrow">Live Status</p>
                  <p className="mt-3 text-3xl font-semibold">SSE</p>
                  <p className="mt-2 text-sm text-[color:var(--muted)]">
                    Agent progress streams directly into the browser while the pipeline runs.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <footer className="flex flex-col gap-3 border-t border-[color:var(--line)] pt-6 text-sm text-[color:var(--muted)] md:flex-row md:items-center md:justify-between">
          <p>FastAPI + CrewAI + pgvector + Next.js recruiter workflow</p>
          <p>Built for interviews, demos, and a clean hiring handoff</p>
        </footer>
      </div>
    </main>
  );
}
