# Project Tasks

This document outlines the tasks to be completed for the project. It is an append-only document. Do not delete tasks; only mark them as complete.

---

### Task 1: Establish Comprehensive Testing Framework

- **Micro-goals:**
    - Integrate `pytest` for the Python backend.
    - Set up a testing framework (e.g., Jest/Playwright) for the Next.js frontend.
    - Configure end-to-end tests with Playwright.
    - Write initial unit tests for core backend logic (e.g., `submit_agent.py`).
    - Write initial component tests for the frontend (e.g., `SubmissionForm.tsx`).
- **Completion Criteria:**
    - `pytest` runs successfully in the `backend` directory.
    - `npm run test` executes tests in the root directory for the frontend.
    - Playwright tests for the submission form are created and passing.
    - Core business logic and UI components have baseline test coverage.
- **Status:** [ ] Incomplete
- **Proof of Completion:**
    - ```
      // AI Agent to fill this section with command output or file paths
      ```

---

### Task 2: Develop CI/CD Pipeline with GitHub Actions

- **Micro-goals:**
    - Create a `.github/workflows` directory.
    - Implement a `ci.yml` workflow file.
    - The workflow should trigger on `push` and `pull_request` to the `main` branch.
    - The workflow must install dependencies for both frontend (`pnpm install`) and backend (`pip install`).
    - The workflow must run linting for both frontend (`pnpm lint`) and backend (`black --check .` and `ruff check .`).
    - The workflow must run all automated tests.
    - The workflow must run a build of the Next.js application (`pnpm build`).
- **Completion Criteria:**
    - A GitHub Action successfully runs on a push to the repository.
    - The action correctly installs all dependencies.
    - The action successfully executes linting, testing, and build steps.
    - A failing test or linting error causes the workflow to fail.
- **Status:** [ ] Incomplete
- **Proof of Completion:**
    - ```
      // AI Agent to fill this section with a link to a successful workflow run or the YML file path.
      ```

---

### Task 3: Enhance Code Quality with Automated Reviews

- **Micro-goals:**
    - Research and select a suitable GitHub Action for automated code review (e.g., Code-review GPT, Codeac, or a custom script using OpenRouter).
    - Configure the selected action to run on pull requests.
    - The action should post comments with suggestions for improvements.
- **Completion Criteria:**
    - An automated code review action is configured in the repository.
    - The action successfully analyzes a pull request and provides feedback.
- **Status:** [ ] Incomplete
- **Proof of Completion:**
    - ```
      // AI Agent to fill this section with a link to a PR comment from the bot or the configuration file.
      ```

---

### Task 4: Implement Vulnerability and Secret Scanning

- **Micro-goals:**
    - Add a security scanning action (e.g., Snyk, Trivy, or GitHub's own CodeQL) to the CI workflow.
    - Add a secret scanning tool (e.g., Gitleaks or TruffleHog) to the CI workflow.
- **Completion Criteria:**
    - The CI pipeline includes steps for vulnerability and secret scanning.
    - The pipeline fails if high-severity vulnerabilities or secrets are detected.
- **Status:** [ ] Incomplete
- **Proof of Completion:**
    - ```
      // AI Agent to fill this section with the YML configuration and output from a scan.
      ```

---

### Task 5: Prepare for Deployment

- **Micro-goals:**
    - Create deployment-specific GitHub Action workflows (e.g., `deploy-frontend.yml`, `deploy-backend.yml`).
    - Document the required environment variables and secrets for Vercel and Render.
    - Create a `.env.example` file in the root directory if one doesn't exist.
- **Completion Criteria:**
    - Deployment workflows are created.
    - A comprehensive list of required environment variables is documented.
- **Status:** [ ] Incomplete
- **Proof of Completion:**
    - ```
      // AI Agent to fill this section with file paths of the created workflows and documentation.
      ```

---
