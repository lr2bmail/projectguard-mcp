from __future__ import annotations

import re

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import file_ext

SECRET_PATTERNS = [
    r"sk_live_[A-Za-z0-9_\-]+",
    r"xox[baprs]-[A-Za-z0-9\-]+",
    r"AKIA[0-9A-Z]{16}",
    r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]",
]


def review_code_quality(files: dict[str, str]) -> dict:
    findings: list[Finding] = []

    if not files:
        findings.append(Finding("NO_CODE", "critical", "No code files were provided."))

    for path, content in files.items():
        ext = file_ext(path)
        lowered = content.lower()

        for pattern in SECRET_PATTERNS:
            if re.search(pattern, content):
                findings.append(Finding(
                    code="POSSIBLE_SECRET",
                    severity="critical",
                    message="Possible secret or credential found in source code.",
                    recommendation="Move secrets to environment variables or a secret manager.",
                    path=path,
                ))
                break

        if "todo" in lowered or "fixme" in lowered:
            findings.append(Finding(
                code="TODO_LEFT_IN_CODE",
                severity="low",
                message="TODO/FIXME marker found.",
                recommendation="Resolve or convert to a tracked issue before final delivery.",
                path=path,
            ))

        if ext == "py":
            if "except:" in content or "except Exception" in content and "logger" not in lowered:
                findings.append(Finding(
                    code="WEAK_EXCEPTION_HANDLING",
                    severity="medium",
                    message="Broad exception handling without visible logging or specific recovery.",
                    recommendation="Catch specific exceptions and log useful context.",
                    path=path,
                ))
            if "os.system(" in content or "subprocess" in content and "shell=True" in content:
                findings.append(Finding(
                    code="RISKY_COMMAND_EXECUTION",
                    severity="high",
                    message="Risky command execution pattern detected.",
                    recommendation="Use allowlisted commands, no shell=True, timeouts, and audit logs.",
                    path=path,
                ))

        if ext in {"html", "htm"}:
            if "<button" in lowered and "disabled" not in lowered and "onclick" not in lowered and "type=" not in lowered:
                findings.append(Finding(
                    code="AMBIGUOUS_BUTTON",
                    severity="low",
                    message="Button without clear type/action may be placeholder UI.",
                    recommendation="Connect buttons to real actions or disable/label them clearly.",
                    path=path,
                ))

    has_tests = any("test" in path.lower() for path in files)
    if not has_tests and len(files) >= 3:
        findings.append(Finding(
            code="NO_TEST_FILES",
            severity="medium",
            message="No test files provided.",
            recommendation="Add unit tests for rules, scoring, and critical flows.",
        ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="Code quality passed basic checks." if score >= 85 else "Code quality needs fixes before final approval.",
        metadata={"file_count": len(files)},
    ).to_dict()
