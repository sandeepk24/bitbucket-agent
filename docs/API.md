# API Reference

Interactive docs: `http://localhost:8000/docs`

Tokens and credentials are never included in responses.

## Process health (`/api/v1`)

### GET /api/v1/health

Liveness plus configuration flags.

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

### GET /api/v1/ready

Returns `200` when the API process can serve traffic.

### GET /api/v1/settings

Non-secret runtime settings. `BITBUCKET_TOKEN` is omitted.

## Bitbucket Data Center (`/api/bitbucket`)

These routes call Bitbucket 10.2.x. See [BITBUCKET.md](./BITBUCKET.md).

### GET /api/bitbucket/health

```json
{
  "configured": true,
  "reachable": true,
  "authenticated": true,
  "base_url": "https://bitbucket.example.com",
  "display_name": "Bitbucket",
  "version": "10.2.8",
  "compatible": true
}
```

`compatible` is true when the remote version starts with `10.2.`.

### GET /api/bitbucket/projects

Paged Bitbucket project discovery, flattened into one list.

### GET /api/bitbucket/projects/{projectKey}/repos

Repositories in a project, including the HTTP clone URL when Bitbucket returns one.

| Status | Meaning |
| --- | --- |
| 200 | Success |
| 404 | Project or resource missing |
| 502 | Auth failure or Bitbucket unreachable |
| 503 | `BITBUCKET_BASE_URL` or `BITBUCKET_TOKEN` is not set |

## GET /

Service metadata for operators.

```json
{
  "name": "Bitbucket Agent",
  "version": "0.1.0",
  "docs": "/docs",
  "health": "/api/v1/health",
  "bitbucket_health": "/api/bitbucket/health"
}
```
