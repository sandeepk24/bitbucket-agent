# Bitbucket Data Center 10.2 connectivity

This service talks to **Bitbucket Data Center 10.2.x** (validated against 10.2.8). It does not call Bitbucket Cloud (`api.bitbucket.org`).

## Official sources

- [HTTP access tokens | Bitbucket Data Center 10.2](https://confluence.atlassian.com/bitbucketserver102/http-access-tokens-1791787433.html)
- [Bitbucket Data Center REST API — projects (v1002)](https://developer.atlassian.com/server/bitbucket/rest/v1002/api-group-project/)
- [Bitbucket Data Center REST API — pull requests (v1002)](https://developer.atlassian.com/server/bitbucket/rest/v1002/api-group-pull-requests/)
- [REST API paging and examples](https://developer.atlassian.com/server/bitbucket/how-tos/command-line-rest/)

## Authentication

Bitbucket 10.2 documents **HTTP access tokens** (personal / user tokens, plus project and repository tokens).

| Token type | REST header |
| --- | --- |
| User HTTP access token | `Authorization: Basic base64(username:token)` when `BITBUCKET_USERNAME` is set |
| User, project, or repository token | `Authorization: Bearer <token>` when `BITBUCKET_USERNAME` is empty |

Project and repository tokens must not be sent as Basic auth with a real username. Official docs require Bearer, or Basic with username `x-token-auth`.

The client never logs `Authorization` headers or token values.

## Endpoints used

`BITBUCKET_BASE_URL` is the instance root, for example `https://bitbucket.example.com`. The client appends `/rest/api/latest`, which 10.2 documents as the current REST alias for `/rest/api/1.0`.

| Purpose | Method | Path | 10.2.x |
| --- | --- | --- | --- |
| Version / connectivity | GET | `/rest/api/latest/application-properties` | Compatible |
| List projects | GET | `/rest/api/latest/projects?start=&limit=` | Compatible |
| List repos in a project | GET | `/rest/api/latest/projects/{projectKey}/repos?start=&limit=` | Compatible |
| List pull requests | GET | `/rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests?state=` | Compatible |
| Get a pull request | GET | `/rest/api/latest/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{pullRequestId}` | Compatible |
| PR commits | GET | `.../pull-requests/{pullRequestId}/commits` | Compatible |
| PR file changes | GET | `.../pull-requests/{pullRequestId}/changes` | Compatible |

Paging uses the documented page envelope: `values`, `isLastPage`, `nextPageStart`.

Personal projects use a `~` key prefix (`~jsmith`), which the client allows.

## Agent APIs

| Agent route | Bitbucket call |
| --- | --- |
| `GET /api/bitbucket/health` | `application-properties` |
| `GET /api/bitbucket/projects` | `projects` (all pages) |
| `GET /api/bitbucket/projects/{projectKey}/repos` | `projects/{projectKey}/repos` (all pages) |
| `GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests` | `pull-requests?state=` (all pages) |
| `GET /api/bitbucket/projects/{projectKey}/repos/{repositorySlug}/pull-requests/{id}` | PR + `/commits` + `/changes` |

`state` accepts `OPEN`, `MERGED`, `DECLINED`, or `ALL`. Reviewers and approval status (`APPROVED`, `UNAPPROVED`, `NEEDS_WORK`) are taken from the PR `reviewers` array. Source and destination branches are `fromRef.displayId` and `toRef.displayId`.

`compatible` on health is `true` when the remote version starts with `10.2.`.

## Not in this change

- AI review / PR Deep Analysis
- Bamboo
- Amazon Bedrock / Strands analysis
