# Architecture

Bitbucket Agent is an enterprise DevOps intelligence console for Bitbucket Data Center, pull requests, Bamboo CI, and production investigation.

```
┌─────────────────────────────┐     ┌──────────────────────────────────┐
│  React + Vite (TypeScript)  │     │  FastAPI (Python 3.12+)          │
│  Sidebar + top nav + pages  │────▶│  /api/v1/health                  │
│  TanStack Query             │     │  /api/bitbucket/health           │
└─────────────────────────────┘     │  /api/bitbucket/projects         │
                                    │  /api/bitbucket/.../repos        │
                                    │  /api/bitbucket/.../pull-requests│
                                    │  providers/                      │
                                    │    bitbucket  (DC 10.2 REST)     │
                                    │    bamboo     (stub)             │
                                    │    ai/bedrock (stub)             │
                                    │    ai/strands (stub)             │
                                    └──────────────────────────────────┘
                                              │
                                              ▼
                                    Bitbucket Data Center 10.2.x
```

## Boundaries

| Layer | Responsibility | Out of scope |
| --- | --- | --- |
| Frontend | Layout, routing, project/repo/PR browse | PR analysis, Bamboo, AI |
| API | Process health plus Bitbucket discovery | Inference |
| Bitbucket client | PAT auth, retries, pagination, PRs | Cloud REST |
| AI providers | Typed interfaces | InvokeModel / Strands runtime |

Tokens stay in process environment. They are never logged or returned on API responses.

## Local topology

- Vite (`http://localhost:5173`) proxies `/api` to FastAPI (`http://localhost:8000`)
- Docker Compose serves the UI on `http://localhost:8080` behind nginx, which proxies `/api` to the backend container
