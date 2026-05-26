from __future__ import annotations


def clamp_score(value: int | float) -> int:
    return max(0, min(100, int(round(value))))


def final_project_score(
    code_score: int,
    ux_score: int,
    security_score: int,
    seo_score: int = 100,
    paid_launch_score: int | None = None,
) -> dict:
    weights = {
        "code": 0.30,
        "ux": 0.25,
        "security": 0.25,
        "seo": 0.10,
        "paid_launch": 0.10 if paid_launch_score is not None else 0.0,
    }

    if paid_launch_score is None:
        weights["code"] = 0.35
        weights["ux"] = 0.30
        weights["security"] = 0.25
        weights["seo"] = 0.10

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
    if code_score < 75:
        blocking.append("code_score_below_minimum")
    if security_score < 80:
        blocking.append("security_score_below_minimum")
    if paid_launch_score is not None and paid_launch_score < 70:
        blocking.append("paid_launch_score_below_beta_minimum")

    return {
        "overall_score": overall,
        "approved": overall >= 85 and not blocking,
        "minimum_required_score": 85,
        "blocking_issues": blocking,
        "scores": {
            "code": clamp_score(code_score),
            "ux": clamp_score(ux_score),
            "security": clamp_score(security_score),
            "seo": clamp_score(seo_score),
            "paid_launch": None if paid_launch_score is None else clamp_score(paid_launch_score),
        },
    }
