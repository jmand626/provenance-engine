# Provenance Engine

A local MVP for tracing reused legislative language from public model legislation into state bills. The monorepo is organized as a Python data pipeline worker, a Java Spring Boot backend, and a frontend viewer.

## Repository Layout

```text
.
├── backend/        # Java Spring Boot REST API
├── data-pipeline/  # Python scraping and NLP worker
├── frontend/       # Web frontend
└── docker-compose.yml
```

## Prerequisites

- Docker Desktop or Docker Engine with Docker Compose
- Python 3.11+
- Java 17+
- Maven 3.9+
- Node.js 20+ when the frontend is initialized

## Start Local Infrastructure

From the repository root:

```bash
docker compose up -d
```

This starts:

- PostgreSQL on `localhost:5432`
- Elasticsearch on `http://localhost:9200`

Default local database settings:

```text
POSTGRES_USER=provenance
POSTGRES_PASSWORD=provenance
POSTGRES_DB=provenance
```

Check container status:

```bash
docker compose ps
```

Stop the containers:

```bash
docker compose down
```

Stop the containers and remove local data volumes:

```bash
docker compose down -v
```

## Run The Python Worker

The worker scaffold lives in `data-pipeline`.

Create and activate a virtual environment:

```bash
cd data-pipeline
python -m venv .venv
```

If you use Git Bash on windows, like me, its this:

```Git Bash on Windows
source .venv/Scripts/activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the worker entry point:

```bash
python main.py
```

## Run The Backend API

The backend scaffold lives in `backend`.

Start PostgreSQL first:

```bash
docker compose up -d postgres
```

Then run Spring Boot:

```bash
cd backend
mvn spring-boot:run
```

The backend is configured for:

```text
http://localhost:8080
jdbc:postgresql://localhost:5432/provenance
```

## Frontend

The `frontend` directory is reserved for the web viewer. The project has not been initialized yet, but the planned stack is Next.js, TypeScript, and Tailwind CSS.

## Notes

- Core NLP alignment, scraping, and API domain logic are intentionally not implemented in this scaffold.
- Elasticsearch security and HTTPS are disabled for local development only.
- The Docker volumes `postgres-data` and `elasticsearch-data` persist local state between restarts.

The actual pieces will be filled in future commits
