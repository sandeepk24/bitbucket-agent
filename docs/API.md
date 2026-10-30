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

### GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests

Query: `state=OPEN|MERGED|DECLINED|ALL` (default `OPEN`).

Each item includes author, reviewers, approval counts, and source/destination branches.

### GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}

Bundles the PR, its commits, and changed files. Reviewer `status` is `APPROVED`, `UNAPPROVED`, or `NEEDS_WORK`.

### GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/comparison

Resolves immutable base and head SHAs (merge-base and `fromRef.latestCommit`), then lists changed files with addition/deletion counts and changed line numbers. Branch names are never used as revisions.

### GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/comparison/file

Query: `path`, `base`, `head`, optional `srcPath`, optional `changeType`.

Returns file content at the supplied commit SHAs. `base` and `head` must be hex SHAs (`7–40` chars). Binary, oversized, missing, and truncated files are flagged instead of being rendered as text.

### GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}/analysis

Deep analysis of a pull request at locked base/head SHAs.

- `summary`, `risk_summary`, and `production_impact` describe the overall change
- `findings` are grouped by `severity` and tagged `kind=confirmed` (static evidence in the diff) or `kind=hypothetical` (runtime/production risk)
- `progress` lists completed stages; `model.error` is set when inference is unavailable
- `unsupported_files` covers binary, oversized, truncated, and capped paths
- Evidence quotes are redacted for the Bitbucket token

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
