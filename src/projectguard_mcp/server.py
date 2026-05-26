from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from projectguard_mcp.reviewers.anti_slop import review_project_text as _review_project_text
from projectguard_mcp.reviewers.classifier import classify_project_risk as _classify_project_risk
from projectguard_mcp.reviewers.code_quality import review_code_quality as _review_code_quality
from projectguard_mcp.reviewers.file_plan import review_file_plan as _review_file_plan
from projectguard_mcp.reviewers.paid_launch import review_paid_launch_readiness as _review_paid_launch_readiness
from projectguard_mcp.reviewers.project_request import (
    analyze_project_request as _analyze_project_request,
)
from projectguard_mcp.reviewers.project_request import create_project_brief as _create_project_brief
from projectguard_mcp.reviewers.security import review_security as _review_security
from projectguard_mcp.reviewers.seo import review_seo as _review_seo
from projectguard_mcp.reviewers.ux import review_ux_checklist as _review_ux_checklist
from projectguard_mcp.rules import rules_for_project
from projectguard_mcp.scoring import final_project_score as _final_project_score

mcp = FastMCP("ProjectGuard MCP", json_response=True)


@mcp.tool()
def classify_project_risk(project_type: str, description: str, features: list[str] | None = None) -> dict[str, Any]:
    """Classify project risk and decide which ProjectGuard reviews are required."""
    return _classify_project_risk(project_type, description, features)


@mcp.tool()
def analyze_project_request(project_type: str, user_request: str) -> dict[str, Any]:
    """Check whether a project request is detailed enough before coding starts."""
    return _analyze_project_request(project_type, user_request)


@mcp.tool()
def create_project_brief(
    product_name: str,
    project_type: str,
    goal: str,
    target_users: list[str],
    core_features: list[str],
    constraints: list[str] | None = None,
) -> dict[str, Any]:
    """Create a structured project brief that the coding agent must follow."""
    return _create_project_brief(product_name, project_type, goal, target_users, core_features, constraints)


@mcp.tool()
def create_build_rules(project_type: str, risk_flags: list[str] | None = None) -> dict[str, Any]:
    """Return strict build rules to prevent low-quality AI-generated projects."""
    return {
        "project_type": project_type,
        "risk_flags": risk_flags or [],
        "rules": rules_for_project(project_type, risk_flags),
    }


@mcp.tool()
def review_file_plan(project_type: str, files: list[str]) -> dict[str, Any]:
    """Review a proposed file structure before the AI creates or edits files."""
    return _review_file_plan(project_type, files)


@mcp.tool()
def review_project_text(content: str) -> dict[str, Any]:
    """Detect sloppy AI text, fake content, filler, and placeholder language."""
    return _review_project_text(content)


@mcp.tool()
def review_code_quality(files: dict[str, str]) -> dict[str, Any]:
    """Run lightweight code-quality checks on proposed or generated files."""
    return _review_code_quality(files)


@mcp.tool()
def review_security(project_type: str, files: dict[str, str], features: list[str] | None = None) -> dict[str, Any]:
    """Review basic security risks based on project type, feature list, and code."""
    return _review_security(project_type, files, features)


@mcp.tool()
def review_seo(public_pages: dict[str, str]) -> dict[str, Any]:
    """Review SEO basics for public HTML pages."""
    return _review_seo(public_pages)


@mcp.tool()
def review_ux_checklist(
    has_mobile_layout: bool,
    has_clear_primary_action: bool,
    has_empty_states: bool,
    has_error_states: bool,
    has_loading_states: bool,
    has_accessible_labels: bool,
    notes: str = "",
) -> dict[str, Any]:
    """Review basic UX completeness using explicit checklist signals."""
    return _review_ux_checklist(
        has_mobile_layout,
        has_clear_primary_action,
        has_empty_states,
        has_error_states,
        has_loading_states,
        has_accessible_labels,
        notes,
    )


@mcp.tool()
def review_paid_launch_readiness(
    project_type: str,
    legal_pages: list[str] | None = None,
    signup_audit_fields: list[str] | None = None,
    payment_fields: list[str] | None = None,
    order_confirmation_fields: list[str] | None = None,
    ledger_fields: list[str] | None = None,
    admin_features: list[str] | None = None,
    processors: list[str] | None = None,
    abuse_sensitive: bool = False,
) -> dict[str, Any]:
    """Check minimum paid SaaS/digital-service launch readiness. Not legal/tax advice."""
    return _review_paid_launch_readiness(
        project_type=project_type,
        legal_pages=legal_pages,
        signup_audit_fields=signup_audit_fields,
        payment_fields=payment_fields,
        order_confirmation_fields=order_confirmation_fields,
        ledger_fields=ledger_fields,
        admin_features=admin_features,
        processors=processors,
        abuse_sensitive=abuse_sensitive,
    )


@mcp.tool()
def final_project_score(
    code_score: int,
    ux_score: int,
    security_score: int,
    seo_score: int = 100,
    paid_launch_score: int | None = None,
) -> dict[str, Any]:
    """Calculate final approval score after individual reviews have run."""
    return _final_project_score(code_score, ux_score, security_score, seo_score, paid_launch_score)


@mcp.resource("projectguard://rules/general")
def general_rules_resource() -> str:
    """General anti-slop build rules."""
    return "\n".join(rules_for_project("general"))


@mcp.prompt()
def coding_agent_workflow(project_type: str = "web app") -> str:
    """Prompt template that forces an AI coding agent to use ProjectGuard gates."""
    return f"""
You are building a {project_type} and you are connected to ProjectGuard MCP.

Before coding:
1. Call classify_project_risk.
2. Call analyze_project_request.
3. Call create_project_brief.
4. Call create_build_rules.
5. Call review_file_plan and do not create files until the plan passes.

After coding:
1. Call review_project_text for public copy/README/final answer.
2. Call review_code_quality.
3. Call review_security.
4. Call review_seo for public websites.
5. Call review_paid_launch_readiness for paid SaaS/digital services.
6. Call final_project_score.

Never mark the project complete if final_project_score.approved is false.
""".strip()


def main() -> None:
    transport = os.getenv("PROJECTGUARD_TRANSPORT", "streamable-http")
    if transport == "stdio":
        mcp.run(transport="stdio")
        return
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
