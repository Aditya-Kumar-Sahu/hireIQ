import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="grid w-full max-w-6xl gap-10 lg:grid-cols-[1fr_420px] lg:items-center">
        <section className="space-y-6">
          <p className="eyebrow">Recruiter Console</p>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[0.96] md:text-6xl">
            Pick up the hiring pipeline exactly where your team left it.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted)]">
            Review agent runs, watch SSE status updates, move candidates through the funnel, and
            keep jobs, applicants, and communication drafts in one place.
          </p>
          <p className="text-sm text-[color:var(--muted)]">
            Need a workspace first?{" "}
            <Link href="/signup" className="font-semibold text-[color:var(--accent-strong)]">
              Create one
            </Link>
          </p>
        </section>

        <AuthForm mode="login" />
      </div>
    </main>
  );
}
