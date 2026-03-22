"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { login, signup } from "@/lib/api";
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

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

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
      setError(submitError instanceof Error ? submitError.message : "Unable to continue");
    } finally {
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
          />
        </label>
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
