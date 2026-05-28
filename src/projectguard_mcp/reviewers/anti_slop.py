from __future__ import annotations

import re

from projectguard_mcp.config import (
    ADDITIONAL_SLOP_PATTERNS,
    ANTI_SLOP_PATTERNS,
    EMPTY_SECTION_MAX_HEADING_LEN,
    EMPTY_SECTION_MIN_WORDS,
    EXCLAMATION_SPAM_THRESHOLD,
    MIN_TEXT_LENGTH,
)
from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import count_words


def _check_empty_sections(text: str, findings: list[Finding]) -> None:
    sections = re.split(r"\n#{1,6}\s|\n(?=<h[1-6])", text)
    for section in sections:
        lines = section.strip().split("\n")
        if lines:
            heading = lines[0].strip()
            body = " ".join(lines[1:]).strip()
            word_count = count_words(body)
            if word_count < EMPTY_SECTION_MIN_WORDS and len(heading) > 0 and len(heading) < EMPTY_SECTION_MAX_HEADING_LEN:
                findings.append(Finding(
                    code="EMPTY_SECTION",
                    severity="medium",
                    message=f"Section '{heading[:60]}' has no meaningful content.",
                    recommendation="Add content to all sections or remove empty headings.",
                ))
                break


def _check_exclamation_spam(text: str, findings: list[Finding]) -> None:
    exclamation_count = text.count("!")
    word_count = count_words(text)
    if word_count > 20 and (exclamation_count / max(word_count, 1)) * 100 > EXCLAMATION_SPAM_THRESHOLD:
        findings.append(Finding(
            code="EXCLAMATION_SPAM",
            severity="low",
            message="Text has excessive exclamation marks.",
            recommendation="Use exclamation marks sparingly for professional tone.",
        ))


_PRIVACY_CLAIM_WORDS = ["private", "privacy", "anonymous", "no tracking", "we don't track", "we do not track", "no data collection"]
_TRACKING_WORDS = ["analytics", "google analytics", "gtag", "facebook pixel", "track", "tracking", "telemetry", "mixpanel", "amplitude", "hotjar", "segment", "datadog"]


def _check_contradictory_privacy_claims(text: str, findings: list[Finding]) -> None:
    lowered = text.lower()
    has_privacy_claim = any(word in lowered for word in _PRIVACY_CLAIM_WORDS)
    has_tracking = any(word in lowered for word in _TRACKING_WORDS)
    if has_privacy_claim and has_tracking:
        # If text contains a formal privacy policy section, assume tracking is legitimately disclosed
        has_formal_policy = bool(re.search(r'(?:privacy policy|data collection policy|cookie policy|tracking disclosure)', lowered))
        if has_formal_policy:
            return
        findings.append(Finding(
            code="CONTRADICTORY_PRIVACY_CLAIMS",
            severity="high",
            message="Text claims privacy/no-tracking but also mentions analytics/tracking tools.",
            recommendation="Either remove the privacy/no-tracking claims or remove tracking tools. "
                           "If using analytics, clearly disclose it in a formal privacy policy.",
        ))


def review_project_text(content: str) -> dict:
    findings: list[Finding] = []
    text = content or ""

    all_patterns = {**ANTI_SLOP_PATTERNS, **ADDITIONAL_SLOP_PATTERNS}
    for code, (pattern, severity) in all_patterns.items():
        matches = re.findall(pattern, text, flags=re.I | re.M)
        if matches:
            findings.append(Finding(
                code=code,
                severity=severity,
                message=f"Detected possible slop/generic content: {code}.",
                recommendation="Replace vague or fake content with specific, accurate, product-specific copy.",
            ))

    _check_empty_sections(text, findings)
    _check_exclamation_spam(text, findings)
    _check_contradictory_privacy_claims(text, findings)

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
