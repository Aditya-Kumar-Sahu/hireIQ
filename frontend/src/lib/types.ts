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

export type DashboardStats = {
  total_jobs: number;
  active_jobs: number;
  total_candidates: number;
  total_applications: number;
  average_score: number;
  offered_count: number;
  status_counts: Record<string, number>;
};

export type DashboardActivityItem = {
  id: string;
  type: "application" | "agent_run" | "job";
  title: string;
  description: string;
  status: string | null;
  timestamp: string;
  application_id: string | null;
  job_id: string | null;
  candidate_id: string | null;
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

export type AssessmentQuestion = {
  type: string;
  question: string;
  evaluation_criteria: string[];
  estimated_time_minutes: number;
};

export type AssessmentResult = {
  questions: AssessmentQuestion[];
  focus_areas: string[];
  question_provenance: Array<Record<string, unknown>>;
};

export type AgentRun = {
  id: string;
  agent_name: string;
  status: string;
  input: string | null;
  output: Record<string, unknown> | null;
  used_fallback: boolean;
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
  assessment_result: AssessmentResult | null;
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
  gemini_enabled: boolean;
  google_calendar_enabled: boolean;
  google_calendar_connected_email: string | null;
  resend_enabled: boolean;
  r2_enabled: boolean;
  resume_storage_enabled: boolean;
  ats_webhooks_enabled: boolean;
  ats_webhook_url: string;
  sse_enabled: boolean;
};

export type GoogleCalendarAuthorization = {
  authorization_url: string;
  state: string;
};

export type GoogleCalendarConnection = {
  provider: string;
  connected: boolean;
  connected_email: string | null;
  calendar_id: string | null;
};

export type StreamEvent = {
  id: string;
  event: string;
  timestamp: string;
  data: Record<string, unknown>;
};
