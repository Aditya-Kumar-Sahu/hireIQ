# 🧠 HireIQ — AI-Powered Hiring Copilot

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![CrewAI](https://img.shields.io/badge/CrewAI-Agents-FF6B35)](https://crewai.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**An autonomous, multi-agent recruitment platform that screens resumes, generates assessments, schedules interviews, and drafts offer letters — all powered by AI agents working in concert.**

[Live Demo →](#) · [Architecture](#3-high-level-architecture) · [API Docs](#5-api-endpoints-spec) · [Agent System](#6-crewai-agent-definitions) · [Screenshots](#)


---

## Table of Contents

1.  [Project Overview](#1-project-overview)
2.  [Tech Stack](#2-tech-stack)
3.  [High-Level Architecture](#3-high-level-architecture)
4.  [Database Schema (ERD)](#4-database-schema-erd)
5.  [API Endpoints Spec](#5-api-endpoints-spec)
6.  [CrewAI Agent Definitions](#6-crewai-agent-definitions)
7.  [RAG Pipeline Design](#7-rag-pipeline-design)
8.  [Frontend Pages & Components](#8-frontend-pages--components)
9.  [Phased Execution Plan](#9-phased-execution-plan)
10. [Folder Structure](#10-folder-structure)
11. [Environment Variables](#11-environment-variables)
12. [Key Engineering Decisions](#12-key-engineering-decisions)
13. [Demo Script (For Interviews)](#13-demo-script-for-interviews)
14. [Stretch Goals (Post-MVP)](#14-stretch-goals-post-mvp)

---

## 1. Project Overview

**HireIQ** is a full-stack, production-grade recruitment platform that replaces tedious, manual hiring workflows with a team of autonomous AI agents. When a recruiter posts a job and a candidate submits a resume, four specialised CrewAI agents kick in sequentially: a **CV Screener** that semantically matches the resume to the job description using pgvector embeddings, a **Technical Assessor** that generates tailored interview questions, an **Interview Scheduler** that proposes time slots and drafts calendar invites, and an **Offer Writer** that produces personalised offer letters grounded in company culture. Each agent's reasoning, output, token usage, and latency are fully logged — making the system auditable, debuggable, and demonstrably intelligent.

### Who is it for?

| Persona            | How they use HireIQ                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------- |
| **Recruiters**      | Post jobs, review AI-screened applicants on a Kanban board, send automated interview invites and offers   |
| **Hiring Managers** | View dashboard metrics (time-to-hire, agent accuracy), review assessment questions before interviews      |
| **Candidates**      | Submit applications via a clean interface; receive personalised communication at every stage              |

### Why it's impressive from an AI/ML engineering perspective

- **Agentic architecture**: Not a single LLM call — a coordinated crew of agents with distinct roles, tools, and structured outputs
- **RAG pipeline**: Cosine-similarity search over pgvector embeddings for semantic resume-to-job matching — not keyword grep
- **Production-grade observability**: Every agent run is logged with input, output, tokens, and latency — ready for cost analysis and performance tuning
- **Real-time streaming**: Server-Sent Events (SSE) push agent progress to the browser as it happens
- **Full-stack deployment**: Docker Compose for local dev, Vercel + Railway for production — end-to-end

### Screenshots

> _Screenshots will be added after Phase 5 (Frontend) is complete._

---

## 2. Tech Stack

| Layer                | Technology                        | Why This Choice                                                                                        |
| -------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **Frontend**         | Next.js 14 (App Router)          | Server Components reduce client bundle; streaming UI for SSE agent progress; RSC for data fetching     |
| **Styling**          | TailwindCSS + shadcn/ui          | Consistent design system with accessible primitives; rapid iteration on a polished SaaS look            |
| **Backend**          | FastAPI (Python 3.11+)           | Async-native with `asyncpg`; Pydantic v2 for schema validation; first-class SSE and background tasks   |
| **Database**         | PostgreSQL 16 + pgvector         | Embeddings co-located with relational data — single DB, better joins, no extra infra vs Pinecone        |
| **Vector Search**    | pgvector (HNSW index)            | Sub-millisecond approximate nearest-neighbour search on embeddings; no external vector DB required      |
| **AI Orchestration** | CrewAI                           | Role-based agent design maps naturally to hiring personas; cleaner collaboration model than LangChain   |
| **LLM**             | Google Gemini                    | Structured reasoning for screening, assessment generation, and offer writing through CrewAI             |
| **Embeddings**       | Gemini `gemini-embedding-001`    | Flexible embedding dimensions with a 1536-dim deployment profile that fits the current pgvector schema  |
| **Job Queue**        | Redis (via `redis-py`)           | Async agent execution queue; prevents request timeouts on long-running LLM chains; embedding cache TTL  |
| **Auth**             | JWT (HS256)                      | Stateless token auth; simple, secure, no session store overhead                                         |
| **Email**            | Resend API                       | Developer-friendly transactional email; great deliverability, simple SDK                                |
| **Calendar**         | Google Calendar API (OAuth 2.0)  | Industry-standard calendar integration for interview scheduling                                         |
| **Storage**          | Cloudflare R2                    | S3-compatible; zero egress fees; stores uploaded resume PDFs                                             |
| **PDF Parsing**      | PyMuPDF (fitz)                   | Fast, reliable text extraction from PDF resumes; no external services                                   |
| **Containerisation** | Docker + Docker Compose          | Reproducible local dev environment; single `docker compose up` for all services                         |
| **Backend Deploy**   | Railway                          | Zero-config Docker deployment; managed PostgreSQL and Redis add-ons; excellent DX                       |
| **Frontend Deploy**  | Vercel                           | Native Next.js edge deployment; preview deployments on every PR                                         |
| **Testing**          | pytest + Playwright              | pytest for backend unit/integration tests; Playwright for frontend E2E                                  |

---

## 3. High-Level Architecture

```mermaid
flowchart TB
    subgraph Frontend["Next.js 14 (Vercel)"]
        UI["Recruiter Dashboard"]
        SSEClient["SSE Client"]
    end

    subgraph Backend["FastAPI (Railway)"]
        API["REST API"]
        SSEServer["SSE Endpoint"]
        Auth["JWT Auth Middleware"]
        BG["Background Task Runner"]
    end

    subgraph Agents["CrewAI Orchestrator"]
        A1["Agent 1: CV Screener"]
        A2["Agent 2: Technical Assessor"]
        A3["Agent 3: Interview Scheduler"]
        A4["Agent 4: Offer Writer"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL + pgvector")]
        RD[("Redis")]
        R2["Cloudflare R2"]
    end

    subgraph External["External Services"]
        Gemini["Google Gemini API"]
        GCal["Google Calendar"]
        Resend["Resend Email"]
    end

    UI -->|REST| API
    SSEClient <-->|SSE| SSEServer
    API --> Auth
    API --> BG
    BG --> Agents
    A1 --> Gemini
    A2 --> Gemini
    A3 --> GCal
    A3 --> Resend
    A4 --> Gemini
    Agents --> PG
    Agents --> RD
    API --> PG
    API --> RD
    API --> R2
```

### Request Flow: Application Submission

```
1. Recruiter uploads resume PDF → R2 storage
2. PyMuPDF extracts text ??? Gemini embeds resume ??? pgvector stores embedding
3. POST /api/v1/applications triggers background task
4. CrewAI Orchestrator runs agents sequentially:
   ????????? CV Screener  ??? cosine similarity + Gemini analysis ??? score, skills, recommendation
   ????????? Assessor     ??? Gemini generates role-specific questions ??? assessment
   ├── Scheduler    → Google Calendar API → proposed slots + email draft
   ????????? Offer Writer ??? Gemini + company context (RAG) ??? personalised offer letter
5. Each agent's output written to `agent_runs` table
6. SSE pushes real-time status to the browser (pending → running → complete)
7. Application status updated to reflect pipeline completion
```

---

## 4. Database Schema (ERD)

```mermaid
erDiagram
    COMPANIES ||--o{ JOBS : has
    COMPANIES ||--o{ USERS : employs
    JOBS ||--o{ APPLICATIONS : receives
    CANDIDATES ||--o{ APPLICATIONS : submits
    APPLICATIONS ||--o{ AGENT_RUNS : triggers

    COMPANIES {
        uuid id PK
        varchar name
        varchar industry
        text culture_notes
        timestamp created_at
    }

    JOBS {
        uuid id PK
        uuid company_id FK
        varchar title
        text description
        text requirements
        vector embedding "1536-dim"
        varchar status "draft | active | closed"
        varchar seniority "junior | mid | senior | lead"
        timestamp created_at
    }

    CANDIDATES {
        uuid id PK
        varchar name
        varchar email UK
        text resume_text
        vector resume_embedding "1536-dim"
        varchar linkedin_url
        varchar resume_file_url
        timestamp created_at
    }

    APPLICATIONS {
        uuid id PK
        uuid job_id FK
        uuid candidate_id FK
        varchar status "submitted | screening | assessed | scheduled | offered | hired | rejected"
        float score
        text screening_notes
        jsonb assessment_result
        timestamp scheduled_at
        text offer_text
        timestamp created_at
        timestamp updated_at
    }

    AGENT_RUNS {
        uuid id PK
        uuid application_id FK
        varchar agent_name "cv_screener | assessor | scheduler | offer_writer"
        text input
        jsonb output
        varchar status "pending | running | completed | failed"
        varchar error_message
        int tokens_used
        int duration_ms
        timestamp created_at
    }

    USERS {
        uuid id PK
        varchar email UK
        varchar hashed_password
        varchar role "recruiter | admin"
        uuid company_id FK
        timestamp created_at
    }
```

### Key Design Notes

- **UUIDs** as primary keys for all tables — URL-safe, non-sequential, globally unique.
- **`vector(1536)`** columns for job descriptions and resumes — indexed with HNSW for fast cosine similarity.
- **`jsonb`** for agent outputs — flexible schema for different agent response structures.
- **Application `status`** is a PostgreSQL enum tracking the full pipeline: `submitted → screening → assessed → scheduled → offered → hired | rejected`.
- **`agent_runs`** table provides full observability: input, output, tokens, latency, and error state per agent execution.

---

## 5. API Endpoints Spec

All endpoints return the standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### Auth

| Method | Path                     | Description                  | Auth    | Request Body                            | Response                |
| ------ | ------------------------ | ---------------------------- | ------- | --------------------------------------- | ----------------------- |
| POST   | `/api/v1/auth/signup`    | Register a new recruiter     | None    | `{ email, password, company_name }`     | `{ user, access_token }`|
| POST   | `/api/v1/auth/login`     | Login, get JWT               | None    | `{ email, password }`                   | `{ access_token }`      |
| GET    | `/api/v1/auth/me`        | Get current user profile     | JWT     | —                                       | `{ user }`              |

### Jobs

| Method | Path                     | Description                  | Auth    | Request Body                                          | Response                |
| ------ | ------------------------ | ---------------------------- | ------- | ----------------------------------------------------- | ----------------------- |
| POST   | `/api/v1/jobs`           | Create a new job listing     | JWT     | `{ title, description, requirements, seniority }`     | `{ job }`               |
| GET    | `/api/v1/jobs`           | List jobs (with filters)     | JWT     | Query: `?status=active&page=1&limit=20`               | `{ jobs[], total }`     |
| GET    | `/api/v1/jobs/{id}`      | Get job details              | JWT     | —                                                     | `{ job }`               |
| PUT    | `/api/v1/jobs/{id}`      | Update job listing           | JWT     | `{ title?, description?, requirements?, status? }`    | `{ job }`               |
| DELETE | `/api/v1/jobs/{id}`      | Soft-delete a job            | JWT     | —                                                     | `{ success: true }`     |

### Candidates

| Method | Path                          | Description                         | Auth    | Request Body                                    | Response                    |
| ------ | ----------------------------- | ----------------------------------- | ------- | ----------------------------------------------- | --------------------------- |
| POST   | `/api/v1/candidates`          | Add a candidate (+ resume upload)   | JWT     | Multipart: `name, email, linkedin_url, resume`  | `{ candidate }`             |
| GET    | `/api/v1/candidates`          | List candidates (with filters)      | JWT     | Query: `?search=react&page=1&limit=20`          | `{ candidates[], total }`   |
| GET    | `/api/v1/candidates/{id}`     | Get candidate profile               | JWT     | —                                               | `{ candidate }`             |
| GET    | `/api/v1/candidates/search`   | Semantic search by skills/desc      | JWT     | Query: `?q=senior react developer`              | `{ candidates[], scores }`  |

### Applications

| Method | Path                                    | Description                            | Auth    | Request Body                   | Response                       |
| ------ | --------------------------------------- | -------------------------------------- | ------- | ------------------------------ | ------------------------------ |
| POST   | `/api/v1/applications`                  | Submit application (triggers pipeline) | JWT     | `{ job_id, candidate_id }`     | `{ application }`              |
| GET    | `/api/v1/applications`                  | List applications (with filters)       | JWT     | Query: `?job_id=&status=`      | `{ applications[], total }`    |
| GET    | `/api/v1/applications/{id}`             | Full detail + agent outputs            | JWT     | —                              | `{ application, agent_runs }` |
| GET    | `/api/v1/applications/{id}/status`      | SSE stream for real-time progress      | JWT     | —                              | SSE stream                     |
| POST   | `/api/v1/applications/{id}/schedule`    | Trigger scheduling agent               | JWT     | `{ availability_slots[] }`     | `{ agent_run }`                |
| POST   | `/api/v1/applications/{id}/offer`       | Trigger offer writer agent             | JWT     | `{ compensation_details? }`    | `{ agent_run }`                |
| PATCH  | `/api/v1/applications/{id}/status`      | Manually update status                 | JWT     | `{ status }`                   | `{ application }`              |

### Dashboard

| Method | Path                            | Description                    | Auth    | Response                                                       |
| ------ | ------------------------------- | ------------------------------ | ------- | -------------------------------------------------------------- |
| GET    | `/api/v1/dashboard/stats`       | Aggregate metrics              | JWT     | `{ total_jobs, total_applications, avg_score, status_counts }` |
| GET    | `/api/v1/dashboard/activity`    | Recent activity feed           | JWT     | `{ activities[] }`                                             |

### Health

| Method | Path        | Description         | Auth | Response                            |
| ------ | ----------- | ------------------- | ---- | ----------------------------------- |
| GET    | `/health`   | Health check         | None | `{ status: "healthy", version }`   |

---

## 6. CrewAI Agent Definitions

### Agent 1 — CV Screener

| Attribute          | Value                                                                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Role**           | Senior Talent Acquisition Analyst                                                                                                               |
| **Goal**           | Evaluate how well a candidate's resume matches the job requirements, producing a quantified fit score with detailed skill gap analysis           |
| **Backstory**      | You have 15 years of experience in technical recruiting at FAANG companies. You know the difference between genuine expertise and keyword stuffing. You assess not just skill overlap, but career trajectory, project complexity, and cultural fit indicators. |
| **Tools**          | `pgvector_similarity_search` — cosine similarity between resume and job embeddings; `db_query` — fetch job requirements and candidate history   |
| **Expected Output**| ```json { "score": 0.87, "matched_skills": ["React", "TypeScript", "PostgreSQL"], "missing_skills": ["Kubernetes", "GraphQL"], "experience_years": 5, "recommendation": "proceed", "summary": "Strong frontend candidate with solid backend awareness. Missing cloud-native experience but demonstrates rapid learning through side projects." } ``` |

### Agent 2 — Technical Assessor

| Attribute          | Value                                                                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Role**           | Technical Interview Designer                                                                                                                    |
| **Goal**           | Generate a tailored, role-specific assessment with a balanced mix of technical and behavioural questions, calibrated to the job's seniority level |
| **Backstory**      | You are a principal engineer who has conducted 1,000+ technical interviews. You design questions that reveal depth of understanding, not memorisation. You adjust difficulty based on seniority — junior roles get fundamentals, senior roles get system design and architectural trade-offs. |
| **Tools**          | `db_query` — fetch job requirements, seniority level, and candidate's matched/missing skills from the screening results                          |
| **Expected Output**| ```json { "questions": [ { "type": "technical", "question": "Design a real-time notification system that scales to 10M users...", "evaluation_criteria": "Looks for: pub/sub patterns, WebSocket vs SSE trade-offs, database fan-out strategies" }, { "type": "behavioural", "question": "Describe a time you had to make a significant architectural decision under time pressure...", "evaluation_criteria": "Looks for: structured thinking, stakeholder communication, trade-off awareness" } ], "estimated_time_minutes": 45 } ``` |

### Agent 3 — Interview Scheduler

| Attribute          | Value                                                                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Role**           | Executive Recruitment Coordinator                                                                                                               |
| **Goal**           | Find mutually convenient interview times, create calendar events, and draft a professional, personalised interview invitation email               |
| **Backstory**      | You are an elite recruitment coordinator at a top-tier company. You understand timezone differences, interviewer availability, and the importance of a warm, professional candidate experience. Every email you write makes the candidate feel valued. |
| **Tools**          | `google_calendar_check` — query available slots; `google_calendar_create` — create interview event; `email_draft` — compose personalised email  |
| **Expected Output**| ```json { "proposed_slots": [ "2025-02-15T10:00:00Z", "2025-02-16T14:00:00Z", "2025-02-17T11:00:00Z" ], "email_draft": "Dear Alex, Thank you for your application to the Senior Frontend Engineer role at Acme Corp...", "calendar_event_details": { "title": "Technical Interview — Alex Chen × Acme Corp", "duration_minutes": 60, "attendees": ["alex@email.com", "hiring@acme.com"] } } ``` |

### Agent 4 — Offer Writer

| Attribute          | Value                                                                                                                                           |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Role**           | VP of People & Culture                                                                                                                         |
| **Goal**           | Craft a compelling, personalised offer letter that reflects the company's culture, highlights the candidate's unique value, and presents the compensation package clearly |
| **Backstory**      | You are a VP of People who has written hundreds of offer letters that convert top talent. You know that an offer letter is not just paperwork — it's the candidate's first impression of what working at this company feels like. You weave in culture, growth opportunities, and genuine enthusiasm. |
| **Tools**          | `db_query` — fetch company culture notes, job details, candidate profile, and screening summary; `rag_retrieval` — retrieve similar past offers and company values documentation |
| **Expected Output**| ```json { "offer_letter": "Dear Alex,\n\nOn behalf of everyone at Acme Corp, I am thrilled to extend an offer for the role of Senior Frontend Engineer...", "compensation_summary": "Base: $165,000 | Equity: 15,000 RSUs (4yr vest) | Signing Bonus: $20,000 | Benefits: Full medical, dental, vision", "key_highlights": [ "Lead the new Design System initiative", "Direct mentorship from the CTO", "Flexible hybrid work — 2 days in-office" ] } ``` |

### Agent Pipeline Flow

```mermaid
sequenceDiagram
    participant API as FastAPI
    participant BG as Background Task
    participant S as CV Screener
    participant A as Assessor
    participant I as Scheduler
    participant O as Offer Writer
    participant DB as PostgreSQL
    participant SSE as SSE Stream

    API->>BG: Dispatch agent pipeline
    BG->>SSE: status: "screening"
    BG->>S: Run CV Screener
    S->>DB: Write agent_run (completed)
    BG->>SSE: status: "assessing"
    BG->>A: Run Assessor
    A->>DB: Write agent_run (completed)
    BG->>SSE: status: "scheduling"
    BG->>I: Run Scheduler
    I->>DB: Write agent_run (completed)
    BG->>SSE: status: "writing_offer"
    BG->>O: Run Offer Writer
    O->>DB: Write agent_run (completed)
    BG->>SSE: status: "complete"
```

---

## 7. RAG Pipeline Design

### Overview

HireIQ uses Retrieval-Augmented Generation (RAG) to ground agent decisions in real company data rather than relying solely on the LLM's parametric knowledge.

### Embedding Pipeline

```
                  ┌─────────────┐
  Job Description ???  Chunking   ???  ??? Gemini gemini-embedding-001 ??? pgvector INSERT
  Resume Text     │  (optional) │      (1536 dimensions)               (HNSW index)
  Culture Notes   │             │
                  └─────────────┘
```

1. **Job descriptions** are embedded on creation (`POST /api/v1/jobs`). Long descriptions are chunked (512-token windows with 50-token overlap) before embedding.
2. **Resumes** are embedded on upload (`POST /api/v1/candidates`). Text is extracted from PDFs using PyMuPDF, cleaned, and embedded as a single vector.
3. **Company culture notes** are embedded when updated — used as RAG context for the Offer Writer.

### Retrieval Strategies

| Agent        | What's Retrieved                                   | How                                                                  |
| ------------ | -------------------------------------------------- | -------------------------------------------------------------------- |
| CV Screener  | Top-K similar jobs to the candidate's resume       | `SELECT *, 1 - (resume_embedding <=> job_embedding) AS similarity`   |
| CV Screener  | Past screening decisions for similar profiles      | Cosine search on `resume_embedding` + join `applications`            |
| Offer Writer | Company culture notes + past successful offers     | Cosine search on `culture_notes` embedding + past `offer_text` where `status = 'hired'` |
| Candidate Search | Candidates matching a free-text skill query   | Embed query → cosine search on `resume_embedding`                    |

### Caching Strategy

- **Redis TTL cache (24h)**: Before calling Gemini's embedding API, compute a SHA-256 hash of the input text. Check Redis for a cached embedding. On miss, call the API and cache the result. This eliminates redundant embedding calls for identical text.

### Vector Index Configuration

```sql
CREATE INDEX idx_jobs_embedding ON jobs 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_candidates_resume_embedding ON candidates 
USING hnsw (resume_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## 8. Frontend Pages & Components

### Page Map

| Route                   | Page Name               | Key Features                                                                        |
| ----------------------- | ----------------------- | ----------------------------------------------------------------------------------- |
| `/`                     | Landing Page            | Hero with value proposition, feature highlights, CTA to sign in, animated gradient  |
| `/login`                | Login Page              | Email/password form, JWT storage, redirect to dashboard                             |
| `/signup`               | Signup Page             | Registration form with company name, auto-login after signup                        |
| `/dashboard`            | Recruiter Dashboard     | Metric cards (jobs, applications, avg score), recent activity feed, status chart     |
| `/jobs`                 | Job Listings            | Filterable/sortable table, status badges, quick actions (edit, close, delete)        |
| `/jobs/new`             | Create Job              | Multi-field form (title, description, requirements, seniority), live preview         |
| `/jobs/[id]`            | Job Detail              | Job info + Kanban board of applicants by stage, drag-and-drop status updates         |
| `/candidates`           | Candidate Database      | Semantic search bar, sortable table, resume preview drawer                           |
| `/candidates/[id]`      | Candidate Profile       | Full profile, resume viewer, all application history, skill tags                     |
| `/applications/[id]`    | Application Detail      | Agent output cards, real-time SSE progress bar, screening report, offer letter       |
| `/settings`             | Settings                | Company profile, API key management, Google Calendar OAuth, email preferences        |

### Core Component Library (shadcn/ui based)

- **Layout**: `Sidebar`, `TopNav`, `PageHeader`, `PageContainer`
- **Data Display**: `DataTable`, `MetricCard`, `StatusBadge`, `SkeletonLoader`
- **Agent UI**: `AgentProgressFeed`, `AgentOutputCard`, `AgentStatusIndicator`
- **Jobs**: `JobCard`, `JobForm`, `KanbanBoard`, `KanbanColumn`, `KanbanCard`
- **Candidates**: `CandidateTable`, `ResumeViewer`, `SemanticSearchBar`, `SkillTag`
- **Common**: `ConfirmDialog`, `EmptyState`, `ErrorBoundary`, `LoadingOverlay`
- **Charts**: `StatusPieChart`, `TimelineChart` (using Recharts)

### Frontend Architecture Decisions

- **React Query** for all server state — auto-refetch, cache invalidation, optimistic updates
- **Server Components** for data-heavy pages (dashboard, job detail) — reduced client JS
- **Client Components** for interactive elements (forms, Kanban drag-and-drop, SSE feed)
- **Skeleton loaders** everywhere — never show spinners or blank screens
- **Mobile-responsive** — sidebar collapses to hamburger menu, tables become cards on mobile

---

## 9. Phased Execution Plan

### Phase 1 — Foundation & DevOps Setup

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| Monorepo structure initialisation             | Create `backend/`, `frontend/`, root configs                                     |
| Docker Compose                                | FastAPI + PostgreSQL 16 (pgvector) + Redis containers                            |
| Environment variable management               | `.env.example` with all vars, python-dotenv for backend, `.env.local` for frontend|
| Database migrations setup                     | Alembic init, async SQLAlchemy engine config                                     |
| Basic health check endpoint                   | `GET /health` returns `{ status: "healthy", version: "0.1.0" }`                 |
| Project README badges and structure           | Badges, LICENSE file                                                             |
| **Checkpoint**                                | `docker compose up` works · DB migrations run · `/health` returns 200            |

### Phase 2 — Database & Core API

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| SQLAlchemy models                             | All 6 tables with typed columns, relationships, enums                            |
| Alembic migrations                            | Initial migration creating all tables + pgvector extension                        |
| CRUD services                                 | Jobs, Candidates, Applications — full async CRUD                                 |
| Pydantic v2 schemas                           | Request/response models with validation                                          |
| JWT authentication                            | Signup, login, token refresh, auth dependency                                    |
| API routes                                    | All endpoints from the spec, paginated list views                                |
| Error handling middleware                     | Global exception handler, consistent envelope responses                          |
| **Checkpoint**                                | All endpoints testable via Swagger UI at `/docs`                                 |

### Phase 3 — RAG Pipeline

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| Gemini embeddings service                     | Google GenAI client, SHA-256 cache check, Redis caching                         |
| pgvector extension setup                      | `CREATE EXTENSION vector` in migration, HNSW indexes                             |
| Resume parsing                                | PyMuPDF text extraction, cleaning, chunking utility                              |
| Embedding pipeline                            | Auto-embed on job creation and candidate upload                                  |
| Semantic search endpoint                      | `/candidates/search?q=...` → embed query → cosine similarity                    |
| **Checkpoint**                                | Upload a resume, query similar jobs — see cosine similarity scores               |

### Phase 4 — CrewAI Agent System

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| CrewAI setup                                  | Agent definitions, crew orchestration, sequential process                        |
| Custom tools                                  | `pgvector_similarity_search`, `db_query`, `email_draft`, `google_calendar_*`     |
| Agent pipeline trigger                        | Background task on `POST /applications`, sequential agent execution              |
| `agent_runs` logging                          | Input, output, tokens, duration, error state per agent                           |
| Async execution                               | FastAPI `BackgroundTasks` for non-blocking agent runs                             |
| SSE endpoint                                  | `GET /applications/{id}/status` streams agent progress events                    |
| **Checkpoint**                                | Submit test application → 4 agents run → results in DB → SSE stream works        |

### Phase 5 — Next.js Frontend

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| Next.js 14 App Router + TypeScript            | Project scaffold, tailwind config, shadcn/ui init                                |
| Auth flow                                     | Login/signup pages, JWT in httpOnly cookie, protected route middleware            |
| Dashboard page                                | Metric cards, recent activity feed, status distribution chart                    |
| Jobs pages                                    | List, create, detail with Kanban pipeline board                                  |
| Candidates pages                              | List with semantic search, profile with resume viewer                            |
| Application detail page                       | Agent output cards, SSE-powered live progress feed                               |
| Settings page                                 | Company profile, integrations                                                    |
| **Checkpoint**                                | Full recruiter workflow completable end-to-end in the browser                    |

### Phase 6 — Integrations

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| Google Calendar OAuth + API                   | OAuth flow, availability check, event creation                                   |
| Email sending (Resend)                        | Interview invite emails, offer letter delivery                                   |
| PDF resume upload                             | Cloudflare R2 integration, signed upload URLs                                    |
| Webhook support                               | Configurable webhook endpoints for external ATS systems                          |
| **Checkpoint**                                | Upload resume → agents run → email sent → calendar event created                 |

### Phase 7 — Polish, Testing & Deployment

| Task                                          | Details                                                                          |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| Backend unit tests (pytest)                   | All agent tools, CRUD services, auth flow                                        |
| API integration tests                         | Critical flows (application submission, agent pipeline)                          |
| Frontend E2E tests (Playwright)               | Core candidate → offer flow                                                      |
| Performance optimisation                      | DB query indexes, embedding caching audit, N+1 query fixes                       |
| Docker production build                       | Multi-stage Dockerfiles, nginx reverse proxy if needed                           |
| Deployment                                    | Backend → Railway, Frontend → Vercel                                             |
| Secrets management                            | Railway secrets, Vercel env vars, documentation                                  |
| **Checkpoint**                                | Live URL accessible · Full flow works in production                              |

---

## 10. Folder Structure

```
hireiq/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── routes/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── auth.py          # signup, login, me
│   │   │       │   ├── jobs.py          # CRUD + list with filters
│   │   │       │   ├── candidates.py    # CRUD + semantic search
│   │   │       │   ├── applications.py  # CRUD + SSE + trigger agents
│   │   │       │   └── dashboard.py     # aggregate metrics
│   │   │       └── deps.py             # shared dependencies (get_db, get_current_user)
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── crew.py                 # CrewAI crew definition + orchestration
│   │   │   ├── cv_screener.py          # Agent 1 definition
│   │   │   ├── assessor.py             # Agent 2 definition
│   │   │   ├── scheduler.py            # Agent 3 definition
│   │   │   └── offer_writer.py         # Agent 4 definition
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── db_query.py             # Database query tool for agents
│   │   │   ├── vector_search.py        # pgvector similarity search tool
│   │   │   ├── calendar.py             # Google Calendar API tool
│   │   │   ├── email_draft.py          # Email composition tool
│   │   │   └── rag_retrieval.py        # RAG context retrieval tool
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── company.py
│   │   │   ├── job.py
│   │   │   ├── candidate.py
│   │   │   ├── application.py
│   │   │   ├── agent_run.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── job.py
│   │   │   ├── candidate.py
│   │   │   ├── application.py
│   │   │   ├── agent_run.py
│   │   │   └── common.py              # APIResponse envelope, pagination
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── job.py
│   │   │   ├── candidate.py
│   │   │   ├── application.py
│   │   │   └── agent_pipeline.py      # Orchestrates the full agent run
│   │   ├── rag/
│   │   │   ├── __init__.py
???   ???   ???   ????????? embeddings.py          # Gemini embedding client + Redis cache
│   │   │   ├── chunker.py            # Text chunking utility
│   │   │   └── retriever.py          # Similarity search queries
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Pydantic Settings (env vars)
│   │   │   ├── database.py           # Async SQLAlchemy engine + session
│   │   │   ├── security.py           # JWT encode/decode, password hashing
│   │   │   ├── redis.py              # Redis client singleton
│   │   │   └── exceptions.py         # Custom exception classes
│   │   └── main.py                   # FastAPI app factory, middleware, lifespan
│   ├── alembic/
│   │   ├── versions/                 # Migration files
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── tests/
│   │   ├── conftest.py               # Fixtures: test DB, client, auth tokens
│   │   ├── test_auth.py
│   │   ├── test_jobs.py
│   │   ├── test_candidates.py
│   │   ├── test_applications.py
│   │   ├── test_agents/
│   │   │   ├── test_cv_screener.py
│   │   │   ├── test_assessor.py
│   │   │   ├── test_scheduler.py
│   │   │   └── test_offer_writer.py
│   │   └── test_rag/
│   │       ├── test_embeddings.py
│   │       └── test_retriever.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                # Root layout with providers
│   │   ├── page.tsx                  # Landing page
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx            # Sidebar + topnav layout
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── jobs/
│   │   │   │   ├── page.tsx          # Job listings
│   │   │   │   ├── new/page.tsx      # Create job
│   │   │   │   └── [id]/page.tsx     # Job detail + Kanban
│   │   │   ├── candidates/
│   │   │   │   ├── page.tsx          # Candidate database
│   │   │   │   └── [id]/page.tsx     # Candidate profile
│   │   │   ├── applications/
│   │   │   │   └── [id]/page.tsx     # Application detail + agent feed
│   │   │   └── settings/page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                       # shadcn/ui primitives
│   │   ├── agents/
│   │   │   ├── agent-progress-feed.tsx
│   │   │   ├── agent-output-card.tsx
│   │   │   └── agent-status-indicator.tsx
│   │   ├── jobs/
│   │   │   ├── job-card.tsx
│   │   │   ├── job-form.tsx
│   │   │   └── kanban-board.tsx
│   │   ├── candidates/
│   │   │   ├── candidate-table.tsx
│   │   │   ├── resume-viewer.tsx
│   │   │   └── semantic-search-bar.tsx
│   │   ├── dashboard/
│   │   │   ├── metric-card.tsx
│   │   │   ├── activity-feed.tsx
│   │   │   └── status-chart.tsx
│   │   └── layout/
│   │       ├── sidebar.tsx
│   │       ├── top-nav.tsx
│   │       └── page-header.tsx
│   ├── lib/
│   │   ├── api.ts                    # Axios/Fetch client + interceptors
│   │   ├── auth.ts                   # JWT helpers, auth context
│   │   ├── hooks/
│   │   │   ├── use-jobs.ts
│   │   │   ├── use-candidates.ts
│   │   │   ├── use-applications.ts
│   │   │   └── use-sse.ts            # SSE hook for agent progress
│   │   └── utils.ts                  # Formatters, constants
│   ├── types/
│   │   ├── job.ts
│   │   ├── candidate.ts
│   │   ├── application.ts
│   │   ├── agent.ts
│   │   └── api.ts                    # APIResponse<T> generic
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── docker-compose.yml                # Local dev: FastAPI + PG + pgvector + Redis
├── docker-compose.prod.yml           # Production overrides
├── .env.example                      # All env vars with empty values
├── .gitignore
├── LICENSE
└── README.md                         # ← You are here
```

---

## 11. Environment Variables

```bash
# ──────────────────────────────────────
# Gemini
# ──────────────────────────────────────
GEMINI_API_KEY=                       # Preferred Gemini API key for CrewAI + embeddings
GOOGLE_API_KEY=                       # Optional alternate env var accepted by Google tooling
GEMINI_MODEL=gemini/gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSION=1536

# ──────────────────────────────────────
# Database
# ──────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://hireiq:password@localhost:5432/hireiq
PGVECTOR_ENABLED=true                 # Enable pgvector extension on startup

# ──────────────────────────────────────
# Authentication
# ──────────────────────────────────────
JWT_SECRET_KEY=                       # Random 64-char secret for JWT signing
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ──────────────────────────────────────
# Redis
# ──────────────────────────────────────
REDIS_URL=redis://localhost:6379/0    # Used for job queue and embedding cache

# ──────────────────────────────────────
# Google Calendar (OAuth 2.0)
# ──────────────────────────────────────
GOOGLE_CLIENT_ID=                     # From Google Cloud Console
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback

# ──────────────────────────────────────
# Email (Resend)
# ──────────────────────────────────────
RESEND_API_KEY=                       # From resend.com dashboard
FROM_EMAIL=noreply@hireiq.dev

# ──────────────────────────────────────
# Cloud Storage (Cloudflare R2)
# ──────────────────────────────────────
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=hireiq-resumes

# ──────────────────────────────────────
# Frontend
# ──────────────────────────────────────
NEXT_PUBLIC_API_URL=http://localhost:8000  # FastAPI backend URL
```

---

## 12. Key Engineering Decisions

### Why CrewAI over LangChain Agents?

CrewAI's role-based agent design maps naturally onto hiring domain personas (Screener, Assessor, Coordinator, VP of People). Its sequential `Process.sequential` execution model ensures each agent builds on the previous one's output — exactly what a hiring pipeline demands. LangChain Agents are more general-purpose and require significantly more boilerplate to achieve the same structured collaboration.

### Why pgvector over Pinecone?

Keeping embeddings in PostgreSQL via pgvector means:
- **Co-located data**: vector similarity queries can `JOIN` with relational tables (applications, agent_runs) in a single query
- **Single database**: no additional infrastructure to manage, no cross-service latency
- **HNSW indexes**: sub-millisecond approximate nearest-neighbour search at the scale this application needs (thousands, not billions, of vectors)

Pinecone would be overkill for this use case and would add operational complexity without proportional benefit.

### Why FastAPI over Django?

- **Async-native**: all database operations use `asyncpg` — no thread pool hacks
- **Pydantic v2**: native request/response validation with performance improvements over v1
- **SSE support**: first-class `StreamingResponse` for real-time agent progress
- **BackgroundTasks**: built-in async task execution without needing Celery for the MVP
- **OpenAPI auto-docs**: Swagger UI at `/docs` for free

### Why Next.js App Router over Pages Router?

- **Server Components**: heavy data tables (jobs, candidates) are rendered server-side, reducing client JS bundle
- **Streaming**: React Suspense boundaries enable progressive page loading with skeleton loaders
- **Server Actions**: form submissions bypass the API client layer for simple mutations
- **Nested layouts**: the dashboard shell (sidebar + topnav) is defined once and shared across routes

### Why Redis?

Redis serves dual purpose:
1. **Embedding cache**: SHA-256 hashed text ??? embedding vector, TTL 24h. Prevents duplicate Gemini API calls.
2. **Future-proof job queue**: while Phase 4 uses FastAPI's `BackgroundTasks` for simplicity, Redis enables a seamless upgrade to Celery/RQ if agent workloads demand true distributed task processing.

---

## 13. Demo Script (For Interviews)

Follow this script for a 7-minute technical demo:

### 1. Dashboard Overview (30s)
Open the recruiter dashboard. Point out the live metric cards — total active jobs, applications in pipeline, average screening score. Highlight the real-time activity feed and status distribution chart.

### 2. Create a Job Listing (45s)
Navigate to `/jobs/new`. Create a job: "Senior Frontend Engineer" requiring 3+ years React, TypeScript, and system design experience. Set seniority to "Senior". Show how the job description is immediately embedded for semantic search.

### 3. Upload a Candidate Resume (45s)
Go to `/candidates`. Upload a sample resume PDF. Show the toast notification confirming text extraction and embedding. Open the candidate profile — highlight the parsed skills and experience.

### 4. Submit an Application — Watch the Agents (2m)
Navigate to the job detail page. Select the candidate and click "Apply". Switch to the application detail page. **This is the money shot:**
- Watch the SSE-powered progress feed animate in real time
- CV Screener runs → score appears, matched/missing skills rendered as badges
- Assessor runs → generated questions display in formatted cards
- Scheduler runs → proposed time slots with email preview
- Offer Writer runs → beautifully formatted offer letter with compensation summary

### 5. Inspect Agent Observability (1m)
Open the agent runs section. Show: input text, full JSON output, token count, latency in milliseconds. Explain how this enables cost tracking and performance optimisation.

### 6. Semantic Search Demo (1m)
Go to `/candidates`. Type "experienced Python developer with ML background" into the semantic search bar. Show candidates ranked by cosine similarity score — emphasise this is semantic, not keyword matching.

### 7. Database Inspection (1m)
Open the PostgreSQL console (or pgAdmin). Show:
- The `embeddings` column in the `jobs` table — real 1536-dimensional vectors
- The `agent_runs` table — full audit trail of every agent execution
- Run a raw cosine similarity query to show the maths behind the search

---

## 14. Stretch Goals (Post-MVP)

| Priority | Goal                     | Description                                                                                                    |
| -------- | ------------------------ | -------------------------------------------------------------------------------------------------------------- |
| P1       | **Fine-tuning**          | Fine-tune Gemini screening prompts on the company's historical decisions to improve scoring accuracy over time   |
| P1       | **Analytics Dashboard**  | Track offer acceptance rate, time-to-hire, cost-per-agent-run, agent accuracy vs human reviewer agreement       |
| P2       | **Bias Detection Agent** | Fifth agent that reviews screening outputs for potentially biased language or criteria before surfacing results |
| P2       | **Multi-Tenant**         | Full tenant isolation with row-level security in PostgreSQL, company-scoped JWT claims                         |
| P3       | **Chrome Extension**     | Scrape LinkedIn profiles directly into the candidate database with one click                                   |
| P3       | **n8n Integration**      | Automated workflow triggers from external ATS webhooks (Greenhouse, Lever, Workday)                            |
| P3       | **Candidate Portal**     | Self-service portal where candidates can track their application status and submit assessments                  |
| P3       | **Mobile App**           | React Native companion app for recruiters to review candidates on-the-go                                       |
