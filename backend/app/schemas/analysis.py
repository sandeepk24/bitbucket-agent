"""PR deep analysis models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.comparison import ComparisonFileSummary

Severity = Literal["critical", "high", "medium", "low", "info"]
FindingKind = Literal["confirmed", "hypothetical"]
FindingSource = Literal["static", "model", "heuristic"]
StageStatus = Literal["pending", "running", "done", "error", "skipped"]
AnalysisStatus = Literal["complete", "partial"]


class FindingEvidence(BaseModel):
    path: str
    revision: str
    line: int | None = None
    quote: str | None = None


class AnalysisFinding(BaseModel):
    id: str
    title: str
    severity: Severity
    kind: FindingKind
    source: FindingSource
    path: str
    src_path: str | None = None
    change_type: str = "MODIFY"
    component: str
    before_lines: list[int] = Field(default_factory=list)
    after_lines: list[int] = Field(default_factory=list)
    evidence: list[FindingEvidence] = Field(default_factory=list)
    risk: str
    recommended_fix: str
    production_impact: str


class AnalysisStage(BaseModel):
    id: str
    label: str
    status: StageStatus
    detail: str | None = None


class UnsupportedFile(BaseModel):
    path: str
    reason: str
    detail: str


class AffectedComponent(BaseModel):
    name: str
    file_count: int
    finding_count: int
    paths: list[str]


class ModelStatus(BaseModel):
    provider: str
    available: bool
    used: bool = False
    error: str | None = None


class PullRequestAnalysisResponse(BaseModel):
    status: AnalysisStatus
    project_key: str
    repo_slug: str
    pull_request_id: int
    title: str
    source_branch: str
    destination_branch: str
    base_sha: str
    head_sha: str
    commit_count: int
    summary: str
    production_impact: str
    risk_summary: str
    progress: list[AnalysisStage]
    model: ModelStatus
    components: list[AffectedComponent]
    files: list[ComparisonFileSummary]
    unsupported_files: list[UnsupportedFile]
    findings: list[AnalysisFinding]
