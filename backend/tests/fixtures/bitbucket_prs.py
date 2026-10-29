"""Realistic Bitbucket Data Center 10.2 REST payloads for pull requests."""

from __future__ import annotations

OPEN_PR = {
    "id": 42,
    "version": 3,
    "title": "Harden token handling in the payments API",
    "description": "Stop logging Authorization headers and add retries around Bitbucket REST.",
    "state": "OPEN",
    "open": True,
    "closed": False,
    "createdDate": 1711900800000,
    "updatedDate": 1711987200000,
    "fromRef": {
        "id": "refs/heads/feature/token-redaction",
        "displayId": "feature/token-redaction",
        "latestCommit": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "repository": {"slug": "payments", "project": {"key": "DEV"}},
    },
    "toRef": {
        "id": "refs/heads/main",
        "displayId": "main",
        "latestCommit": "cafebabecafebabecafebabecafebabecafebabe",
        "repository": {"slug": "payments", "project": {"key": "DEV"}},
    },
    "author": {
        "user": {
            "name": "tom",
            "emailAddress": "tom@example.com",
            "id": 115026,
            "displayName": "Tom Rivera",
            "active": True,
            "slug": "tom",
            "type": "NORMAL",
        },
        "role": "AUTHOR",
        "approved": False,
        "status": "UNAPPROVED",
    },
    "reviewers": [
        {
            "user": {
                "name": "jcitizen",
                "emailAddress": "jane@example.com",
                "id": 101,
                "displayName": "Jane Citizen",
                "active": True,
                "slug": "jcitizen",
                "type": "NORMAL",
            },
            "role": "REVIEWER",
            "approved": True,
            "status": "APPROVED",
        },
        {
            "user": {
                "name": "alex",
                "emailAddress": "alex@example.com",
                "id": 202,
                "displayName": "Alex Ng",
                "active": True,
                "slug": "alex",
                "type": "NORMAL",
            },
            "role": "REVIEWER",
            "approved": False,
            "status": "NEEDS_WORK",
        },
    ],
    "participants": [],
    "links": {
        "self": [{"href": "https://bitbucket.example.com/projects/DEV/repos/payments/pull-requests/42"}]
    },
}

MERGED_PR = {
    **OPEN_PR,
    "id": 7,
    "title": "Bump httpx and pin timeouts",
    "state": "MERGED",
    "open": False,
    "closed": True,
    "reviewers": [
        {
            "user": {
                "name": "jcitizen",
                "emailAddress": "jane@example.com",
                "displayName": "Jane Citizen",
                "slug": "jcitizen",
            },
            "role": "REVIEWER",
            "approved": True,
            "status": "APPROVED",
        }
    ],
}

DECLINED_PR = {
    **OPEN_PR,
    "id": 9,
    "title": "Rewrite the cache in one commit",
    "state": "DECLINED",
    "open": False,
    "closed": True,
    "reviewers": [],
}

PR_COMMITS = [
    {
        "id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "displayId": "a1b2c3d",
        "author": {
            "name": "Tom Rivera",
            "emailAddress": "tom@example.com",
        },
        "authorTimestamp": 1711900800000,
        "message": "Redact Authorization headers in Bitbucket logs",
        "parents": [{"id": "cafebabecafebabecafebabecafebabecafebabe", "displayId": "cafebab"}],
    }
]

PR_CHANGES = [
    {
        "contentId": "content-1",
        "fromHash": "cafebabecafebabecafebabecafebabecafebabe",
        "toHash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "type": "MODIFY",
        "nodeType": "FILE",
        "path": {
            "components": ["backend", "app", "providers", "bitbucket", "client.py"],
            "parent": "backend/app/providers/bitbucket",
            "name": "client.py",
            "extension": "py",
            "toString": "backend/app/providers/bitbucket/client.py",
        },
        "executable": False,
    },
    {
        "contentId": "content-2",
        "type": "ADD",
        "nodeType": "FILE",
        "path": {
            "toString": "backend/app/core/secrets.py",
            "name": "secrets.py",
            "parent": "backend/app/core",
        },
        "srcPath": None,
        "executable": False,
    },
]


def page(values, *, start=0, is_last=True, next_start=None, limit=25):
    payload = {
        "size": len(values),
        "limit": limit,
        "isLastPage": is_last,
        "values": values,
        "start": start,
        "filter": None,
    }
    if next_start is not None:
        payload["nextPageStart"] = next_start
    return payload
