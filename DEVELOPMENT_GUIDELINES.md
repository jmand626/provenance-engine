# Development Guidelines & Workflow

## 1. Coding Philosophy
* **Stop and Test:** Do not implement multiple features at once. Implement a single function or endpoint, verify it works (unit test or manual trigger), and then proceed.
* **Atomic Commits:** Commit often with descriptive messages. Each commit should represent one logical change.
* **No Task Logs:** Do not leave "Task Log" comments or verbose "AI was here" headers in the source code. Use standard docstrings/JSDoc for actual logic explanation only.
* **Idempotency:** Scripts (especially scrapers and database migrations) must be safe to run multiple times. Check if a record exists before inserting.

## 2. Git & Branching Strategy
* **Feature Branches:** Do not work on the `main` branch. Create a new branch for every distinct task (e.g., `feature/alec-scraper`, `setup/docker-config`).
* **PR Summaries:** Before merging a branch, provide a concise summary of what was changed and any new environment variables required.

## 3. Tool-Specific Instructions (For AI Agent)
* **Verify Context:** Before editing a file, read the existing imports and patterns to maintain consistency.
* **Check the Logs:** If a build fails, prioritize reading the compiler or runtime logs before guessing a fix.
* **Java Standards:** Follow standard Maven directory structures and use Lombok for boilerplate reduction where appropriate.
* **Python Standards:** Use Type Hinting for all function signatures in the data-pipeline.

## Todo:
* Add Java/Python Linters?
