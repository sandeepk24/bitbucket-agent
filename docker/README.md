# Docker

Images are built from the repository root via `docker compose`.

| File | Role |
| --- | --- |
| `Dockerfile.backend` | Python 3.12 FastAPI image |
| `Dockerfile.frontend` | Vite build + nginx |
| `nginx.conf` | SPA routing and `/api` proxy to the backend service |

```bash
docker compose up --build
```

- UI: http://localhost:8080
- API health: http://localhost:8000/api/v1/health
