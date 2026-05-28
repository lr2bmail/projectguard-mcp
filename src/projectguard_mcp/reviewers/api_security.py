from __future__ import annotations

import re

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings

_ROUTE_PATTERNS = [
    r"@app\.route\([^)]+",
    r"@router\.(get|post|put|patch|delete)\([^)]+",
    r"app\.(get|post|put|patch|delete)\([^)]+",
    r"router\.(get|post|put|patch|delete)\([^)]+",
]

_AUTH_WORDS = [
    "login_required",
    "require_auth",
    "authenticated",
    "current_user",
    "jwt_required",
    "depends(get_current_user",
    "authmiddleware",
    "passport.authenticate",
    "verifytoken",
    "bearer",
]

_OWNER_WORDS = [
    "owner_id",
    "user_id",
    "account_id",
    "tenant_id",
    "team_id",
    "organization_id",
    "current_user.id",
    "request.user",
    "g.user",
    "session[",
]

_ADMIN_WORDS = [
    "is_admin",
    "role",
    "permission",
    "require_admin",
    "admin_required",
    "has_permission",
    "authorize",
]

_RATE_LIMIT_WORDS = [
    "limiter",
    "rate_limit",
    "ratelimit",
    "slowapi",
    "flask-limiter",
    "express-rate-limit",
    "throttle",
]

_MUTATING_METHODS = ["post", "put", "patch", "delete"]


def _has_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def _looks_like_route(content: str) -> bool:
    return any(re.search(pattern, content, re.I) for pattern in _ROUTE_PATTERNS)


def _has_numeric_resource_id(content: str) -> bool:
    patterns = [
        r"/<(?:int:)?(?:id|user_id|order_id|invoice_id|file_id|project_id)>",
        r"/:(?:id|userId|orderId|invoiceId|fileId|projectId)",
        r"\b(?:id|user_id|order_id|invoice_id|file_id|project_id)\s*=\s*request\.",
    ]
    return any(re.search(pattern, content, re.I) for pattern in patterns)


def _route_uses_mutating_method(content: str) -> bool:
    lowered = content.lower()
    if any(f"@router.{method}" in lowered or f"app.{method}(" in lowered or f"router.{method}(" in lowered for method in _MUTATING_METHODS):
        return True
    return bool(re.search(r"methods\s*=\s*\[[^\]]*(post|put|patch|delete)", lowered, re.I))


def review_api_security(project_type: str, files: dict[str, str] | None = None, features: list[str] | None = None) -> dict:
    """Review defensive API security issues such as auth, IDOR/BOLA, admin checks, and rate limits."""
    files = files or {}
    findings: list[Finding] = []
    all_text = "\n".join(files.values()).lower()
    feature_text = " ".join(features or []).lower()
    pt = (project_type or "").lower()

    route_files = [(path, content) for path, content in files.items() if _looks_like_route(content)]
    api_context = any(word in pt + " " + feature_text + " " + all_text for word in ["api", "dashboard", "admin", "graphql", "webhook", "endpoint"])

    if not route_files and not api_context:
        findings.append(Finding(
            code="NO_API_SURFACE_DETECTED",
            severity="info",
            message="No obvious API route surface was detected.",
            recommendation="Run this review only when the project has API routes, dashboards, or resource endpoints.",
        ))

    if api_context and not _has_any(all_text, _AUTH_WORDS):
        findings.append(Finding(
            code="API_AUTH_NOT_VISIBLE",
            severity="high",
            message="API or dashboard surface detected but no visible authentication checks were found.",
            recommendation="Require authentication middleware/dependencies on private API and dashboard routes.",
            path=None,
        ))

    if api_context and not _has_any(all_text, _RATE_LIMIT_WORDS):
        findings.append(Finding(
            code="API_RATE_LIMIT_NOT_VISIBLE",
            severity="medium",
            message="No visible rate limiting for API or dashboard endpoints.",
            recommendation="Add rate limits to login, public API, webhook, and abuse-sensitive endpoints.",
        ))

    if "graphql" in all_text and not any(word in all_text for word in ["depth", "complexity", "cost", "disable_introspection", "introspection"]):
        findings.append(Finding(
            code="GRAPHQL_NO_DEPTH_OR_COMPLEXITY_LIMIT",
            severity="high",
            message="GraphQL endpoint is present without visible depth/complexity limiting.",
            recommendation="Add query depth, complexity, and cost limits; restrict introspection in production.",
        ))

    for path, content in route_files:
        lowered = content.lower()
        if _has_numeric_resource_id(content) and not _has_any(lowered, _OWNER_WORDS):
            findings.append(Finding(
                code="MISSING_OBJECT_AUTHORIZATION",
                severity="high",
                message="Route appears to use resource IDs without visible owner/user/tenant checks.",
                recommendation="Filter resources by current user/account/team before returning or modifying them.",
                path=path,
            ))

        if "admin" in path.lower() or "admin" in lowered:
            if not _has_any(lowered, _ADMIN_WORDS):
                findings.append(Finding(
                    code="ADMIN_ROUTE_WITHOUT_ROLE_CHECK",
                    severity="critical",
                    message="Admin route or admin logic detected without visible role/permission checks.",
                    recommendation="Require explicit admin role/permission checks for all admin endpoints.",
                    path=path,
                ))

        if _route_uses_mutating_method(content) and not _has_any(lowered, _AUTH_WORDS):
            findings.append(Finding(
                code="MUTATING_ROUTE_WITHOUT_AUTH",
                severity="high",
                message="POST/PUT/PATCH/DELETE route detected without visible authentication.",
                recommendation="Require auth and authorization on all state-changing endpoints.",
                path=path,
            ))

        if re.search(r"api[_-]?key|token", lowered) and "hash" not in lowered and "secret" not in lowered:
            findings.append(Finding(
                code="API_KEY_HANDLING_REVIEW_NEEDED",
                severity="medium",
                message="API key/token handling appears present without visible hashing or secret-management wording.",
                recommendation="Store API keys hashed where possible, show only once, and support revocation/rotation.",
                path=path,
            ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="API security review passed." if score >= 85 else "API security review found issues to fix.",
        metadata={
            "project_type": project_type,
            "route_file_count": len(route_files),
            "frameworks": ["OWASP API Top 10", "OWASP A01 Broken Access Control"],
        },
    ).to_dict()
