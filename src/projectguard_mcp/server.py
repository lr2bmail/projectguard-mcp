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

PROJECTGUARD_INSTRUCTIONS = """
ProjectGuard MCP is a quality gate for AI coding agents.

Use it before and after building apps, websites, SaaS products, dashboards, APIs,
scripts, and paid digital services. Always start with start_project_review unless the
user explicitly asks for a single review tool.

Required workflow:
1. start_project_review
2. create_project_brief
3. create_build_rules
4. review_file_plan before writing files
5. implementation
6. review_project_text, review_code_quality, review_security
7. review_seo for public websites
8. review_paid_launch_readiness for paid, payment, account-balance, proxy, VPN,
   email API, scanner, or other abuse-sensitive services
9. final_project_score

Do not mark a project complete when final_project_score.approved is false. Never create
fake features, fake integrations, fake testimonials, placeholder buttons, or filler text
as if they are production-ready.
""".strip()

REQUIRED_WORKFLOW = [
    "start_project_review",
    "create_project_brief",
    "create_build_rules",
    "review_file_plan",
    "implementation",
    "review_project_text",
    "review_code_quality",
    "review_security",
    "review_seo_if_public_website",
    "review_paid_launch_readiness_if_paid_or_abuse_sensitive",
    "final_project_score",
]

HARD_RULES = [
    "Do not create or edit files before review_file_plan passes.",
    "Do not mark complete unless final_project_score.approved is true.",
    "Do not create fake features, fake integrations, fake testimonials, or filler text.",
    "Do not rewrite unrelated files or ignore the existing project structure.",
    "For paid or abuse-sensitive services, run paid launch readiness before final approval.",
]

mcp = FastMCP(
    "ProjectGuard MCP",
    instructions=PROJECTGUARD_INSTRUCTIONS,
    json_response=True,
)


@mcp.tool()
def start_project_review(
    project_type: str,
    user_request: str,
    features: list[str] | None = None,
) -> dict[str, Any]:
    """
    Start here before building any app, website, SaaS, dashboard, API, or script.

    Returns the required ProjectGuard workflow, risk flags, missing details, required
    review gates, hard rules, and the next tool the coding agent should call.
    """
    risk = _classify_project_risk(project_type, user_request, features)
    analysis = _analyze_project_request(project_type, user_request)
    required_reviews = ["review_file_plan", "review_project_text", "review_code_quality", "review_security"]

    if any(word in project_type.lower() for word in ["website", "seo", "landing", "tools"]):
        required_reviews.append("review_seo")
    if risk.get("requires_paid_launch_review") or risk.get("requires_aup_review"):
        required_reviews.append("review_paid_launch_readiness")

    return {
        "status": "started",
        "required_workflow": REQUIRED_WORKFLOW,
        "required_reviews": required_reviews,
        "risk": risk,
        "request_analysis": analysis,
        "next_tool": "create_project_brief",
        "hard_rules": HARD_RULES,
        "client_usage_hint": (
            "Claude Code should keep these rules in CLAUDE.md. Codex should keep these rules in AGENTS.md. "
            "Both clients should connect this MCP server and call start_project_review first."
        ),
    }


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
    """Detect AI slop, fake content, filler text, boilerplate phrases, fake metrics, stub code, placeholder brackets, empty sections, and exclamation spam."""
    return _review_project_text(content)


@mcp.tool()
def review_code_quality(files: dict[str, str]) -> dict[str, Any]:
    """Run code-quality checks: secrets, TODOs, debug statements, hardcoded URLs, commented code, empty catches, large files, async error handling, and missing tests."""
    return _review_code_quality(files)


@mcp.tool()
def review_security(project_type: str, files: dict[str, str], features: list[str] | None = None) -> dict[str, Any]:
    """Review security risks: SQL injection, XSS, SSRF, deserialization, weak crypto, hardcoded credentials, debug mode, CORS, path traversal, JWT, CSP, CSRF, rate limiting, and payment security."""
    return _review_security(project_type, files, features)


@mcp.tool()
def review_seo(public_pages: dict[str, str]) -> dict[str, Any]:
    """Review SEO for public HTML pages: title/meta length, H1 hierarchy, OG/Twitter cards, viewport, lang attr, noindex traps, image alt/dimensions, JSON-LD schema, content depth, and canonical URLs."""
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


@mcp.resource("projectguard://workflow/agent")
def agent_workflow_resource() -> str:
    """Canonical ProjectGuard workflow for AI coding agents."""
    return PROJECTGUARD_INSTRUCTIONS


@mcp.resource("projectguard://workflow/claude-code")
def claude_code_workflow_resource() -> str:
    """Claude Code usage rules for ProjectGuard."""
    return """
Use ProjectGuard MCP as the quality gate in Claude Code.

Before coding:
- Call start_project_review.
- Call create_project_brief and create_build_rules.
- Call review_file_plan and wait for approval before writing files.

After coding:
- Call review_project_text, review_code_quality, review_security, and final_project_score.
- Call review_seo for public websites.
- Call review_paid_launch_readiness for paid/payment/account-balance/abuse-sensitive projects.

Put these rules in CLAUDE.md for persistent project behavior.
""".strip()


@mcp.resource("projectguard://workflow/codex")
def codex_workflow_resource() -> str:
    """Codex usage rules for ProjectGuard."""
    return """
Use ProjectGuard MCP as the quality gate in Codex.

Before coding:
- Call start_project_review.
- Call create_project_brief and create_build_rules.
- Call review_file_plan and wait for approval before writing files.

After coding:
- Call review_project_text, review_code_quality, review_security, and final_project_score.
- Call review_seo for public websites.
- Call review_paid_launch_readiness for paid/payment/account-balance/abuse-sensitive projects.

Put these rules in AGENTS.md for persistent project behavior. Configure MCP in ~/.codex/config.toml
or project-scoped .codex/config.toml for trusted projects.
""".strip()


@mcp.resource("projectguard://rules/general")
def general_rules_resource() -> str:
    """General anti-slop build rules."""
    return "\n".join(rules_for_project("general"))


@mcp.resource("projectguard://rules/website")
def website_rules_resource() -> str:
    """Website and SEO anti-slop build rules."""
    return "\n".join(rules_for_project("website", ["public_website"]))


@mcp.resource("projectguard://rules/saas")
def saas_rules_resource() -> str:
    """SaaS and web-app anti-slop build rules."""
    return "\n".join(rules_for_project("saas", ["user_data", "deployment"]))


@mcp.resource("projectguard://rules/paid-launch")
def paid_launch_rules_resource() -> str:
    """Paid SaaS and digital-service readiness rules."""
    return "\n".join(rules_for_project("paid saas", ["paid", "payment", "account_balance", "abuse_sensitive"]))


@mcp.resource("projectguard://examples/good-file-plan")
def good_file_plan_resource() -> str:
    """Example of a better file plan for a Flask SaaS."""
    return """
app.py
config.py
routes/auth.py
routes/billing.py
routes/tools.py
models/user.py
models/invoice.py
templates/base.html
templates/index.html
templates/dashboard.html
static/css/app.css
static/js/app.js
tests/test_auth.py
tests/test_billing.py
""".strip()


@mcp.resource("projectguard://examples/bad-file-plan")
def bad_file_plan_resource() -> str:
    """Example of a weak file plan that should be rejected."""
    return """
index.html
style.css
script.js
""".strip()


@mcp.prompt()
def coding_agent_workflow(project_type: str = "web app") -> str:
    """Prompt template that forces an AI coding agent to use ProjectGuard gates."""
    return f"""
You are building a {project_type} and you are connected to ProjectGuard MCP.

Before coding:
1. Call start_project_review.
2. Call create_project_brief.
3. Call create_build_rules.
4. Call review_file_plan and do not create files until the plan passes.

After coding:
1. Call review_project_text for public copy/README/final answer.
2. Call review_code_quality.
3. Call review_security.
4. Call review_seo for public websites.
5. Call review_paid_launch_readiness for paid SaaS/digital services.
6. Call final_project_score.

Never mark the project complete if final_project_score.approved is false.
""".strip()


@mcp.prompt()
def projectguard_start(project_type: str = "web app") -> str:
    """Use this at the start of any AI coding task."""
    return coding_agent_workflow(project_type)


@mcp.prompt()
def projectguard_final_review(project_type: str = "web app") -> str:
    """Use this before marking an AI coding task complete."""
    return f"""
Before marking the {project_type} task complete, call ProjectGuard final review tools:
1. review_project_text
2. review_code_quality
3. review_security
4. review_seo if this is a public website
5. review_paid_launch_readiness if this is paid, account-based, payment-based, or abuse-sensitive
6. final_project_score

Do not say the task is complete unless final_project_score.approved is true.
""".strip()


@mcp.prompt()
def claude_code_projectguard_workflow(project_type: str = "web app") -> str:
    """Claude Code prompt for using ProjectGuard as a quality gate."""
    return coding_agent_workflow(project_type)


@mcp.prompt()
def codex_projectguard_workflow(project_type: str = "web app") -> str:
    """Codex prompt for using ProjectGuard as a quality gate."""
    return f"""
You are Codex working on a {project_type}. ProjectGuard MCP is available.

Follow this gate:
1. Call start_project_review before planning code changes.
2. Call create_project_brief and create_build_rules.
3. Call review_file_plan and do not edit files until it passes.
4. Implement only the approved scope.
5. Run review_project_text, review_code_quality, review_security, and final_project_score.
6. Add review_seo for public websites.
7. Add review_paid_launch_readiness for paid/payment/account-balance/abuse-sensitive projects.

Never mark complete if final_project_score.approved is false.
""".strip()


def main() -> None:
    transport = os.getenv("PROJECTGUARD_TRANSPORT", "stdio").lower()
    if transport in {"http", "streamable-http", "streamable_http"}:
        mcp.run(transport="streamable-http")
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
