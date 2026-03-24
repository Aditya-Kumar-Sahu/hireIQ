"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Search } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useCandidate, useCandidates, useCandidateSearch, useSimilarJobsForCandidate } from "@/hooks/use-candidates";
import {
  createCandidate,
  createCandidateFromPdf,
  getApiErrorMessage,
} from "@/lib/api";
import type { Candidate } from "@/lib/types";
import { formatDate } from "@/lib/utils";

const EMPTY_CANDIDATES: Candidate[] = [];

export default function CandidatesPage() {
  const queryClient = useQueryClient();
  const { token } = useSession();
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [queryInput, setQueryInput] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"text" | "pdf">("text");
  const [createStatusMessage, setCreateStatusMessage] = useState<string | null>(null);
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    linkedinUrl: "",
    resumeText: "",
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const candidatesQuery = useCandidates(token, { limit: 100 });
  const searchQuery = useCandidateSearch(token, submittedQuery, Boolean(submittedQuery));
  const candidateQuery = useCandidate(token, selectedCandidateId || undefined);
  const similarJobsQuery = useSimilarJobsForCandidate(token, selectedCandidateId || undefined);
  const createCandidateMutation = useMutation({
    mutationFn: (input: { name: string; email: string; linkedin_url?: string; resume_text?: string }) =>
      createCandidate(token, input),
  });
  const createCandidateFromPdfMutation = useMutation({
    mutationFn: (input: { name: string; email: string; linkedin_url?: string; resume: File }) =>
      createCandidateFromPdf(token, input),
  });

  const candidates = candidatesQuery.data?.items ?? EMPTY_CANDIDATES;
  const searching = searchQuery.isFetching;
  const visibleCandidates: Candidate[] = submittedQuery
    ? (searchQuery.data?.map((result) => result.candidate) ?? [])
    : candidates;
  const selectedCandidate = candidateQuery.data ?? null;
  const similarJobs = similarJobsQuery.data ?? [];
  const loading = candidatesQuery.isLoading;
  const candidateDetailLoading = candidateQuery.isLoading || similarJobsQuery.isLoading;
  const activeError = error
    ?? (candidatesQuery.error || searchQuery.error || candidateQuery.error || similarJobsQuery.error
      ? getApiErrorMessage(
          candidatesQuery.error || searchQuery.error || candidateQuery.error || similarJobsQuery.error,
          "Unable to load candidates",
          {
            401: "Your session expired. Please log in again.",
            404: "That candidate could not be found.",
            422: "Search query is too short. Try a more specific prompt.",
          },
        )
      : null);

  useEffect(() => {
    if (!selectedCandidateId && candidates[0]?.id) {
      setSelectedCandidateId(candidates[0].id);
    }
  }, [candidates, selectedCandidateId]);

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmittedQuery(queryInput.trim());
  }

  async function handleCreateCandidate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setError(null);
    setCreateStatusMessage(
      formMode === "pdf"
        ? "Uploading the PDF, extracting the resume, and generating an embedding..."
        : "Saving the candidate and generating an embedding...",
    );
    const slowRequestTimer = window.setTimeout(() => {
      setCreateStatusMessage(
        formMode === "pdf"
          ? "Still working. HireIQ is parsing the PDF, storing the original resume, and preparing semantic search."
          : "Still working. HireIQ is generating the resume embedding for semantic search.",
      );
    }, 1200);

    try {
      const createdCandidate =
        formMode === "pdf"
          ? await createCandidateFromPdfMutation.mutateAsync({
              name: formState.name,
              email: formState.email,
              linkedin_url: formState.linkedinUrl || undefined,
              resume: resumeFile!,
            })
          : await createCandidateMutation.mutateAsync({
              name: formState.name,
              email: formState.email,
              linkedin_url: formState.linkedinUrl || undefined,
              resume_text: formState.resumeText,
            });

      setFormState({ name: "", email: "", linkedinUrl: "", resumeText: "" });
      setResumeFile(null);
      setSubmittedQuery("");
      setQueryInput("");
      setSelectedCandidateId(createdCandidate.id);
      await queryClient.invalidateQueries({ queryKey: ["candidates"] });
    } catch (createError) {
      setError(
        getApiErrorMessage(createError, "Unable to create candidate", {
          401: "Your session expired. Please log in again.",
          409: "A candidate with this email already exists.",
          422: "Please review the candidate fields and try again.",
          503:
            "Resume storage is currently unavailable. Please retry after checking the storage integration.",
        }),
      );
    } finally {
      window.clearTimeout(slowRequestTimer);
      setCreateStatusMessage(null);
    }
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="eyebrow">Candidates</p>
        <h1 className="section-title">Semantic search and intake</h1>
        <p className="max-w-2xl text-sm leading-7 text-[color:var(--muted)]">
          Add candidates by pasted resume text or PDF upload, search semantically across the talent
          pool, and inspect similar jobs before submitting them into a role.
        </p>
      </section>

      {activeError ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <CardTitle className="text-xl">Candidate workspace issue</CardTitle>
          <CardDescription>{activeError}</CardDescription>
        </Card>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="eyebrow">Search</p>
              <CardTitle className="mt-2 text-3xl">Find the right profile fast</CardTitle>
            </div>
            <Badge>{visibleCandidates.length} profiles</Badge>
          </div>

          <form className="mt-6 flex flex-col gap-3 md:flex-row" onSubmit={handleSearch}>
            <Input
              placeholder="Search semantically: fastapi backend engineer"
              value={queryInput}
              onChange={(event) => setQueryInput(event.target.value)}
              disabled={searching}
            />
            <Button type="submit" disabled={searching}>
              <Search className="mr-2 h-4 w-4" />
              {searching ? "Searching..." : "Search"}
            </Button>
            {submittedQuery ? (
              <Button
                type="button"
                variant="secondary"
                disabled={searching}
                onClick={() => {
                  setQueryInput("");
                  setSubmittedQuery("");
                }}
              >
                Reset
              </Button>
            ) : null}
          </form>

          <div className="mt-6 grid gap-3">
            {loading ? (
              Array.from({ length: 4 }, (_, index) => <Skeleton key={index} className="h-24 w-full" />)
            ) : visibleCandidates.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No candidates yet. Add the first profile to start semantic matching.
              </p>
            ) : (
              visibleCandidates.map((candidate) => {
                const result = searchQuery.data?.find((item) => item.candidate.id === candidate.id);
                return (
                  <button
                    key={candidate.id}
                    className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4 text-left transition hover:border-[color:var(--accent)]"
                    onClick={() => setSelectedCandidateId(candidate.id)}
                    type="button"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <p className="font-semibold">{candidate.name}</p>
                        <p className="mt-1 text-sm text-[color:var(--muted)]">{candidate.email}</p>
                        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-[color:var(--muted-soft)]">
                          Added {formatDate(candidate.created_at)}
                        </p>
                      </div>
                      {result ? <Badge>{result.similarity_score.toFixed(2)}</Badge> : null}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </Card>

        <Card>
          <p className="eyebrow">Intake</p>
          <CardTitle className="mt-2 text-3xl">Add a new candidate</CardTitle>
          <form className="mt-6 space-y-4" onSubmit={handleCreateCandidate}>
            <div className="flex gap-3">
              <Button
                className="flex-1"
                type="button"
                variant={formMode === "text" ? "primary" : "secondary"}
                disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
                onClick={() => setFormMode("text")}
              >
                Resume text
              </Button>
              <Button
                className="flex-1"
                type="button"
                variant={formMode === "pdf" ? "primary" : "secondary"}
                disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
                onClick={() => setFormMode("pdf")}
              >
                PDF upload
              </Button>
            </div>
            <Input
              placeholder="Candidate name"
              required
              disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
              value={formState.name}
              onChange={(event) =>
                setFormState((current) => ({ ...current, name: event.target.value }))
              }
            />
            <Input
              placeholder="candidate@example.com"
              required
              type="email"
              disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
              value={formState.email}
              onChange={(event) =>
                setFormState((current) => ({ ...current, email: event.target.value }))
              }
            />
            <Input
              placeholder="LinkedIn URL (optional)"
              disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
              value={formState.linkedinUrl}
              onChange={(event) =>
                setFormState((current) => ({ ...current, linkedinUrl: event.target.value }))
              }
            />
            {formMode === "text" ? (
              <Textarea
                placeholder="Paste resume text here"
                disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
                value={formState.resumeText}
                onChange={(event) =>
                  setFormState((current) => ({ ...current, resumeText: event.target.value }))
                }
              />
            ) : (
              <Input
                accept=".pdf,application/pdf"
                type="file"
                disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending}
                onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
              />
            )}
            {createStatusMessage ? (
              <p className="rounded-2xl border border-[color:var(--line)] bg-white/75 px-4 py-3 text-sm text-[color:var(--muted)]">
                {createStatusMessage}
              </p>
            ) : null}
            <Button data-testid="candidate-save" type="submit" disabled={createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending || (formMode === "pdf" && !resumeFile)}>
              {createCandidateMutation.isPending || createCandidateFromPdfMutation.isPending ? "Saving candidate..." : "Save candidate"}
            </Button>
          </form>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <p className="eyebrow">Selected profile</p>
          <CardTitle className="mt-2 text-3xl">
            {selectedCandidate?.name ?? "Choose a candidate"}
          </CardTitle>
          {candidateDetailLoading ? (
            <div className="mt-4 space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-8 w-24" />
            </div>
          ) : selectedCandidate ? (
            <div className="mt-6 space-y-4">
              <div className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4">
                <p className="text-sm text-[color:var(--muted)]">{selectedCandidate.email}</p>
                <p className="mt-2 text-sm leading-7">
                  {selectedCandidate.resume_text?.slice(0, 420)}
                  {selectedCandidate.resume_text && selectedCandidate.resume_text.length > 420
                    ? "..."
                    : ""}
                </p>
              </div>
              <Badge>{selectedCandidate.has_embedding ? "Embedded" : "Pending embed"}</Badge>
              {selectedCandidate.resume_file_url ? (
                <p className="text-sm text-[color:var(--muted)]">
                  Original resume stored in backend resume storage.
                </p>
              ) : null}
            </div>
          ) : (
            <p className="mt-4 text-sm text-[color:var(--muted)]">
              Select a candidate from the list to inspect their profile and similar jobs.
            </p>
          )}
        </Card>

        <Card>
          <p className="eyebrow">Similar jobs</p>
          <CardTitle className="mt-2 text-3xl">Best matching roles</CardTitle>
          <div className="mt-6 grid gap-3">
            {candidateDetailLoading ? (
              Array.from({ length: 3 }, (_, index) => <Skeleton key={index} className="h-24 w-full" />)
            ) : selectedCandidateId && similarJobs.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No similar jobs available yet. Create more roles or wait for embeddings to be ready.
              </p>
            ) : (
              similarJobs.map((match) => (
                <div
                  key={match.job.id}
                  className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold">{match.job.title}</p>
                      <p className="mt-1 text-sm text-[color:var(--muted)]">
                        {match.job.seniority} / {match.job.status}
                      </p>
                    </div>
                    <Badge>{match.similarity_score.toFixed(2)}</Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
