from __future__ import annotations

import re

from projectguard_mcp.config import SQL_INJECTION_PATTERN
from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings


def review_security(project_type: str, files: dict[str, str], features: list[str] | None = None) -> dict:
    findings: list[Finding] = []
    features_text = " ".join(features or []).lower()
    all_text = "\n".join(files.values()).lower()
    pt = project_type.lower()

    if any(word in features_text + " " + pt for word in ["login", "signup", "auth", "dashboard", "admin"]):
        if "csrf" not in all_text and any(ext in " ".join(files).lower() for ext in ["html", "template", "flask"]):
            findings.append(Finding(
                code="CSRF_NOT_VISIBLE",
                severity="medium",
                message="Auth/admin/form project does not show CSRF protection.",
                recommendation="Add CSRF protection for state-changing form actions.",
            ))
        if "rate limit" not in all_text and "limiter" not in all_text:
            findings.append(Finding(
                code="RATE_LIMIT_NOT_VISIBLE",
                severity="medium",
                message="No visible rate limiting for login/API-sensitive flows.",
                recommendation="Add rate limits to login, signup, password reset, and public API endpoints.",
            ))

    if any(word in features_text + " " + pt for word in ["upload", "pdf", "image", "file"]):
        if not any(word in all_text for word in ["allowed_extensions", "content-type", "max_content_length", "file size"]):
            findings.append(Finding(
                code="UPLOAD_VALIDATION_MISSING",
                severity="high",
                message="File upload feature has no visible extension/type/size validation.",
                recommendation="Validate file type, size, storage path, and scan/parse safely.",
            ))

    for path, content in files.items():
        if re.search(SQL_INJECTION_PATTERN, content, flags=re.I):
            findings.append(Finding(
                code="POSSIBLE_SQL_INJECTION",
                severity="critical",
                message="Possible SQL query string concatenation detected.",
                recommendation="Use parameterized queries or ORM filters.",
                path=path,
            ))
        if "innerhtml" in content.lower() and "sanitize" not in content.lower():
            findings.append(Finding(
                code="POSSIBLE_XSS",
                severity="high",
                message="innerHTML is used without visible sanitization.",
                recommendation="Use textContent or sanitize trusted HTML.",
                path=path,
            ))

    if "payment" in features_text or "stripe" in all_text or "paypal" in all_text:
        if "webhook" not in all_text:
            findings.append(Finding(
                code="PAYMENT_WEBHOOK_MISSING",
                severity="high",
                message="Payment flow appears present but webhook handling is not visible.",
                recommendation="Use provider webhooks and store provider event IDs/idempotency.",
            ))
        if "idempot" not in all_text:
            findings.append(Finding(
                code="PAYMENT_IDEMPOTENCY_MISSING",
                severity="medium",
                message="No visible idempotency handling for payment events.",
                recommendation="Store provider event IDs and ignore duplicates.",
            ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="Security review passed basic checks." if score >= 85 else "Security review found launch-blocking or important issues.",
        metadata={"project_type": project_type, "feature_count": len(features or [])},
    ).to_dict()
