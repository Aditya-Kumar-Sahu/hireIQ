export type ApiEnvelope<T> = {
  success: boolean;
  data: T;
  error: string | null;
};

export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
};

export type User = {
  id: string;
  email: string;
  role: string;
  company_id: string;
  created_at: string;
};

export type JobStatus = "draft" | "active" | "closed";
export type JobSeniority = "junior" | "mid" | "senior" | "lead";

export type Job = {
  id: string;
  company_id: string;
  title: string;
  description: string;
  requirements: string;
  seniority: JobSeniority;
  status: JobStatus;
  has_embedding: boolean;
  created_at: string;
};

export type Candidate = {
  id: string;
  name: string;
  email: string;
  linkedin_url: string | null;
  resume_file_url: string | null;
  has_embedding: boolean;
  created_at: string;
};

export type CandidateDetail = Candidate & {
  resume_text: string | null;
};

export type CandidateSearchResult = {
  candidate: Candidate;
  similarity_score: number;
};

export type SimilarJobResult = {
  job: Job;
  similarity_score: number;
};

export type ApplicationStatus =
  | "submitted"
  | "screening"
  | "assessed"
  | "scheduled"
  | "offered"
  | "hired"
  | "rejected";

export type ApplicationJobSummary = {
  id: string;
  title: string;
  status: JobStatus;
  seniority: JobSeniority;
};

export type ApplicationCandidateSummary = {
  id: string;
  name: string;
  email: string;
  linkedin_url: string | null;
};

export type AgentRun = {
  id: string;
  agent_name: string;
  status: string;
  input: string | null;
  output: Record<string, unknown> | null;
  error_message: string | null;
  tokens_used: number | null;
  duration_ms: number | null;
  created_at: string;
};

export type Application = {
  id: string;
  job_id: string;
  candidate_id: string;
  status: ApplicationStatus;
  score: number | null;
  screening_notes: string | null;
  assessment_result: Record<string, unknown> | null;
  scheduled_at: string | null;
  offer_text: string | null;
  created_at: string;
  updated_at: string;
  job: ApplicationJobSummary | null;
  candidate: ApplicationCandidateSummary | null;
};

export type ApplicationDetail = Application & {
  agent_runs: AgentRun[];
};

export type AuthResponse = {
  user: User;
  access_token: string;
  token_type: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type IntegrationStatus = {
  openai_enabled: boolean;
  google_calendar_enabled: boolean;
  resend_enabled: boolean;
  sse_enabled: boolean;
};
