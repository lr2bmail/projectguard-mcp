from __future__ import annotations

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import contains_any, count_words


def analyze_project_request(project_type: str, user_request: str) -> dict:
    findings: list[Finding] = []
    word_count = count_words(user_request)
    lowered = user_request.lower()

    if word_count < 25:
        findings.append(Finding(
            code="REQUEST_TOO_SHORT",
            severity="medium",
            message="Project request is too short and may cause generic AI output.",
            recommendation="Add target users, main features, tech stack, and success criteria.",
        ))

    if not contains_any(lowered, ["user", "customer", "visitor", "admin", "client", "developer", "business"]):
        findings.append(Finding(
            code="TARGET_USERS_UNCLEAR",
            severity="medium",
            message="Target users are unclear.",
            recommendation="Define who will use the product and what they need to do first.",
        ))

    if not contains_any(lowered, ["feature", "tool", "page", "flow", "api", "dashboard", "upload", "payment", "report"]):
        findings.append(Finding(
            code="CORE_FEATURES_UNCLEAR",
            severity="medium",
            message="Core features are unclear.",
            recommendation="List the exact v1 screens/tools/endpoints before coding.",
        ))

    if project_type.lower() in {"website", "web app", "saas", "app"} and "mobile" not in lowered:
        findings.append(Finding(
            code="MOBILE_UX_NOT_MENTIONED",
            severity="low",
            message="Mobile UX is not mentioned.",
            recommendation="Require mobile-first layout and usable forms on small screens.",
        ))

    if contains_any(lowered, ["make it like", "clone", "copy"]):
        findings.append(Finding(
            code="CLONE_RISK",
            severity="low",
            message="The request may need clarification to clone a business model, not copy protected design/code/brand.",
            recommendation="Use competitor analysis only for feature inspiration and avoid copying brand/design/code.",
        ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 80),
        score=score,
        findings=findings,
        summary="Project request has enough detail." if score >= 80 else "Project request needs clarification or assumptions before coding.",
        metadata={"word_count": word_count},
    ).to_dict()


def create_project_brief(
    product_name: str,
    project_type: str,
    goal: str,
    target_users: list[str],
    core_features: list[str],
    constraints: list[str] | None = None,
) -> dict:
    constraints = constraints or []
    success_criteria = [
        "No fake features or fake integrations.",
        "Clear user flow from first visit to completed task.",
        "Mobile-friendly UI.",
        "Input validation and useful error states.",
        "Security basics documented for the project type.",
        "Final score must pass ProjectGuard threshold.",
    ]
    if any(word in project_type.lower() for word in ["website", "seo", "tool"]):
        success_criteria.extend([
            "Indexable content and clean URL structure.",
            "Unique title/meta description for public pages.",
        ])
    if any(word in goal.lower() for word in ["paid", "payment", "stripe", "invoice", "balance"]):
        success_criteria.extend([
            "Explicit user agreement and payment consent stored.",
            "Invoice/payment/refund records are durable.",
        ])

    return {
        "product_name": product_name,
        "project_type": project_type,
        "goal": goal,
        "target_users": target_users,
        "core_features": core_features,
        "constraints": constraints,
        "success_criteria": success_criteria,
        "v1_rule": "Build the smallest real usable version. Do not add fake/demo-only features unless clearly labeled as demo data.",
    }
