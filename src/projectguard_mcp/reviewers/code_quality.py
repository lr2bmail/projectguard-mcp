from __future__ import annotations

import re

from projectguard_mcp.config import (
    LARGE_FILE_LINE_THRESHOLD,
    LOCAL_URL_PATTERNS,
    MIN_FILES_FOR_TEST_CHECK,
    SECRET_PATTERNS,
)
from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import file_ext


def _check_debug_statements(path: str, content: str, ext: str, findings: list[Finding]) -> None:
    is_test = "test" in path.lower() or "spec" in path.lower()
    if is_test:
        return

    if ext in {"js", "ts", "jsx", "tsx"}:
        if re.search(r"\bconsole\.(log|debug|info)\s*\(", content):
            findings.append(Finding(
                code="DEBUG_STATEMENT_LEFT",
                severity="medium",
                message="console.log/debug/info statement found in production code.",
                recommendation="Remove debug console statements before final delivery.",
                path=path,
            ))
        if re.search(r"\bdebugger\s*;?", content):
            findings.append(Finding(
                code="DEBUG_STATEMENT_LEFT",
                severity="high",
                message="debugger statement found.",
                recommendation="Remove debugger statements before final delivery.",
                path=path,
            ))

    if ext == "py":
        if re.search(r"\bbreakpoint\s*\(\)|pdb\.set_trace\(\)|import\s+pdb\b", content):
            findings.append(Finding(
                code="DEBUG_STATEMENT_LEFT",
                severity="high",
                message="Debugger breakpoint found in Python code.",
                recommendation="Remove breakpoint/pdb statements before final delivery.",
                path=path,
            ))


def _check_hardcoded_local_urls(path: str, content: str, findings: list[Finding]) -> None:
    is_test = "test" in path.lower() or "spec" in path.lower()
    is_config = path.endswith(".example") or path.endswith(".env") or "docker-compose" in path.lower()
    if is_test or is_config:
        return

    for pattern in LOCAL_URL_PATTERNS:
        if re.search(pattern, content):
            findings.append(Finding(
                code="HARDCODED_LOCAL_URL",
                severity="low",
                message="Hardcoded local URL (localhost/127.0.0.1) found in source code.",
                recommendation="Use environment variables for service URLs and host configuration.",
                path=path,
            ))
            break


def _check_commented_out_code(path: str, content: str, ext: str, findings: list[Finding]) -> None:
    comment_prefix = "//" if ext in {"js", "ts", "jsx", "tsx", "java", "go", "rs", "c", "cpp"} else "#"
    code_keywords = re.compile(r"\b(if|for|while|def|class|return|import|const|let|var|function|from)\b")
    lines = content.split("\n")
    consecutive = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(comment_prefix) and code_keywords.search(stripped):
            consecutive += 1
            if consecutive >= 3:
                findings.append(Finding(
                    code="COMMENTED_OUT_CODE",
                    severity="low",
                    message="Commented-out code block detected (3+ lines).",
                    recommendation="Remove commented-out code blocks. Use version control for history.",
                    path=path,
                ))
                return
        else:
            consecutive = 0


def _check_empty_catch(path: str, content: str, ext: str, findings: list[Finding]) -> None:
    if ext in {"js", "ts", "jsx", "tsx"}:
        if re.search(r"catch\s*\([^)]*\)\s*\{\s*\}", content):
            findings.append(Finding(
                code="EMPTY_CATCH_BLOCK",
                severity="medium",
                message="Empty catch block found in JavaScript/TypeScript.",
                recommendation="Handle errors properly. At minimum, log the error for debugging.",
                path=path,
            ))

    if ext == "py":
        if re.search(r"except\s+\w*\s*:\s*\n\s*pass", content):
            findings.append(Finding(
                code="EMPTY_CATCH_BLOCK",
                severity="medium",
                message="Empty except/pass block found in Python.",
                recommendation="Handle errors properly. At minimum, log the error for debugging.",
                path=path,
            ))


def _check_large_file(path: str, content: str, findings: list[Finding]) -> None:
    line_count = content.count("\n") + 1
    if line_count > LARGE_FILE_LINE_THRESHOLD:
        findings.append(Finding(
            code="LARGE_FILE",
            severity="low",
            message=f"File has {line_count} lines, which may indicate a maintainability issue.",
            recommendation="Consider splitting large files into focused modules.",
            path=path,
        ))


def _check_async_without_error_handling(path: str, content: str, ext: str, findings: list[Finding]) -> None:
    if ext in {"js", "ts", "jsx", "tsx"}:
        if re.search(r"\basync\s+(function|\w+\s*\()", content) and "try" not in content:
            findings.append(Finding(
                code="ASYNC_WITHOUT_ERROR_HANDLING",
                severity="medium",
                message="Async function without try/catch error handling.",
                recommendation="Wrap async operations in try/catch for proper error handling.",
                path=path,
            ))
    elif ext == "py":
        if re.search(r"\basync\s+def\b", content) and "try:" not in content:
            findings.append(Finding(
                code="ASYNC_WITHOUT_ERROR_HANDLING",
                severity="medium",
                message="Async function without try/except error handling.",
                recommendation="Wrap async operations in try/except for proper error handling.",
                path=path,
            ))


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
            if ("except:" in content or "except Exception" in content) and "logger" not in lowered:
                findings.append(Finding(
                    code="WEAK_EXCEPTION_HANDLING",
                    severity="medium",
                    message="Broad exception handling without visible logging or specific recovery.",
                    recommendation="Catch specific exceptions and log useful context.",
                    path=path,
                ))
            if "os.system(" in content or ("subprocess" in content and "shell=True" in content):
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

        # New checks
        _check_debug_statements(path, content, ext, findings)
        _check_hardcoded_local_urls(path, content, findings)
        _check_commented_out_code(path, content, ext, findings)
        _check_empty_catch(path, content, ext, findings)
        _check_large_file(path, content, findings)
        _check_async_without_error_handling(path, content, ext, findings)

    has_tests = any("test" in path.lower() for path in files)
    if not has_tests and len(files) >= MIN_FILES_FOR_TEST_CHECK:
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
