"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { getApiErrorMessage, login, signup } from "@/lib/api";
import { persistToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type AuthFormProps = {
  mode: "login" | "signup";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    setStatusMessage(mode === "signup" ? "Creating your workspace..." : "Signing you in...");
    const slowRequestTimer = window.setTimeout(() => {
      setStatusMessage(
        mode === "signup"
          ? "Still working. We’re creating your workspace and loading your recruiter profile."
          : "Still working. We’re verifying your account and loading your recruiter profile.",
      );
    }, 1200);

    try {
      const token =
        mode === "signup"
          ? (await signup({ email, password, company_name: companyName })).access_token
          : (await login({ email, password })).access_token;
      persistToken(token);
      const nextPath = new URLSearchParams(window.location.search).get("next");
      router.replace(nextPath ?? "/dashboard");
      router.refresh();
    } catch (submitError) {
      setError(
        getApiErrorMessage(submitError, "Unable to continue", {
          401: "Invalid email or password.",
          409: "An account with this email already exists. Try logging in instead.",
          422: "Please review the form fields and try again.",
          500: "The backend hit an error while processing your request. Please try again.",
        }),
      );
    } finally {
      window.clearTimeout(slowRequestTimer);
      setStatusMessage(null);
      setLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-md rounded-[2rem] p-8">
      <div className="space-y-2">
        <p className="eyebrow">{mode === "signup" ? "Recruiter Onboarding" : "Welcome Back"}</p>
        <CardTitle className="text-4xl">
          {mode === "signup" ? "Create your hiring workspace" : "Log into HireIQ"}
        </CardTitle>
        <CardDescription>
          {mode === "signup"
            ? "Spin up a recruiter workspace with the backend pipeline, screening, and agent orchestration already wired."
            : "Jump back into the recruiter dashboard and pick up where your pipeline left off."}
        </CardDescription>
      </div>

      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        {mode === "signup" ? (
          <label className="block space-y-2">
            <span className="text-sm font-medium text-[color:var(--muted)]">Company name</span>
            <Input
              placeholder="Acme Hiring"
              value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            required
            disabled={loading}
          />
        </label>
      ) : null}
        <label className="block space-y-2">
          <span className="text-sm font-medium text-[color:var(--muted)]">Work email</span>
          <Input
            type="email"
            placeholder="recruiter@company.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            disabled={loading}
          />
        </label>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-[color:var(--muted)]">Password</span>
          <Input
            type="password"
            placeholder="At least 8 characters"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            disabled={loading}
          />
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
        <Button className="w-full" data-testid="auth-submit" disabled={loading} type="submit">
          {loading
            ? "Working..."
            : mode === "signup"
              ? "Create recruiter workspace"
              : "Log in"}
        </Button>
      </form>

      <p className="mt-6 text-sm text-[color:var(--muted)]">
        {mode === "signup" ? "Already have an account?" : "Need a fresh workspace?"}{" "}
        <Link
          href={mode === "signup" ? "/login" : "/signup"}
          className="font-semibold text-[color:var(--accent-strong)]"
        >
          {mode === "signup" ? "Log in" : "Create one"}
        </Link>
      </p>
    </Card>
  );
}
