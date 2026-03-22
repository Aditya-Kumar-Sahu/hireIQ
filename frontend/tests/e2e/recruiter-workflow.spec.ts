import { expect, test } from "@playwright/test";

test("recruiter can sign up, create a candidate and job, and open an application", async ({
  page,
}) => {
  const slug = Date.now();
  const email = `playwright.${slug}@example.com`;
  const candidateName = `Playwright Candidate ${slug}`;
  const jobTitle = `Playwright Backend Engineer ${slug}`;

  await page.goto("/signup");

  await page.getByLabel("Company name").fill("Playwright Hiring");
  await page.getByLabel("Work email").fill(email);
  await page.getByLabel("Password").fill("supersecure123");
  await page.getByTestId("auth-submit").click();

  await page.waitForURL("**/dashboard");
  await expect(page.getByText("Recruiter command center")).toBeVisible();

  await page.getByRole("link", { name: "Candidates", exact: true }).click();
  await expect(page.getByText("Semantic search and intake")).toBeVisible();

  await page.getByPlaceholder("Candidate name").fill(candidateName);
  await page.getByPlaceholder("candidate@example.com").fill(`candidate.${slug}@example.com`);
  await page.getByPlaceholder("Paste resume text here").fill(
    "Backend engineer with FastAPI, PostgreSQL, Docker, and API testing experience.",
  );
  await page.getByTestId("candidate-save").click();

  await expect(page.getByRole("heading", { name: candidateName, exact: true })).toBeVisible();

  await page.goto("/jobs/new");
  await expect(page.getByText("Open a new hiring lane")).toBeVisible();

  await page.getByLabel("Role title").fill(jobTitle);
  await page.getByLabel("Description").fill(
    "Build backend APIs, recruiter workflows, and orchestration features.",
  );
  await page.getByLabel("Requirements").fill(
    "FastAPI PostgreSQL Docker testing communication",
  );
  await page.getByTestId("job-create-submit").click();

  await page.waitForURL(/\/jobs\/.+/);
  await expect(page.getByText(jobTitle)).toBeVisible();

  await page.getByTestId("application-create-submit").click();

  await page.waitForURL(/\/applications\/.+/);
  await expect(page.getByText("Application Detail")).toBeVisible();
  await expect(page.getByText("Pipeline activity")).toBeVisible();
  await expect(page.getByText("Execution log")).toBeVisible();

  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await expect(page.getByText("Workspace configuration")).toBeVisible();
  await expect(page.getByText("ATS webhooks")).toBeVisible();
});
