# Architecture

Bitbucket Agent is an enterprise DevOps intelligence console for Bitbucket Cloud / Data Center, pull requests, Bamboo CI, and production investigation. This milestone delivers a runnable platform only.

```
┌─────────────────────────────┐     ┌──────────────────────────────────┐
│  React + Vite (TypeScript)  │     │  FastAPI (Python 3.12+)          │
│  Sidebar + top nav + pages  │────▶│  /api/v1/health                  │
│  TanStack Query             │     │  /api/v1/ready                   │
└─────────────────────────────┘     │  /api/v1/settings                │
                                    │                                  │
                                    │  providers/                      │
                                    │    bitbucket  (stub)             │
                                    │    bamboo     (stub)             │
                                    │    ai/bedrock (stub)             │
                                    │    ai/strands (stub)             │
                                    └──────────────────────────────────┘
```

## Boundaries

| Layer | Responsibility | Out of scope (Milestone 1) |
| --- | --- | --- |
| Frontend | Layout, routing, health display | Live Bitbucket/Bamboo data |
| API | Health, readiness, sanitized settings | Inference, ingestion |
| Providers | Typed interfaces + config checks | HTTP to Bitbucket, Bamboo, or Bedrock |

Tokens and credentials stay in process environment. They are never logged or returned on API responses.

## Local topology

- Vite (`http://localhost:5173`) proxies `/api` to FastAPI (`http://localhost:8000`)
- Docker Compose serves the UI on `http://localhost:8080` behind nginx, which proxies `/api` to the backend container
