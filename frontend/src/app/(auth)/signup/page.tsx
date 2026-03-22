import Link from "next/link";

import { AuthForm } from "@/components/auth-form";

export default function SignupPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <div className="grid w-full max-w-6xl gap-10 lg:grid-cols-[1fr_420px] lg:items-center">
        <section className="space-y-6">
          <p className="eyebrow">New Workspace</p>
          <h1 className="max-w-3xl text-5xl font-semibold leading-[0.96] md:text-6xl">
            Launch a recruiter cockpit that already speaks jobs, resumes, and agent runs.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted)]">
            HireIQ is wired for semantic screening, sequential CrewAI workflows, interview
            scheduling, and offer delivery from the first sign-in.
          </p>
          <p className="text-sm text-[color:var(--muted)]">
            Already onboarded?{" "}
            <Link href="/login" className="font-semibold text-[color:var(--accent-strong)]">
              Log in
            </Link>
          </p>
        </section>

        <AuthForm mode="signup" />
      </div>
    </main>
  );
}
