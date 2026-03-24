# Backend Scripts

This folder contains small operational scripts for local development and demo setup.

## Demo Seeding

Seed a demo company, jobs, and candidates through the public API:

```bash
python backend/scripts/seed_demo_company.py --base-url http://127.0.0.1:8000 --company-name "HireIQ Demo Talent"
```

The script:
- creates a demo recruiter account
- seeds a small dataset of jobs and candidates
- does not create any applications or trigger the screening pipeline

## Resetting Demo Data

There is no automatic reset script yet. For a clean rerun, use one of these approaches:
- run the script against a fresh local database
- delete the seeded demo company and related records from Postgres before seeding again

If you want, a future improvement is to add a companion reset script that removes only the demo company data created by the seeder.
