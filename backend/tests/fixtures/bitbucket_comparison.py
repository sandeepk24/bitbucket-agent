"""Bitbucket Data Center payloads for PR before/after comparison."""

from __future__ import annotations

from tests.fixtures.bitbucket_prs import page

HEAD_SHA = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
TARGET_SHA = "cafebabecafebabecafebabecafebabecafebabe"
MERGE_BASE_SHA = "0123456789abcdef0123456789abcdef01234567"
MID_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"

CLIENT_PATH = "backend/app/providers/bitbucket/client.py"
SECRETS_PATH = "backend/app/core/secrets.py"
DELETED_PATH = "backend/app/legacy/auth.py"
RENAME_SRC = "backend/app/util/names.py"
RENAME_DEST = "backend/app/util/display.py"
BINARY_PATH = "frontend/public/logo.png"

MERGE_BASE = {
    "id": MERGE_BASE_SHA,
    "displayId": MERGE_BASE_SHA[:7],
}

COMPARISON_COMMITS = [
    {
        "id": HEAD_SHA,
        "displayId": HEAD_SHA[:7],
        "author": {"name": "Tom Rivera", "emailAddress": "tom@example.com"},
        "authorTimestamp": 1711987200000,
        "message": "Rename display helpers and drop legacy auth",
        "parents": [{"id": MID_SHA, "displayId": MID_SHA[:7]}],
    },
    {
        "id": MID_SHA,
        "displayId": MID_SHA[:7],
        "author": {"name": "Tom Rivera", "emailAddress": "tom@example.com"},
        "authorTimestamp": 1711900800000,
        "message": "Redact Authorization headers in Bitbucket logs",
        "parents": [{"id": MERGE_BASE_SHA, "displayId": MERGE_BASE_SHA[:7]}],
    },
]

COMPARISON_CHANGES = [
    {
        "type": "MODIFY",
        "nodeType": "FILE",
        "path": {"toString": CLIENT_PATH, "name": "client.py"},
    },
    {
        "type": "ADD",
        "nodeType": "FILE",
        "path": {"toString": SECRETS_PATH, "name": "secrets.py"},
        "srcPath": None,
    },
    {
        "type": "DELETE",
        "nodeType": "FILE",
        "path": {"toString": DELETED_PATH, "name": "auth.py"},
    },
    {
        "type": "MOVE",
        "nodeType": "FILE",
        "path": {"toString": RENAME_DEST, "name": "display.py"},
        "srcPath": {"toString": RENAME_SRC, "name": "names.py"},
    },
    {
        "type": "MODIFY",
        "nodeType": "BINARY",
        "path": {"toString": BINARY_PATH, "name": "logo.png"},
    },
]


def _hunk(*, source_line: int, dest_line: int, removed: list[str], added: list[str]) -> dict:
    segments = []
    if removed:
        segments.append(
            {
                "type": "REMOVED",
                "lines": [
                    {"source": source_line + index, "destination": dest_line, "line": text}
                    for index, text in enumerate(removed)
                ],
            }
        )
    if added:
        segments.append(
            {
                "type": "ADDED",
                "lines": [
                    {"source": source_line, "destination": dest_line + index, "line": text}
                    for index, text in enumerate(added)
                ],
            }
        )
    return {
        "sourceLine": source_line,
        "sourceSpan": len(removed) or 1,
        "destinationLine": dest_line,
        "destinationSpan": len(added) or 1,
        "segments": segments,
    }


PR_DIFF = {
    "fromHash": MERGE_BASE_SHA,
    "toHash": HEAD_SHA,
    "contextLines": 10,
    "truncated": False,
    "diffs": [
        {
            "source": {"toString": CLIENT_PATH},
            "destination": {"toString": CLIENT_PATH},
            "hunks": [
                _hunk(
                    source_line=12,
                    dest_line=12,
                    removed=["TOKEN = os.environ['BITBUCKET_TOKEN']"],
                    added=["token = settings.bitbucket_token"],
                )
            ],
            "truncated": False,
        },
        {
            "source": None,
            "destination": {"toString": SECRETS_PATH},
            "hunks": [
                _hunk(source_line=1, dest_line=1, removed=[], added=["def redact_secrets(text, token):"])
            ],
        },
        {
            "source": {"toString": DELETED_PATH},
            "destination": None,
            "hunks": [
                _hunk(source_line=4, dest_line=1, removed=["print(token)"], added=[]),
            ],
        },
        {
            "source": {"toString": RENAME_SRC},
            "destination": {"toString": RENAME_DEST},
            "hunks": [
                _hunk(
                    source_line=1,
                    dest_line=1,
                    removed=["def names():"],
                    added=["def display_name():"],
                )
            ],
        },
        {
            "source": {"toString": BINARY_PATH},
            "destination": {"toString": BINARY_PATH},
            "hunks": None,
            "binary": True,
        },
    ],
}

TRUNCATED_DIFF = {
    **PR_DIFF,
    "truncated": True,
    "diffs": [
        {
            **PR_DIFF["diffs"][0],
            "truncated": True,
        }
    ],
}

BEFORE_CLIENT = "class BitbucketClient:\n    TOKEN = os.environ['BITBUCKET_TOKEN']\n"
AFTER_CLIENT = "class BitbucketClient:\n    token = settings.bitbucket_token\n"
AFTER_SECRETS = "def redact_secrets(text, token):\n    return text.replace(token, '***')\n"
BEFORE_DELETED = "def login():\n    print(token)\n"
BEFORE_RENAME = "def names():\n    return []\n"
AFTER_RENAME = "def display_name():\n    return []\n"

RAW_FILES = {
    (CLIENT_PATH, MERGE_BASE_SHA): BEFORE_CLIENT,
    (CLIENT_PATH, HEAD_SHA): AFTER_CLIENT,
    (SECRETS_PATH, HEAD_SHA): AFTER_SECRETS,
    (DELETED_PATH, MERGE_BASE_SHA): BEFORE_DELETED,
    (RENAME_SRC, MERGE_BASE_SHA): BEFORE_RENAME,
    (RENAME_DEST, HEAD_SHA): AFTER_RENAME,
}


def comparison_page(values):
    return page(values)
