from __future__ import annotations

import re

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings

SLOP_PATTERNS = {
    "LOREM_IPSUM": r"lorem ipsum|dolor sit amet",
    "PLACEHOLDER_TEXT": r"placeholder|coming soon|under construction|todo\b|fixme\b|dummy data",
    "FAKE_SOCIAL_PROOF": r"trusted by thousands|millions of users|world.?class|industry.?leading|#1\b",
    "GENERIC_AI_COPY": r"unlock your potential|seamless experience|revolutionize|transform your workflow|cutting-edge solution",
    "FAKE_INTEGRATION": r"integrates with (stripe|paypal|openai|slack|github|google)" ,
}


def review_project_text(content: str) -> dict:
    findings: list[Finding] = []
    text = content or ""

    for code, pattern in SLOP_PATTERNS.items():
        matches = re.findall(pattern, text, flags=re.I)
        if matches:
            findings.append(Finding(
                code=code,
                severity="medium" if code != "FAKE_INTEGRATION" else "high",
                message=f"Detected possible slop/generic content: {code}.",
                recommendation="Replace vague or fake content with specific, accurate, product-specific copy.",
            ))

    if len(text.strip()) < 80:
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
