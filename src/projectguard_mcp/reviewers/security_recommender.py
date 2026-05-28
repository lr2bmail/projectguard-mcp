from __future__ import annotations

from typing import Any


API_KEYWORDS = [
    "api",
    "rest",
    "graphql",
    "endpoint",
    "route",
    "controller",
    "dashboard",
    "admin",
    "user resource",
    "invoice",
    "order",
]

PAYMENT_KEYWORDS = [
    "payment",
    "checkout",
    "stripe",
    "paypal",
    "nowpayments",
    "crypto payment",
    "webhook",
    "invoice",
    "refund",
    "balance",
    "wallet",
    "add funds",
]

DOCKER_KEYWORDS = [
    "docker",
    "container",
    "compose",
    "dockerfile",
    "deployment",
]

CI_KEYWORDS = [
    "github actions",
    "gitlab ci",
    "workflow",
    "ci/cd",
    "deploy",
]

IAC_KEYWORDS = [
    "terraform",
    "infrastructure as code",
    "aws",
    "s3",
    "iam",
    "security group",
]


def _content_blob(project_type: str, files: dict[str, str], features: list[str] | None) -> str:
    filenames = "\n".join(files.keys())
    sample = "\n".join(files.values())[:20000]
    return "\n".join([project_type or "", " ".join(features or []), filenames, sample]).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def recommend_security_reviews(
    project_type: str,
    files: dict[str, str] | None = None,
    features: list[str] | None = None,
) -> dict[str, Any]:
    """Recommend focused defensive security reviews based on project type and files."""
    files = files or {}
    text = _content_blob(project_type, files, features)
    filenames = [name.lower().replace("\\", "/") for name in files]

    recommended: list[str] = ["review_security"]
    blocking: list[str] = []
    reasons: dict[str, list[str]] = {"review_security": ["Baseline security review should always run."]}
    future_suggestions: list[str] = []

    def add(tool: str, reason: str, is_blocking: bool = False) -> None:
        if tool not in recommended:
            recommended.append(tool)
        reasons.setdefault(tool, []).append(reason)
        if is_blocking and tool not in blocking:
            blocking.append(tool)

    has_api_file = any(
        "/api" in path or "/routes" in path or "/controllers" in path or path.endswith("routes.py")
        for path in filenames
    )
    has_route_code = any(marker in text for marker in ["@app.route", "@router.", "express.router", "router.", "fastapi"])
    if has_api_file or has_route_code or _has_any(text, API_KEYWORDS):
        add("review_api_security", "API/routes/dashboard/admin/resource patterns detected.", True)

    has_payment_file = any("billing" in path or "payment" in path or "stripe" in path for path in filenames)
    if has_payment_file or _has_any(text, PAYMENT_KEYWORDS):
        add("review_payment_webhook_security", "Payment, checkout, invoice, refund, wallet, or webhook patterns detected.", True)

    has_docker_file = any(
        path.endswith("dockerfile")
        or path.endswith("docker-compose.yml")
        or path.endswith("docker-compose.yaml")
        or path.endswith("compose.yml")
        or path.endswith("compose.yaml")
        for path in filenames
    )
    if has_docker_file or _has_any(text, DOCKER_KEYWORDS):
        add("review_docker_security", "Docker/container deployment artifacts detected.", False)

    if any(path.startswith(".github/workflows/") or path.endswith(".gitlab-ci.yml") for path in filenames) or _has_any(text, CI_KEYWORDS):
        future_suggestions.append("review_ci_cd_security")

    if any(path.endswith(".tf") or path.startswith("terraform/") or path.startswith("infra/") for path in filenames) or _has_any(text, IAC_KEYWORDS):
        future_suggestions.append("review_iac_security")

    return {
        "recommended_reviews": recommended,
        "blocking_reviews": blocking,
        "future_suggestions": future_suggestions,
        "reasons": reasons,
        "detected_file_count": len(files),
        "note": "ProjectGuard recommends defensive review tools only; it does not run offensive scans or exploit workflows.",
    }
