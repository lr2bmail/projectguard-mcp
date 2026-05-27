from __future__ import annotations

from projectguard_mcp.config import (
    APPROVAL_THRESHOLDS,
    BLOCKING_THRESHOLDS,
    SCORING_WEIGHTS_WITH_PAID,
    SCORING_WEIGHTS_WITHOUT_PAID,
)


def clamp_score(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def final_project_score(
    code_score: int,
    ux_score: int,
    security_score: int,
    seo_score: int = 100,
    paid_launch_score: int | None = None,
) -> dict:
    if paid_launch_score is None:
        weights = dict(SCORING_WEIGHTS_WITHOUT_PAID)
    else:
        weights = dict(SCORING_WEIGHTS_WITH_PAID)

    raw = (
        code_score * weights["code"]
        + ux_score * weights["ux"]
        + security_score * weights["security"]
        + seo_score * weights["seo"]
    )
    if paid_launch_score is not None:
        raw += paid_launch_score * weights["paid_launch"]

    overall = clamp_score(raw)
    blocking = []
    if code_score < BLOCKING_THRESHOLDS["code_score"]:
        blocking.append("code_score_below_minimum")
    if security_score < BLOCKING_THRESHOLDS["security_score"]:
        blocking.append("security_score_below_minimum")
    if paid_launch_score is not None and paid_launch_score < BLOCKING_THRESHOLDS["paid_launch_score"]:
        blocking.append("paid_launch_score_below_beta_minimum")

    return {
        "overall_score": overall,
        "approved": overall >= APPROVAL_THRESHOLDS["final_overall"] and not blocking,
        "minimum_required_score": APPROVAL_THRESHOLDS["final_overall"],
        "blocking_issues": blocking,
        "scores": {
            "code": clamp_score(code_score),
            "ux": clamp_score(ux_score),
            "security": clamp_score(security_score),
            "seo": clamp_score(seo_score),
            "paid_launch": None if paid_launch_score is None else clamp_score(paid_launch_score),
        },
    }
