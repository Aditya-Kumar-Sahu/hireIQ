import type {
  Application,
  ApplicationDetail,
  AuthResponse,
  Candidate,
  CandidateDetail,
  CandidateSearchResult,
  IntegrationStatus,
  Job,
  PaginatedResponse,
  SimilarJobResult,
  TokenResponse,
  User,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type RequestOptions = {
  method?: string;
  token?: string | null;
  body?: unknown;
  formData?: FormData;
  searchParams?: Record<string, string | number | null | undefined>;
  signal?: AbortSignal;
};

function buildUrl(path: string, searchParams?: RequestOptions["searchParams"]) {
  const url = new URL(path, API_BASE);
  Object.entries(searchParams ?? {}).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

async function request<T>(path: string, options: RequestOptions = {}) {
  const headers = new Headers();
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  let body: BodyInit | undefined;
  if (options.formData) {
    body = options.formData;
  } else if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.body);
  }

  const response = await fetch(buildUrl(path, options.searchParams), {
    method: options.method ?? "GET",
    headers,
    body,
    cache: "no-store",
    signal: options.signal,
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok || !payload?.success) {
    throw new Error(payload?.error ?? "Request failed");
  }

  return payload.data as T;
}

export function signup(input: { email: string; password: string; company_name: string }) {
  return request<AuthResponse>("/api/v1/auth/signup", { method: "POST", body: input });
}

export function login(input: { email: string; password: string }) {
  return request<TokenResponse>("/api/v1/auth/login", { method: "POST", body: input });
}

export function getMe(token: string | null) {
  return request<User>("/api/v1/auth/me", { token });
}

export function getIntegrations(token: string | null) {
  return request<IntegrationStatus>("/api/v1/meta/integrations", { token });
}

export function listJobs(token: string | null, searchParams?: { status?: string; page?: number; limit?: number }) {
  return request<PaginatedResponse<Job>>("/api/v1/jobs", { token, searchParams });
}

export function getJob(token: string | null, jobId: string) {
  return request<Job>(`/api/v1/jobs/${jobId}`, { token });
}

export function createJob(
  token: string | null,
  input: { title: string; description: string; requirements: string; seniority: string },
) {
  return request<Job>("/api/v1/jobs", { token, method: "POST", body: input });
}

export function updateJob(
  token: string | null,
  jobId: string,
  input: Partial<{
    title: string;
    description: string;
    requirements: string;
    seniority: string;
    status: string;
  }>,
) {
  return request<Job>(`/api/v1/jobs/${jobId}`, { token, method: "PUT", body: input });
}

export function listCandidates(
  token: string | null,
  searchParams?: { search?: string; page?: number; limit?: number },
) {
  return request<PaginatedResponse<Candidate>>("/api/v1/candidates", { token, searchParams });
}

export function getCandidate(token: string | null, candidateId: string) {
  return request<CandidateDetail>(`/api/v1/candidates/${candidateId}`, { token });
}

export function createCandidate(
  token: string | null,
  input: { name: string; email: string; linkedin_url?: string; resume_text?: string },
) {
  return request<Candidate>("/api/v1/candidates", { token, method: "POST", body: input });
}

export function createCandidateFromPdf(
  token: string | null,
  input: { name: string; email: string; linkedin_url?: string; resume: File },
) {
  const formData = new FormData();
  formData.set("name", input.name);
  formData.set("email", input.email);
  if (input.linkedin_url) {
    formData.set("linkedin_url", input.linkedin_url);
  }
  formData.set("resume", input.resume);

  return request<Candidate>("/api/v1/candidates", {
    token,
    method: "POST",
    formData,
  });
}

export function searchCandidates(token: string | null, query: string) {
  return request<CandidateSearchResult[]>("/api/v1/candidates/search", {
    token,
    searchParams: { q: query },
  });
}

export function listApplications(
  token: string | null,
  searchParams?: { job_id?: string; status?: string; page?: number; limit?: number },
) {
  return request<PaginatedResponse<Application>>("/api/v1/applications", { token, searchParams });
}

export function createApplication(token: string | null, input: { job_id: string; candidate_id: string }) {
  return request<Application>("/api/v1/applications", { token, method: "POST", body: input });
}

export function getApplication(token: string | null, applicationId: string) {
  return request<ApplicationDetail>(`/api/v1/applications/${applicationId}`, { token });
}

export function updateApplicationStatus(token: string | null, applicationId: string, status: string) {
  return request<Application>(`/api/v1/applications/${applicationId}/status`, {
    token,
    method: "PATCH",
    body: { status },
  });
}

export function getSimilarJobsForCandidate(token: string | null, candidateId: string) {
  return request<SimilarJobResult[]>(`/api/v1/candidates/${candidateId}/similar-jobs`, { token });
}

export function getSimilarJobsForApplication(token: string | null, applicationId: string) {
  return request<SimilarJobResult[]>(`/api/v1/applications/${applicationId}/similar-jobs`, {
    token,
  });
}
