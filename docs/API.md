# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

All endpoints in this milestone report process health and **configuration presence**. They do not call Bitbucket, Bamboo, Amazon Bedrock, or Strands Agents.

## GET /health

Liveness plus configuration flags. Secret values are never included.

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "bitbucket_configured": false,
  "bamboo_configured": false,
  "ai_provider": "bedrock",
  "bedrock_configured": false,
  "strands_configured": false
}
```

## GET /ready

Readiness for process orchestration. Returns `200` when the API can serve traffic.

```json
{
  "status": "ready"
}
```

## GET /settings

Non-secret runtime settings (Bitbucket base URL, workspace slug, Bamboo host, AWS region, selected AI provider, model id). Tokens are omitted.

## GET /

Service metadata used by operators and Compose health probes.

```json
{
  "name": "Bitbucket Agent",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```
