"""Deterministic static review of PR file text. Findings are evidence-backed."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.secrets import redact_secrets
from app.schemas.analysis import AnalysisFinding, FindingEvidence

_SECRET_ASSIGN = re.compile(
    r"""(?i)\b(api[_-]?key|auth(?:orization)?|passwd|password|secret|token)\b\s*[:=]\s*['\"][^'\"]{4,}['\"]"""
)
_AWS_KEY = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")
_EVAL = re.compile(r"(?i)\beval\s*\(")
_EXEC = re.compile(r"(?i)\bexec\s*\(")
_PICKLE = re.compile(r"(?i)\bpickle\.loads\s*\(")
_SHELL = re.compile(r"(?i)\bshell\s*=\s*True")
_BARE_EXCEPT = re.compile(r"(?i)^\s*except\s*:")
_PRINT_SECRET = re.compile(r"(?i)\bprint\s*\(.*\b(token|password|secret|authorization)\b")
_SQL_CONCAT = re.compile(r"""(?i)\b(SELECT|INSERT|UPDATE|DELETE)\b.+(?:\+|f['\"].*\{)""")
_MD5 = re.compile(r"(?i)\bmd5\s*\(")
_SECURITY_PATH = re.compile(r"(?i)(auth|security|login|permission|iam|oauth|jwt|session)")
_CODE_FILE = re.compile(r"\.(py|ts|tsx|js|jsx|java|go|rb|rs|php)$")
_TEST_FILE = re.compile(r"(?i)(^|/)(tests?|spec)(/|_|\.)|test_|\.test\.|\.spec\.")


@dataclass(frozen=True, slots=True)
class _Rule:
    slug: str
    pattern: re.Pattern[str]
    title: str
    severity: str
    risk: str
    recommended_fix: str
    production_impact: str
    after_only: bool = True


_RULES = (
    _Rule(
        "hardcoded-secret",
        _SECRET_ASSIGN,
        "Hardcoded credential in source",
        "critical",
        "A secret appears as a literal in the new revision. Anyone with repo access can use it.",
        "Move the value to a secret store or environment variable and rotate the exposed credential.",
        "A leaked credential can be used against production services immediately.",
    ),
    _Rule(
        "aws-key",
        _AWS_KEY,
        "AWS access key material in source",
        "critical",
        "An AKIA access key is present in the diff.",
        "Remove the key, rotate it in IAM, and load credentials from the instance role or a secret manager.",
        "Cloud account takeover if the key is valid.",
    ),
    _Rule(
        "private-key",
        _PRIVATE_KEY,
        "Private key committed in the change",
        "critical",
        "PEM private key armor is present in the file.",
        "Delete the key from git history if needed, rotate it, and keep keys out of the repository.",
        "TLS, SSH, or signing identity can be impersonated.",
    ),
    _Rule(
        "eval",
        _EVAL,
        "Dynamic eval of untrusted input",
        "high",
        "eval() executes a string as code. If any caller-controlled data reaches it, this is remote code execution.",
        "Replace eval with an allow-listed parser or explicit branching.",
        "Runtime code execution in the serving process.",
        after_only=True,
    ),
    _Rule(
        "exec",
        _EXEC,
        "Dynamic exec of untrusted input",
        "high",
        "exec() runs arbitrary Python from a string.",
        "Remove exec and use explicit functions or a constrained DSL.",
        "Runtime code execution in the serving process.",
    ),
    _Rule(
        "pickle",
        _PICKLE,
        "Unsafe pickle deserialization",
        "high",
        "pickle.loads can execute attacker-controlled objects.",
        "Use JSON or a signed serializer. Never unpickle untrusted data.",
        "Remote code execution if pickled payloads come from users or queues.",
    ),
    _Rule(
        "shell-true",
        _SHELL,
        "Subprocess invoked with shell=True",
        "high",
        "shell=True concatenates a command string that is easy to inject into.",
        "Pass a argument list and keep shell=False.",
        "Host command injection if any argument is user-controlled.",
    ),
    _Rule(
        "print-secret",
        _PRINT_SECRET,
        "Secret value written to logs or stdout",
        "high",
        "Token or password material is printed. Logs are often shipped to shared aggregators.",
        "Redact secrets before logging. Print a presence flag, not the value.",
        "Credentials in logs can be reused against production APIs.",
        after_only=False,
    ),
    _Rule(
        "sql-concat",
        _SQL_CONCAT,
        "SQL assembled by string concatenation",
        "medium",
        "Query text is built with + or an f-string, which often leads to injection.",
        "Use bound parameters on the database driver.",
        "Data disclosure or mutation if the query runs in production.",
    ),
    _Rule(
        "bare-except",
        _BARE_EXCEPT,
        "Bare except swallows errors",
        "medium",
        "except: hides failures, including security-relevant ones.",
        "Catch a specific exception type and log or re-raise.",
        "Outages and bypassed controls can go unnoticed.",
        after_only=False,
    ),
    _Rule(
        "md5",
        _MD5,
        "Weak MD5 digest",
        "low",
        "MD5 is not suitable for integrity or password hashing.",
        "Use SHA-256 for integrity or a password KDF such as Argon2.",
        "Integrity checks can be forged more easily than with modern hashes.",
    ),
)


def component_for(path: str) -> str:
    parts = [part for part in path.strip("/").split("/") if part]
    if len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0] if parts else "repository"


def scan_file(
    *,
    path: str,
    src_path: str | None,
    change_type: str,
    before: str | None,
    after: str | None,
    base_sha: str,
    head_sha: str,
    token: str = "",
) -> list[AnalysisFinding]:
    findings: list[AnalysisFinding] = []
    if change_type != "DELETE" and after:
        findings.extend(
            _scan_text(
                path=path,
                src_path=src_path,
                change_type=change_type,
                content=after,
                revision=head_sha,
                side="after",
                token=token,
            )
        )
    if before and change_type == "DELETE":
        findings.extend(
            _scan_text(
                path=path,
                src_path=src_path,
                change_type=change_type,
                content=before,
                revision=base_sha,
                side="before",
                token=token,
            )
        )
    findings.extend(
        heuristic_risks(
            path=path,
            src_path=src_path,
            change_type=change_type,
            before=before,
            after=after,
            base_sha=base_sha,
            head_sha=head_sha,
        )
    )
    return findings


def heuristic_risks(
    *,
    path: str,
    src_path: str | None,
    change_type: str,
    before: str | None,
    after: str | None,
    base_sha: str,
    head_sha: str,
) -> list[AnalysisFinding]:
    findings: list[AnalysisFinding] = []
    component = component_for(path)
    if change_type == "DELETE" and _SECURITY_PATH.search(path):
            findings.append(
                _finding(
                    id=f"heuristic-delete-{path}",
                title="Security-sensitive path removed",
                severity="high",
                kind="hypothetical",
                source="heuristic",
                path=path,
                src_path=src_path,
                change_type=change_type,
                component=component,
                before_lines=_line_span(before),
                after_lines=[],
                evidence=[
                    FindingEvidence(
                        path=path,
                        revision=base_sha,
                        quote="File deleted in this pull request.",
                    )
                ],
                risk="Removing auth or session code can silently drop checks if callers are not updated.",
                recommended_fix="Confirm every caller still authenticates, and add a regression test before merge.",
                production_impact="Unauthenticated access or broken login in production if this module was still wired.",
            )
        )
    if change_type == "MOVE" and src_path:
        findings.append(
            _finding(
                id=f"heuristic-move-{path}",
                title="Renamed module may break imports",
                severity="medium",
                kind="hypothetical",
                source="heuristic",
                path=path,
                src_path=src_path,
                change_type=change_type,
                component=component,
                before_lines=[],
                after_lines=_line_span(after),
                evidence=[
                    FindingEvidence(
                        path=path,
                        revision=head_sha,
                        quote=f"{src_path} → {path}",
                    )
                ],
                risk="Runtime import errors if other services still load the old path.",
                recommended_fix="Update remaining imports and re-run the unit and integration suites.",
                production_impact="Process crash or missing feature after deploy if an import still points at the old module.",
            )
        )
    if change_type == "ADD" and _CODE_FILE.search(path) and not _TEST_FILE.search(path) and after:
        findings.append(
            _finding(
                id=f"heuristic-notest-{path}",
                title="New code path has no accompanying test file",
                severity="low",
                kind="hypothetical",
                source="heuristic",
                path=path,
                src_path=src_path,
                change_type=change_type,
                component=component,
                before_lines=[],
                after_lines=_line_span(after)[:3],
                evidence=[
                    FindingEvidence(path=path, revision=head_sha, quote="Added without a sibling test file in this PR.")
                ],
                risk="Regressions in this module may only show up after deploy.",
                recommended_fix="Add tests that cover the new behavior, including failure cases.",
                production_impact="Latent defects are more likely to reach production.",
            )
        )
    return findings


def _scan_text(
    *,
    path: str,
    src_path: str | None,
    change_type: str,
    content: str,
    revision: str,
    side: str,
    token: str,
) -> list[AnalysisFinding]:
    findings: list[AnalysisFinding] = []
    for index, line in enumerate(content.splitlines(), start=1):
        for rule in _RULES:
            if side == "before" and rule.after_only:
                continue
            if not rule.pattern.search(line):
                continue
            line_field = "after_lines" if side == "after" else "before_lines"
            findings.append(
                _finding(
                    id=f"static-{rule.slug}-{path}-{index}",
                    title=rule.title,
                    severity=rule.severity,  # type: ignore[arg-type]
                    kind="confirmed",
                    source="static",
                    path=path,
                    src_path=src_path,
                    change_type=change_type,
                    component=component_for(path),
                    before_lines=[index] if line_field == "before_lines" else [],
                    after_lines=[index] if line_field == "after_lines" else [],
                    evidence=[
                        FindingEvidence(
                            path=path,
                            revision=revision,
                            line=index,
                            quote=redact_secrets(line.strip()[:240], token),
                        )
                    ],
                    risk=rule.risk,
                    recommended_fix=rule.recommended_fix,
                    production_impact=rule.production_impact,
                )
            )
    return findings


def _finding(**kwargs: object) -> AnalysisFinding:
    return AnalysisFinding.model_validate(kwargs)


def _line_span(content: str | None) -> list[int]:
    if not content:
        return []
    count = min(3, content.count("\n") + 1)
    return list(range(1, count + 1))
