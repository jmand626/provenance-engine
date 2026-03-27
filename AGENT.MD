# AGENTS.md

## Project Context
- **Name:** The Provenance Engine (Local MVP)
- **Architecture:** Monorepo containing a Python worker (`/data-pipeline`), a Java Spring Boot backend (`/backend`), and a web frontend (`/frontend`).
- **Goal:** Trace identical legislative language from partisan think tanks to official state legislation using NLP alignment algorithms.

## Setup & Execution Commands
- **Docker:** `docker-compose up -d` (Starts PostgreSQL and Elasticsearch)
- **Backend (Java):** `cd backend && ./mvnw spring-boot:run`
- **Pipeline (Python):** `cd data-pipeline && python main.py`
- **Frontend (Node):** `cd frontend && npm run dev`

## Coding Philosophy & Workflow
- **Plan First:** Always explicitly output a plan before writing complex logic.
- **Stop and Test:** Implement a single function or API endpoint, verify it works, and then proceed. Do not write hundreds of lines blindly.
- **Idempotency:** Scripts (especially web scrapers and DB migrations) must be safe to run multiple times without duplicating data.
- **No Task Logs:** Do not leave verbose "AI was here" headers or task logs in the source code. Use standard Javadoc or Python docstrings strictly for logic explanation.

## Code Style & Tech Stack
### `/data-pipeline` (Python)
- Use Python 3.11+.
- Enforce Type Hinting for all function signatures.
- Prefer `requests` and `beautifulsoup4` for scraping. 
- Use parameterized queries for all `psycopg2` database interactions to prevent SQL injection.

### `/backend` (Java Spring Boot)
- Use Java 17+.
- Follow standard Spring Boot MVC architecture (Controller -> Service -> Repository).
- Use `Lombok` to reduce boilerplate (e.g., `@Data`, `@RequiredArgsConstructor`).
- Return standard JSON responses.

### `/frontend` (React/Next.js)
- Use TypeScript strict mode.
- Use Tailwind CSS for styling.
- Functional components only.

## Git Strategy
- **Atomic Commits:** Commit often with descriptive messages. One logical change per commit.
- **Branching:** Do not work on the `main` branch. Create a new branch for every distinct task.
