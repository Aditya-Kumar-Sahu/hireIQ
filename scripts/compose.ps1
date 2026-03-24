param(
    [ValidateSet("up", "migrate", "test-api", "lint-frontend", "build-frontend", "test-e2e", "validate")]
    [string]$Task = "validate"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & docker compose @Args
}

switch ($Task) {
    "up" {
        Invoke-Compose up -d --build db redis api frontend frontend-e2e
    }
    "migrate" {
        Invoke-Compose exec api alembic upgrade head
    }
    "test-api" {
        Invoke-Compose exec api python -m pytest -q
    }
    "lint-frontend" {
        Invoke-Compose exec frontend npm run lint
    }
    "build-frontend" {
        Invoke-Compose exec frontend npm run build
    }
    "test-e2e" {
        Invoke-Compose exec frontend-e2e sh -lc "npm ci && npm run e2e"
    }
    "validate" {
        Invoke-Compose up -d --build db redis api frontend frontend-e2e
        Invoke-Compose exec api alembic upgrade head
        Invoke-Compose exec api python -m pytest -q
        Invoke-Compose exec frontend npm run lint
        Invoke-Compose exec frontend npm run build
        Invoke-Compose exec frontend-e2e sh -lc "npm ci && npm run e2e"
    }
}
