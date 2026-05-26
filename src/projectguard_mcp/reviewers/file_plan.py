from __future__ import annotations

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import safe_path_parts


def review_file_plan(project_type: str, files: list[str]) -> dict:
    findings: list[Finding] = []
    lowered_paths = [f.lower().replace("\\", "/") for f in files]
    pt = project_type.lower()

    if not files:
        findings.append(Finding("NO_FILES", "critical", "No files were provided in the file plan."))

    if 0 < len(files) <= 3 and any(word in pt for word in ["website", "app", "saas", "dashboard"]):
        findings.append(Finding(
            code="FILE_PLAN_TOO_SMALL",
            severity="medium",
            message="File plan is very small for this project type.",
            recommendation="Use separate files/modules for routes, templates/components, static assets, and business logic.",
        ))

    if any(".." in safe_path_parts(path) for path in files):
        findings.append(Finding(
            code="UNSAFE_PATH",
            severity="critical",
            message="File plan contains unsafe parent-directory traversal.",
            recommendation="All paths must stay inside the project root.",
        ))

    if any(word in pt for word in ["flask", "python", "saas", "api"]):
        if not any(path.endswith(".py") for path in lowered_paths):
            findings.append(Finding("NO_PYTHON_FILES", "medium", "Python/backend project has no Python files."))
        if not any("test" in path for path in lowered_paths):
            findings.append(Finding("NO_TESTS", "medium", "No tests are planned.", "Add at least basic tests for reviewers/rules."))

    if any(word in pt for word in ["website", "seo", "tools", "landing"]):
        has_layout = any("base" in path or "layout" in path for path in lowered_paths)
        has_static = any("static" in path or "assets" in path or path.endswith(('.css', '.js')) for path in lowered_paths)
        if not has_layout:
            findings.append(Finding("NO_SHARED_LAYOUT", "medium", "No reusable layout/base template is planned."))
        if not has_static:
            findings.append(Finding("NO_STATIC_STRUCTURE", "low", "No CSS/JS/static asset structure is planned."))

    if any(word in pt for word in ["saas", "dashboard", "admin"]):
        if not any("model" in path or "schema" in path for path in lowered_paths):
            findings.append(Finding("NO_MODEL_SCHEMA", "medium", "No model/schema layer is planned."))
        if not any("route" in path or "controller" in path or "api" in path for path in lowered_paths):
            findings.append(Finding("NO_ROUTES", "medium", "No routes/controllers/API layer is planned."))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 82),
        score=score,
        findings=findings,
        summary="File plan is acceptable." if score >= 82 else "File plan should be improved before implementation.",
        metadata={"file_count": len(files)},
    ).to_dict()
