"use client";

import { useEffect, useState } from "react";
import { AlertCircle, Search } from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ListItemSkeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import {
  createCandidate,
  createCandidateFromPdf,
  getCandidate,
  getSimilarJobsForCandidate,
  listCandidates,
  searchCandidates,
} from "@/lib/api";
import type { Candidate, CandidateDetail, CandidateSearchResult, SimilarJobResult } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function CandidatesPage() {
  const { token } = useSession();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [searchResults, setSearchResults] = useState<CandidateSearchResult[] | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateDetail | null>(null);
  const [similarJobs, setSimilarJobs] = useState<SimilarJobResult[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"text" | "pdf">("text");
  const [formState, setFormState] = useState({
    name: "",
    email: "",
    linkedinUrl: "",
    resumeText: "",
  });
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;
    async function loadCandidates() {
      setLoading(true);
      setError(null);
      try {
        const response = await listCandidates(token, { limit: 100 });
        if (!cancelled) {
          setCandidates(response.items);
          setSelectedCandidateId((current) => current || response.items[0]?.id || "");
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load candidates");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadCandidates();
    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!token || !selectedCandidateId) {
      return;
    }

    let cancelled = false;
    async function loadCandidateDetails() {
      try {
        const [detailResponse, similarJobsResponse] = await Promise.all([
          getCandidate(token, selectedCandidateId),
          getSimilarJobsForCandidate(token, selectedCandidateId),
        ]);
        if (!cancelled) {
          setSelectedCandidate(detailResponse);
          setSimilarJobs(similarJobsResponse);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load candidate");
        }
      }
    }

    void loadCandidateDetails();
    return () => {
      cancelled = true;
    };
  }, [selectedCandidateId, token]);

  async function refreshCandidates() {
    if (!token) {
      return;
    }
    const response = await listCandidates(token, { limit: 100 });
    setCandidates(response.items);
    setSelectedCandidateId(response.items[0]?.id ?? "");
  }

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    if (!query.trim()) {
      setSearchResults(null);
      return;
    }

    try {
      const results = await searchCandidates(token, query.trim());
      setSearchResults(results);
    } catch (searchError) {
      setError(searchError instanceof Error ? searchError.message : "Unable to search candidates");
    }
  }

  async function handleCreateCandidate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setError(null);
    try {
      if (formMode === "pdf") {
        if (!resumeFile) {
          throw new Error("Please attach a PDF resume.");
        }
        await createCandidateFromPdf(token, {
          name: formState.name,
          email: formState.email,
          linkedin_url: formState.linkedinUrl || undefined,
          resume: resumeFile,
        });
      } else {
        await createCandidate(token, {
          name: formState.name,
          email: formState.email,
          linkedin_url: formState.linkedinUrl || undefined,
          resume_text: formState.resumeText,
        });
      }

      setFormState({ name: "", email: "", linkedinUrl: "", resumeText: "" });
      setResumeFile(null);
      setSearchResults(null);
      await refreshCandidates();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Unable to create candidate");
    }
  }

  const visibleCandidates = searchResults
    ? searchResults.map((result) => result.candidate)
    : candidates;

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

      {error ? (
        <Card className="border-[rgba(180,35,24,0.15)] bg-[rgba(255,241,240,0.8)]">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-[rgba(180,35,24,0.1)] p-2 text-[color:var(--danger)]">
              <AlertCircle className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-xl">Candidate workspace issue</CardTitle>
              <CardDescription>{error}</CardDescription>
            </div>
          </div>
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
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Button type="submit">
              <Search className="mr-2 h-4 w-4" />
              Search
            </Button>
            {searchResults ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setQuery("");
                  setSearchResults(null);
                }}
              >
                Reset
              </Button>
            ) : null}
          </form>

          <div className="mt-6 grid gap-3">
            {loading ? (
              <>
                <ListItemSkeleton />
                <ListItemSkeleton />
                <ListItemSkeleton />
              </>
            ) : visibleCandidates.length === 0 ? (
              <p className="text-sm text-[color:var(--muted)]">
                No candidates yet. Add the first profile to start semantic matching.
              </p>
            ) : (
              visibleCandidates.map((candidate) => {
                const result = searchResults?.find((item) => item.candidate.id === candidate.id);
                return (
                  <button
                    key={candidate.id}
                    className="rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4 text-left transition hover:border-[color:var(--accent)]"
                    onClick={() => {
                      setSelectedCandidateId(candidate.id);
                      setSearchResults(null);
                      setQuery("");
                    }}
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
                onClick={() => setFormMode("text")}
              >
                Resume text
              </Button>
              <Button
                className="flex-1"
                type="button"
                variant={formMode === "pdf" ? "primary" : "secondary"}
                onClick={() => setFormMode("pdf")}
              >
                PDF upload
              </Button>
            </div>
            <Input
              placeholder="Candidate name"
              required
              value={formState.name}
              onChange={(event) =>
                setFormState((current) => ({ ...current, name: event.target.value }))
              }
            />
            <Input
              placeholder="candidate@example.com"
              required
              type="email"
              value={formState.email}
              onChange={(event) =>
                setFormState((current) => ({ ...current, email: event.target.value }))
              }
            />
            <Input
              placeholder="LinkedIn URL (optional)"
              value={formState.linkedinUrl}
              onChange={(event) =>
                setFormState((current) => ({ ...current, linkedinUrl: event.target.value }))
              }
            />
            {formMode === "text" ? (
              <Textarea
                placeholder="Paste resume text here"
                value={formState.resumeText}
                onChange={(event) =>
                  setFormState((current) => ({ ...current, resumeText: event.target.value }))
                }
              />
            ) : (
              <Input
                accept=".pdf,application/pdf"
                type="file"
                onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
              />
            )}
            <Button data-testid="candidate-save" type="submit">
              Save candidate
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
          {selectedCandidateId && !selectedCandidate ? (
            <div className="mt-6 space-y-4">
              <ListItemSkeleton />
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
            {!selectedCandidateId ? (
              <p className="text-sm text-[color:var(--muted)]">
                Select a candidate from the list to see matching roles.
              </p>
            ) : similarJobs.length === 0 ? (
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
