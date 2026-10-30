"""PR deep analysis: SHA-locked diffs, static review, optional model enrichment."""

from __future__ import annotations

import json
import re
from typing import Any

from app.core.logging import get_logger
from app.core.secrets import redact_secrets
from app.providers.ai.base import AINotImplementedError, AIProvider
from app.providers.bitbucket.client import BitbucketClient
from app.schemas.analysis import (
    AffectedComponent,
    AnalysisFinding,
    AnalysisStage,
    FindingEvidence,
    ModelStatus,
    PullRequestAnalysisResponse,
    UnsupportedFile,
)
from app.schemas.comparison import ComparisonFileSummary
from app.schemas.pull_requests import pull_request_from_rest
from app.services.comparison import build_comparison, build_file_comparison
from app.services.static_review import component_for, scan_file

logger = get_logger(__name__)

_MAX_FILES = 25
_PROMPT_CHARS = 12_000
_SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

_SYSTEM = (
    "You review pull request diffs for production risk. Reply with JSON only: "
    '{"summary": str, "production_impact": str, "findings": ['
    '{"title": str, "severity": "critical|high|medium|low|info", '
    '"kind": "confirmed|hypothetical", "path": str, "after_lines": [int], '
    '"evidence": [str], "risk": str, "recommended_fix": str, "production_impact": str}'
    "]}. "
    "kind=confirmed only when the issue is visible in the supplied text. "
    "kind=hypothetical for runtime or production risks that are not proven by the diff."
)


async def analyze_pull_request(
    client: BitbucketClient,
    provider: AIProvider,
    project_key: str,
    repo_slug: str,
    pull_request_id: int,
) -> PullRequestAnalysisResponse:
    progress: list[AnalysisStage] = []
    raw_pr = await client.get_pull_request(project_key, repo_slug, pull_request_id)
    pr = pull_request_from_rest(raw_pr)
    progress.append(_stage("resolve-pr", "Load pull request metadata", "done", pr.title))

    comparison = await build_comparison(client, project_key, repo_slug, pull_request_id)
    progress.append(
        _stage(
            "resolve-revisions",
            "Lock base and head SHAs",
            "done",
            f"{comparison.base.sha[:12]} → {comparison.head.sha[:12]}",
        )
    )
    progress.append(
        _stage("load-changes", "List changed files", "done", f"{len(comparison.files)} paths")
    )

    unsupported: list[UnsupportedFile] = []
    findings: list[AnalysisFinding] = []
    analyzed = 0
    for file in comparison.files[:_MAX_FILES]:
        if file.binary:
            unsupported.append(
                UnsupportedFile(
                    path=file.path,
                    reason="binary",
                    detail="Binary files are not sent to static review or the model.",
                )
            )
            continue
        snapshot = await build_file_comparison(
            client,
            project_key,
            repo_slug,
            pull_request_id,
            path=file.path,
            src_path=file.src_path,
            change_type=file.change_type,
            base_sha=comparison.base.sha,
            head_sha=comparison.head.sha,
        )
        if snapshot.before.too_large or snapshot.after.too_large:
            unsupported.append(
                UnsupportedFile(
                    path=file.path,
                    reason="too_large",
                    detail="File exceeded BITBUCKET_MAX_FILE_BYTES and was skipped.",
                )
            )
            continue
        if snapshot.before.binary or snapshot.after.binary:
            unsupported.append(
                UnsupportedFile(
                    path=file.path,
                    reason="binary",
                    detail="Bitbucket returned a binary payload for this path.",
                )
            )
            continue
        if snapshot.truncated_diff or snapshot.before.truncated or snapshot.after.truncated:
            unsupported.append(
                UnsupportedFile(
                    path=file.path,
                    reason="truncated",
                    detail="Bitbucket truncated this file or diff. Findings may be incomplete.",
                )
            )
        analyzed += 1
        findings.extend(
            scan_file(
                path=file.path,
                src_path=file.src_path,
                change_type=file.change_type,
                before=snapshot.before.content,
                after=snapshot.after.content,
                base_sha=comparison.base.sha,
                head_sha=comparison.head.sha,
                token=client.config.token,
            )
        )

    skipped = max(0, len(comparison.files) - _MAX_FILES)
    if skipped:
        unsupported.append(
            UnsupportedFile(
                path="(additional files)",
                reason="capped",
                detail=f"{skipped} extra files were not opened because the analysis cap is {_MAX_FILES}.",
            )
        )
    progress.append(
        _stage("static-review", "Run confirmed static analysis", "done", f"{analyzed} text files")
    )

    model_status, model_findings, model_summary, model_impact = await _run_model(
        provider,
        comparison.files,
        findings,
        token=client.config.token,
        head_sha=comparison.head.sha,
    )
    findings.extend(model_findings)
    if model_status.error:
        progress.append(
            _stage("model-inference", "AI model review", "error" if model_status.available else "skipped", model_status.error)
        )
    elif model_status.used:
        progress.append(_stage("model-inference", "AI model review", "done", provider.name))
    else:
        progress.append(_stage("model-inference", "AI model review", "skipped", "Provider is not configured"))

    findings = _dedupe(findings)
    findings.sort(key=lambda item: (_SEVERITY_RANK.get(item.severity, 9), item.path, item.title))
    components = _components(comparison.files, findings)
    summary = model_summary or _fallback_summary(pr.title, comparison.files, findings)
    production_impact = model_impact or _fallback_impact(findings)
    risk_summary = _risk_summary(findings)
    progress.append(_stage("assemble", "Assemble report", "done", f"{len(findings)} findings"))

    status = "partial" if model_status.error or unsupported else "complete"
    return PullRequestAnalysisResponse(
        status=status,
        project_key=project_key,
        repo_slug=repo_slug,
        pull_request_id=pull_request_id,
        title=pr.title,
        source_branch=pr.source_branch,
        destination_branch=pr.destination_branch,
        base_sha=comparison.base.sha,
        head_sha=comparison.head.sha,
        commit_count=comparison.commit_count,
        summary=summary,
        production_impact=production_impact,
        risk_summary=risk_summary,
        progress=progress,
        model=model_status,
        components=components,
        files=comparison.files,
        unsupported_files=unsupported,
        findings=findings,
    )


async def _run_model(
    provider: AIProvider,
    files: list[ComparisonFileSummary],
    static_findings: list[AnalysisFinding],
    *,
    token: str,
    head_sha: str,
) -> tuple[ModelStatus, list[AnalysisFinding], str | None, str | None]:
    available = await provider.is_available()
    if not available:
        return (
            ModelStatus(provider=provider.name, available=False, used=False, error="AI provider is not configured"),
            [],
            None,
            None,
        )
    prompt = _model_prompt(files, static_findings)
    try:
        raw = await provider.generate(prompt, system=_SYSTEM)
    except AINotImplementedError as exc:
        logger.info("AI generate is not wired: %s", type(exc).__name__)
        return (
            ModelStatus(provider=provider.name, available=True, used=False, error=str(exc)),
            [],
            None,
            None,
        )
    except Exception as exc:
        logger.warning("AI generate failed: %s", type(exc).__name__)
        return (
            ModelStatus(
                provider=provider.name,
                available=True,
                used=False,
                error="The model call failed. Static findings are still available.",
            ),
            [],
            None,
            None,
        )
    try:
        payload = _parse_model_json(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return (
            ModelStatus(
                provider=provider.name,
                available=True,
                used=False,
                error="The model returned JSON that could not be parsed.",
            ),
            [],
            None,
            None,
        )
    findings = _findings_from_model(payload, files, token=token, head_sha=head_sha)
    summary = payload.get("summary") if isinstance(payload.get("summary"), str) else None
    impact = payload.get("production_impact") if isinstance(payload.get("production_impact"), str) else None
    return (
        ModelStatus(provider=provider.name, available=True, used=True, error=None),
        findings,
        summary,
        impact,
    )


def _model_prompt(files: list[ComparisonFileSummary], static_findings: list[AnalysisFinding]) -> str:
    file_lines = [
        f"- {item.change_type} {item.path} (+{item.additions}/-{item.deletions})"
        for item in files[:_MAX_FILES]
    ]
    finding_lines = [f"- [{item.severity}] {item.title} in {item.path}" for item in static_findings[:20]]
    text = (
        "Changed files:\n"
        + "\n".join(file_lines)
        + "\n\nConfirmed static findings:\n"
        + ("\n".join(finding_lines) if finding_lines else "(none)")
    )
    return text[:_PROMPT_CHARS]


def _parse_model_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("model payload was not an object")
    return payload


def _findings_from_model(
    payload: dict[str, Any],
    files: list[ComparisonFileSummary],
    *,
    token: str,
    head_sha: str,
) -> list[AnalysisFinding]:
    known = {item.path: item for item in files}
    findings: list[AnalysisFinding] = []
    raw_items = payload.get("findings")
    if not isinstance(raw_items, list):
        return findings
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict) or not item.get("title"):
            continue
        path = str(item.get("path") or next(iter(known), "unknown"))
        match = known.get(path)
        kind = item.get("kind") if item.get("kind") in {"confirmed", "hypothetical"} else "hypothetical"
        severity = item.get("severity") if item.get("severity") in _SEVERITY_RANK else "medium"
        after_lines = [line for line in item.get("after_lines") or [] if isinstance(line, int)]
        evidence_raw = item.get("evidence") if isinstance(item.get("evidence"), list) else []
        evidence = [
            FindingEvidence(
                path=path,
                revision=head_sha,
                line=after_lines[0] if after_lines else None,
                quote=redact_secrets(str(quote)[:240], token),
            )
            for quote in evidence_raw
            if quote
        ]
        findings.append(
            AnalysisFinding(
                id=f"model-{index}-{path}",
                title=str(item.get("title")),
                severity=severity,
                kind=kind,
                source="model",
                path=path,
                src_path=match.src_path if match else None,
                change_type=match.change_type if match else "MODIFY",
                component=component_for(path),
                before_lines=[],
                after_lines=after_lines,
                evidence=evidence,
                risk=str(item.get("risk") or "Model-reported risk. Treat as hypothetical until verified in the diff."),
                recommended_fix=str(item.get("recommended_fix") or "Review the referenced file before merge."),
                production_impact=str(item.get("production_impact") or "Impact is not proven by static evidence."),
            )
        )
    return findings


def _components(
    files: list[ComparisonFileSummary], findings: list[AnalysisFinding]
) -> list[AffectedComponent]:
    grouped: dict[str, list[str]] = {}
    for file in files:
        grouped.setdefault(component_for(file.path), []).append(file.path)
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.component] = counts.get(finding.component, 0) + 1
    return [
        AffectedComponent(
            name=name,
            file_count=len(paths),
            finding_count=counts.get(name, 0),
            paths=paths,
        )
        for name, paths in sorted(grouped.items())
    ]


def _dedupe(findings: list[AnalysisFinding]) -> list[AnalysisFinding]:
    seen: set[tuple[str, str, str, int | None]] = set()
    unique: list[AnalysisFinding] = []
    for item in findings:
        line = (item.after_lines or item.before_lines or [None])[0]
        key = (item.title, item.path, item.source, line)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _fallback_summary(title: str, files: list[ComparisonFileSummary], findings: list[AnalysisFinding]) -> str:
    confirmed = sum(1 for item in findings if item.kind == "confirmed")
    hypothetical = sum(1 for item in findings if item.kind == "hypothetical")
    return (
        f'"{title}" changes {len(files)} file(s) across {len({component_for(item.path) for item in files}) or 1} component(s). '
        f"Static review found {confirmed} confirmed issue(s) and {hypothetical} hypothetical runtime risk(s)."
    )


def _fallback_impact(findings: list[AnalysisFinding]) -> str:
    if any(item.severity in {"critical", "high"} and item.kind == "confirmed" for item in findings):
        return "High-severity confirmed findings should be treated as merge blockers until remediated."
    if findings:
        return "No confirmed critical issue was proven in the text. Review hypothetical runtime risks before deploy."
    return "No confirmed static issues were found in the text files that could be opened."


def _risk_summary(findings: list[AnalysisFinding]) -> str:
    if not findings:
        return "No findings. Confirm binary and skipped files separately."
    top = findings[0]
    return f"Highest finding: {top.severity} — {top.title} ({top.kind}, {top.source})."


def _stage(ident: str, label: str, status: str, detail: str | None = None) -> AnalysisStage:
    return AnalysisStage(id=ident, label=label, status=status, detail=detail)  # type: ignore[arg-type]
