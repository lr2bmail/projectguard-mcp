from __future__ import annotations

import re

from projectguard_mcp.config import ANTI_SLOP_PATTERNS, MIN_TEXT_LENGTH
from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings


def review_project_text(content: str) -> dict:
    findings: list[Finding] = []
    text = content or ""

    for code, (pattern, severity) in ANTI_SLOP_PATTERNS.items():
        matches = re.findall(pattern, text, flags=re.I)
        if matches:
            findings.append(Finding(
                code=code,
                severity=severity,
                message=f"Detected possible slop/generic content: {code}.",
                recommendation="Replace vague or fake content with specific, accurate, product-specific copy.",
            ))

    if len(text.strip()) < MIN_TEXT_LENGTH:
        findings.append(Finding(
            code="TEXT_TOO_SHORT",
            severity="low",
            message="Text is too short to evaluate properly.",
            recommendation="Provide page copy, README, plan, or final response text for review.",
        ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="Text passed anti-slop checks." if score >= 85 else "Text contains generic, fake, or placeholder patterns.",
        metadata={"content_length": len(text)},
    ).to_dict()
