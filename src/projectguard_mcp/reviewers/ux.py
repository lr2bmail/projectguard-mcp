from __future__ import annotations

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings


def review_ux_checklist(
    has_mobile_layout: bool,
    has_clear_primary_action: bool,
    has_empty_states: bool,
    has_error_states: bool,
    has_loading_states: bool,
    has_accessible_labels: bool,
    notes: str = "",
) -> dict:
    findings: list[Finding] = []
    checks = {
        "MOBILE_LAYOUT_MISSING": (has_mobile_layout, "No confirmed mobile layout."),
        "PRIMARY_ACTION_MISSING": (has_clear_primary_action, "No clear primary action."),
        "EMPTY_STATES_MISSING": (has_empty_states, "No empty states."),
        "ERROR_STATES_MISSING": (has_error_states, "No useful error states."),
        "LOADING_STATES_MISSING": (has_loading_states, "No loading states."),
        "ACCESSIBLE_LABELS_MISSING": (has_accessible_labels, "No accessible form labels/controls."),
    }
    for code, (passed, message) in checks.items():
        if not passed:
            findings.append(Finding(code, "medium", message, "Add the missing UX state before final delivery."))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="UX checklist passed." if score >= 85 else "UX checklist needs fixes.",
        metadata={"notes": notes},
    ).to_dict()
