from __future__ import annotations

import re

from projectguard_mcp.config import SQL_INJECTION_PATTERN
from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings
from projectguard_mcp.utils import file_ext


def _check_project_level_security(
    pt: str, features_text: str, all_text: str, files: dict[str, str], findings: list[Finding],
) -> None:
    if any(word in features_text + " " + pt for word in ["login", "signup", "auth", "dashboard", "admin"]):
        if "csrf" not in all_text and any(ext in " ".join(files).lower() for ext in ["html", "template", "flask"]):
            findings.append(Finding(
                code="CSRF_NOT_VISIBLE",
                severity="medium",
                message="Auth/admin/form project does not show CSRF protection.",
                recommendation="Add CSRF protection for state-changing form actions.",
            ))
        if "rate limit" not in all_text and "limiter" not in all_text:
            findings.append(Finding(
                code="RATE_LIMIT_NOT_VISIBLE",
                severity="medium",
                message="No visible rate limiting for login/API-sensitive flows.",
                recommendation="Add rate limits to login, signup, password reset, and public API endpoints.",
            ))

    if any(word in features_text + " " + pt for word in ["upload", "pdf", "image", "file"]):
        if not any(word in all_text for word in ["allowed_extensions", "content-type", "max_content_length", "file size"]):
            findings.append(Finding(
                code="UPLOAD_VALIDATION_MISSING",
                severity="high",
                message="File upload feature has no visible extension/type/size validation.",
                recommendation="Validate file type, size, storage path, and scan/parse safely.",
            ))

    if "payment" in features_text or "stripe" in all_text or "paypal" in all_text:
        if "webhook" not in all_text:
            findings.append(Finding(
                code="PAYMENT_WEBHOOK_MISSING",
                severity="high",
                message="Payment flow appears present but webhook handling is not visible.",
                recommendation="Use provider webhooks and store provider event IDs/idempotency.",
            ))
        if "idempot" not in all_text:
            findings.append(Finding(
                code="PAYMENT_IDEMPOTENCY_MISSING",
                severity="medium",
                message="No visible idempotency handling for payment events.",
                recommendation="Store provider event IDs and ignore duplicates.",
            ))


# -- File-level check helpers --

_FETCH_PATTERNS = [
    r"requests\.(get|post|put|delete|patch)\(",
    r"urllib\.request\.urlopen\(",
    r"httpx\.(get|post|async_get|async_post)\(",
    r"\bfetch\s*\(",
]

_USER_INPUT_PATTERNS = [
    r"request\.(args|form|data|query_params|GET|POST|body|params)",
    r"req\.(body|params|query)",
    r"\$_GET",
    r"\$_POST",
    r"\$_REQUEST",
]

_DESERIALIZATION_PATTERNS: list[tuple[str, str, str]] = [
    (r"pickle\.loads?\(", "pickle", "critical"),
    (r"marshal\.loads?\(", "marshal", "critical"),
    (r"\beval\s*\(", "eval", "critical"),
    (r"\bexec\s*\(", "exec", "critical"),
    (r"yaml\.load\((?!.*Loader)", "yaml_unsafe", "high"),
]

_FRAMEWORK_XSS_PATTERNS: list[tuple[str, str]] = [
    (r"dangerouslySetInnerHTML", "React dangerouslySetInnerHTML"),
    (r"v-html\s*=", "Vue v-html"),
    (r"\|\s*safe\b", "Django |safe filter"),
    (r"\.html_safe\b", "Rails html_safe"),
    (r"innerHTML\s*=", "innerHTML assignment"),
    (r"document\.write\s*\(", "document.write"),
    (r"outerHTML\s*=", "outerHTML assignment"),
]

_WEAK_CRYPTO_PATTERNS: list[tuple[str, str, str]] = [
    (r"hashlib\.(md5|sha1)\s*\(", "weak_hash", "high"),
    (r"\bDES\b|\bRC4\b|\bBlowfish\b", "weak_cipher", "high"),
    (r"random\.(randint|choice|random)\s*\(", "weak_random", "medium"),
]

_CRYPTO_CONTEXT_WORDS = ["token", "password", "secret", "key", "session", "csrf", "auth", "hash"]

_CREDENTIAL_PATTERNS = [
    r"password\s*=\s*['\"][^'\"]+['\"]",
    r"secret\s*=\s*['\"][^'\"]+['\"]",
    r"api_key\s*=\s*['\"][^'\"]+['\"]",
    r"DATABASE_URL\s*=\s*['\"]postgres(ql)?://[^'\"]+['\"]",
    r"PRIVATE_KEY\s*=\s*['\"]-----BEGIN",
]


def _check_file_security(path: str, content: str, ext: str, findings: list[Finding]) -> None:
    lowered = content.lower()

    # -- SSRF --
    has_fetch = any(re.search(p, content) for p in _FETCH_PATTERNS)
    has_user_input = any(re.search(p, content) for p in _USER_INPUT_PATTERNS)
    if has_fetch and has_user_input:
        findings.append(Finding(
            code="SSRF_USER_CONTROLLED_URL",
            severity="high",
            message="URL fetch with possible user-controlled input detected.",
            recommendation="Validate and allowlist URLs before fetching. Never pass user input directly to HTTP clients.",
            path=path,
        ))
        # Check if SSRF protection is present
        ssrf_protection_words = ["allowlist", "allow_list", "whitelist", "blocklist", "block_list",
                                 "url_validation", "validate_url", "allowed_hosts", "safe_url",
                                 "internal_only", "private_ip", "deny_private"]
        if not any(word in lowered for word in ssrf_protection_words):
            findings.append(Finding(
                code="SSRF_PROTECTION_MISSING",
                severity="high",
                message="URL fetch with user input but no visible SSRF protection.",
                recommendation="Add URL allowlisting, block private IP ranges, and validate domains before fetching.",
                path=path,
            ))

    # -- Insecure deserialization --
    for pattern, label, severity in _DESERIALIZATION_PATTERNS:
        if re.search(pattern, content):
            findings.append(Finding(
                code="INSECURE_DESERIALIZATION",
                severity=severity,
                message=f"Insecure deserialization detected: {label}.",
                recommendation="Avoid deserializing untrusted data. Use json.loads() or yaml.safe_load() instead.",
                path=path,
            ))
            break

    # -- Template injection / Framework XSS --
    for pattern, label in _FRAMEWORK_XSS_PATTERNS:
        if re.search(pattern, content, re.I):
            has_sanitization = any(word in lowered for word in ["sanitize", "dompurify", "bleach", "escap"])
            if not has_sanitization:
                findings.append(Finding(
                    code="FRAMEWORK_XSS_PATTERN",
                    severity="high",
                    message=f"Potential XSS via {label} without visible sanitization.",
                    recommendation="Use textContent or sanitize trusted HTML with a library like DOMPurify.",
                    path=path,
                ))
                break

    # -- Weak crypto --
    for pattern, label, base_severity in _WEAK_CRYPTO_PATTERNS:
        if re.search(pattern, content, re.I):
            severity = base_severity
            if label == "weak_random":
                if not any(word in lowered for word in _CRYPTO_CONTEXT_WORDS):
                    continue
                severity = "medium"
            findings.append(Finding(
                code="WEAK_CRYPTO",
                severity=severity,
                message=f"Weak cryptographic pattern detected: {label}.",
                recommendation="Use secrets module for tokens, hashlib.sha256+ for hashing, and established ciphers (AES-GCM).",
                path=path,
            ))
            break

    # -- Hardcoded credentials --
    is_test = "test" in path.lower() or "spec" in path.lower()
    is_config_example = path.endswith(".example") or path.endswith(".env.example")
    if not is_test and not is_config_example:
        for pattern in _CREDENTIAL_PATTERNS:
            if re.search(pattern, content, re.I):
                findings.append(Finding(
                    code="HARDCODED_CREDENTIALS",
                    severity="critical",
                    message="Possible hardcoded credentials in source code.",
                    recommendation="Move credentials to environment variables or a secret manager.",
                    path=path,
                ))
                break

    # -- Debug mode --
    if re.search(r"(app\.run\(.*debug\s*=\s*True|DEBUG\s*=\s*True|django\.conf.*DEBUG\s*=\s*True)", content, re.I):
        findings.append(Finding(
            code="DEBUG_TRUE",
            severity="high",
            message="Debug mode appears to be enabled.",
            recommendation="Set DEBUG=False in production. Use environment variables to control debug mode.",
            path=path,
        ))

    # -- CORS wildcard --
    if re.search(r"CORS_ORIGINS\s*=\s*['\"]\*['\"]|allow_origins\s*=\s*\[?['\"]\*['\"]|Access-Control-Allow-Origin.*\*", content):
        findings.append(Finding(
            code="CORS_WILDCARD_ORIGIN",
            severity="high",
            message="CORS configured to allow all origins.",
            recommendation="Restrict CORS to specific trusted origins instead of using wildcard.",
            path=path,
        ))

    # -- Path traversal --
    if re.search(r"\.\./|\.\.\\\\|\.\.%2[fF]|%2[eE]%2[eE]", content):
        findings.append(Finding(
            code="PATH_TRAVERSAL_RISK",
            severity="high",
            message="Potential path traversal pattern detected.",
            recommendation="Validate and normalize file paths. Use allowlisted directories.",
            path=path,
        ))

    # -- Insecure session config --
    if re.search(
        r"SESSION_COOKIE_SECURE['\"\]]*\s*[:=]\s*False|cookie\s*=\s*{.*secure\s*:\s*False|"
        r"SESSION_COOKIE_SECURE['\"\]]*\s*[:=]\s*false",
        content,
        re.I,
    ):
        findings.append(Finding(
            code="INSECURE_SESSION_CONFIG",
            severity="high",
            message="Session cookie configured without secure flag.",
            recommendation="Set SESSION_COOKIE_SECURE=True and use Secure flag on all session cookies.",
            path=path,
        ))

    # -- JWT algorithm none --
    if re.search(r"algorithm\s*=\s*['\"]none['\"]", content, re.I):
        findings.append(Finding(
            code="JWT_ALGORITHM_NONE",
            severity="critical",
            message="JWT configured with 'none' algorithm, allowing token forgery.",
            recommendation="Always specify a strong algorithm (e.g., HS256, RS256). Never accept 'none'.",
            path=path,
        ))

    # -- SQL injection (existing check) --
    if re.search(SQL_INJECTION_PATTERN, content, flags=re.I):
        findings.append(Finding(
            code="POSSIBLE_SQL_INJECTION",
            severity="critical",
            message="Possible SQL query string concatenation detected.",
            recommendation="Use parameterized queries or ORM filters.",
            path=path,
        ))

    # -- XSS innerHTML (existing check, simplified since framework check covers more) --
    if "innerhtml" in lowered and "sanitize" not in lowered:
        if not any(re.search(p, content, re.I) for p, _ in _FRAMEWORK_XSS_PATTERNS):
            findings.append(Finding(
                code="POSSIBLE_XSS",
                severity="high",
                message="innerHTML is used without visible sanitization.",
                recommendation="Use textContent or sanitize trusted HTML.",
                path=path,
            ))

    # -- Missing CSP --
    if ext in {"html", "htm"} and "<head" in lowered:
        if "content-security-policy" not in lowered and "csp" not in lowered:
            findings.append(Finding(
                code="MISSING_CSP",
                severity="medium",
                message="HTML page is missing Content-Security-Policy header.",
                recommendation="Add CSP headers to prevent XSS and data injection attacks.",
                path=path,
            ))


def review_security(project_type: str, files: dict[str, str], features: list[str] | None = None) -> dict:
    findings: list[Finding] = []
    files = files or {}
    features_text = " ".join(features or []).lower()
    all_text = "\n".join(files.values()).lower()
    pt = project_type.lower()

    if not files:
        findings.append(Finding("NO_FILES", "critical", "No code files were provided for security review."))

    _check_project_level_security(pt, features_text, all_text, files, findings)

    for path, content in files.items():
        ext = file_ext(path)
        _check_file_security(path, content, ext, findings)

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 85),
        score=score,
        findings=findings,
        summary="Security review passed basic checks." if score >= 85 else "Security review found launch-blocking or important issues.",
        metadata={"project_type": project_type, "feature_count": len(features or [])},
    ).to_dict()
