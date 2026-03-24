# HireIQ Deployment Runbook

This runbook covers the final production rollout for the backend on Railway and the frontend on Vercel.

## Local Container Validation

Run the full pre-deploy validation flow from the repo root:

1. `docker compose up -d --build db redis api frontend frontend-e2e`
2. `docker compose exec api alembic upgrade head`
3. `docker compose exec api python -m pytest -q`
4. `docker compose exec frontend npm run lint`
5. `docker compose exec frontend npm run build`
6. `docker compose exec frontend-e2e sh -lc "npm ci && npm run e2e"`

On Windows PowerShell, the same sequence is wrapped in [scripts/compose.ps1](/D:/Projects/hireIQ/scripts/compose.ps1) via `.\scripts\compose.ps1 -Task validate`.

## Backend / Railway

### Create the Railway service

1. Create a new Railway project for the backend.
2. Point the service at the `backend/` directory.
3. Use [railway.toml](/D:/Projects/hireIQ/backend/railway.toml) as the deployment config.

### Required backend environment variables

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `BACKEND_PUBLIC_URL`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_EMBEDDING_MODEL`
- `GEMINI_EMBEDDING_DIMENSION`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_CALENDAR_ID`
- `RESEND_API_KEY`
- `FROM_EMAIL`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`
- `R2_REGION`
- `ATS_WEBHOOK_SECRET`
- `ATS_WEBHOOK_PROVIDER`
- `ALLOWED_ORIGINS`

### Backend release steps

1. Deploy the Railway service.
2. Run `alembic upgrade head` against the production database.
3. Verify `/health`.
4. Verify `/docs` loads.
5. Create a test recruiter account.
6. Verify Google Calendar connection from the settings page.
7. Verify candidate PDF upload and resume download.
8. Submit a test application and verify the SSE status stream.

## Frontend / Vercel

### Create the Vercel project

1. Create a new Vercel project for the `frontend/` directory.
2. Use [vercel.json](/D:/Projects/hireIQ/frontend/vercel.json).

### Required frontend environment variables

- `NEXT_PUBLIC_API_URL`
- `INTERNAL_API_URL`

### Frontend release steps

1. Deploy the Vercel project.
2. Log in through the production frontend.
3. Verify protected route handling.
4. Open an application detail page and confirm the SSE feed replays.
5. Verify the settings page shows live integration status.

## Production smoke checklist

1. Signup, login, and logout succeed.
2. Job creation, update, and closure succeed.
3. Candidate creation works for both text and PDF flows.
4. Application submission triggers all four agent stages.
5. Interview scheduling and offer email metadata render correctly.
6. ATS webhook endpoint accepts a valid signed payload.

## Rollback

1. Roll frontend back through Vercel to the last healthy deployment.
2. Roll backend back through Railway to the last healthy deployment.
3. If a schema change is implicated, pause traffic before database rollback.
4. Re-run the production smoke checklist after rollback.
