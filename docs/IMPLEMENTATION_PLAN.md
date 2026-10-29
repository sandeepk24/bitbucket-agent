# Implementation Plan

## Milestone 1 — Architecture and Foundation (this delivery)

- [x] Monorepo scaffolding (`frontend/`, `backend/`, `docs/`, `docker/`)
- [x] Architecture and API documentation
- [x] React + Vite + TypeScript frontend with enterprise dashboard layout
- [x] FastAPI backend with env-based config and structured logging
- [x] Health, readiness, and settings endpoints
- [x] AI provider interfaces (Bedrock, Strands) — stubs only
- [x] Bitbucket and Bamboo client stubs (configuration check only)
- [x] Docker Compose for local development
- [x] pytest (backend) and Vitest (frontend)

## Milestone 2 — Bitbucket connectivity

- [x] Authenticated Bitbucket Data Center REST client (HTTP access tokens)
- [x] Project and repository discovery APIs
- [ ] Frontend repository browser
- [ ] Pull request list/detail APIs

## Milestone 3 — PR intelligence and Bamboo

- [ ] PR Deep Analysis (diff summaries, risk signals) via Bedrock / Strands
- [ ] Bamboo build ingestion and failure clustering
- [ ] Insight APIs and UI

## Milestone 4 — Production investigation and platform

- [ ] Production investigation workflows
- [ ] Persistence
- [ ] Authn/authz for the accelerator itself
- [ ] Evaluation metrics and dashboard polish
