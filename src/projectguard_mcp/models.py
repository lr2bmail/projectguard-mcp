from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Finding:
    code: str
    severity: str
    message: str
    recommendation: str = ""
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.recommendation:
            data["recommendation"] = self.recommendation
        if self.path:
            data["path"] = self.path
        return data


@dataclass(slots=True)
class ReviewResult:
    approved: bool
    score: int
    findings: list[Finding] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "score": max(0, min(100, int(self.score))),
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
            "metadata": self.metadata,
        }


SEVERITY_WEIGHT = {
    "info": 0,
    "low": 4,
    "medium": 8,
    "high": 15,
    "critical": 25,
}


def score_from_findings(findings: list[Finding], base: int = 100) -> int:
    penalty = sum(SEVERITY_WEIGHT.get(f.severity, 5) for f in findings)
    return max(0, min(100, base - penalty))


def approval_from_score(score: int, minimum: int = 85) -> bool:
    return score >= minimum
