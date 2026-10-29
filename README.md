# Bitbucket Agent

Enterprise DevOps intelligence for Bitbucket repositories, pull requests, Bamboo CI, and production investigation. Amazon Bedrock and Strands Agents will power analysis in a later milestone.

This repository is the **foundation**: a runnable React + FastAPI app, Docker Compose, health checks, and typed provider boundaries. Bitbucket API calls, Bamboo ingestion, and model inference are **not implemented yet**.

**Author:** [sandeepk24](https://github.com/sandeepk24)

---

## What works today

- FastAPI backend with structured logging, CORS, `/api/v1/health`, `/api/v1/ready`, and `/api/v1/settings`
- React + Vite + TypeScript dashboard with sidebar, top navigation, and seven workspace pages
- Environment-based configuration (Pydantic Settings)
- AI provider **interfaces** for Amazon Bedrock and Strands Agents (stubs)
- Bitbucket and Bamboo client **stubs** that only report whether tokens are configured
- Docker Compose for local backend + frontend
- pytest (backend) and Vitest (frontend)

## What is not implemented

| Capability | Status |
| --- | --- |
| Bitbucket REST calls | Not started |
| Pull request ingestion | Not started |
| PR deep analysis | Not started |
| Bamboo build ingestion | Not started |
| Production investigation | Not started |
| Bedrock `InvokeModel` | Interface only |
| Strands Agents runtime | Interface only |

---

## Repository layout

```
bitbucket-agent/
├── frontend/     React + Vite + TypeScript UI
├── backend/      FastAPI + Pydantic v2 API
├── docs/         Architecture, API, implementation plan
└── docker/       Dockerfiles and nginx config
```

---

## Local development

### Prerequisites

- Node.js 20+
- Python 3.12+
- Docker (optional, for Compose)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Ready: http://localhost:8000/api/v1/ready

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the backend.

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- UI: http://localhost:8080
- API: http://localhost:8000/api/v1/health

---

## Tests

```bash
# Backend
cd backend
source .venv/bin/activate
pytest

# Frontend
cd frontend
npm test
```

---

## Configuration

Copy `.env.example` to `.env`. Important variables:

| Variable | Purpose |
| --- | --- |
| `BITBUCKET_BASE_URL` | Bitbucket API host (unused until Milestone 2) |
| `BITBUCKET_WORKSPACE` | Workspace slug (unused until Milestone 2) |
| `BITBUCKET_TOKEN` | Access token — never logged or returned |
| `BAMBOO_BASE_URL` | Bamboo host (unused until Milestone 3) |
| `BAMBOO_TOKEN` | Bamboo token — never logged or returned |
| `AI_PROVIDER` | `bedrock` or `strands` |
| `BEDROCK_ENABLED` | Must stay `false` until inference is implemented |
| `STRANDS_ENABLED` | Must stay `false` until the agent runtime is implemented |

---

## Dashboard navigation

| Page | Route | Purpose |
| --- | --- | --- |
| Dashboard | `/` | Platform health and foundation status |
| Repositories | `/repositories` | Bitbucket repository browser (placeholder) |
| Pull Requests | `/pull-requests` | PR inbox (placeholder) |
| PR Deep Analysis | `/pr-analysis` | AI-assisted review (placeholder) |
| Bamboo Builds | `/bamboo` | CI build intelligence (placeholder) |
| Production Investigation | `/production` | Incident investigation (placeholder) |
| Settings | `/settings` | Non-secret runtime configuration |

---

## License

MIT
