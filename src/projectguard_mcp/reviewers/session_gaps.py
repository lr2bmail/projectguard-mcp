"""analyze_session_gaps — meta-reviewer that compares session actions against existing MCP checks.

This is a self-improvement tool: after a coding session, the agent runs this to discover
what the MCP would NOT have caught. Each gap becomes a candidate for a future check.
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# 1. Catalog of ALL existing MCP checks (code, category, what it covers)
# ---------------------------------------------------------------------------

EXISTING_CHECKS: list[dict[str, str]] = [
    # -- Security --
    {"code": "POSSIBLE_SQL_INJECTION", "category": "security", "covers": "sql injection string concat f-string"},
    {"code": "POSSIBLE_XSS", "category": "security", "covers": "innerHTML XSS DOM injection"},
    {"code": "FRAMEWORK_XSS_PATTERN", "category": "security", "covers": "dangerouslySetInnerHTML v-html |safe html_safe document.write"},
    {"code": "SSRF_USER_CONTROLLED_URL", "category": "security", "covers": "ssrf user url fetch requests"},
    {"code": "SSRF_PROTECTION_MISSING", "category": "security", "covers": "ssrf url allowlist validation"},
    {"code": "INSECURE_DESERIALIZATION", "category": "security", "covers": "pickle yaml eval exec deserialization"},
    {"code": "WEAK_CRYPTO", "category": "security", "covers": "md5 sha1 weak crypto random des rc4"},
    {"code": "HARDCODED_CREDENTIALS", "category": "security", "covers": "hardcoded password secret api_key credentials"},
    {"code": "DEBUG_TRUE", "category": "security", "covers": "debug mode flask django debug=True"},
    {"code": "CORS_WILDCARD_ORIGIN", "category": "security", "covers": "cors wildcard allow_origins star"},
    {"code": "PATH_TRAVERSAL_RISK", "category": "security", "covers": "path traversal directory parent dot-dot"},
    {"code": "INSECURE_SESSION_CONFIG", "category": "security", "covers": "session cookie secure flag"},
    {"code": "JWT_ALGORITHM_NONE", "category": "security", "covers": "jwt algorithm none token forgery"},
    {"code": "MISSING_CSP", "category": "security", "covers": "content-security-policy CSP header"},
    {"code": "CSRF_NOT_VISIBLE", "category": "security", "covers": "csrf cross-site request forgery"},
    {"code": "RATE_LIMIT_NOT_VISIBLE", "category": "security", "covers": "rate limiting throttling"},
    {"code": "UPLOAD_VALIDATION_MISSING", "category": "security", "covers": "file upload validation extension type"},
    {"code": "PAYMENT_WEBHOOK_MISSING", "category": "security", "covers": "payment webhook handling"},
    {"code": "PAYMENT_IDEMPOTENCY_MISSING", "category": "security", "covers": "payment idempotency duplicate"},
    # -- API Security --
    {"code": "API_AUTH_NOT_VISIBLE", "category": "security", "covers": "api authentication auth middleware"},
    {"code": "API_RATE_LIMIT_NOT_VISIBLE", "category": "security", "covers": "api rate limiting endpoint"},
    {"code": "GRAPHQL_NO_DEPTH_OR_COMPLEXITY_LIMIT", "category": "security", "covers": "graphql depth complexity cost limit"},
    {"code": "MISSING_OBJECT_AUTHORIZATION", "category": "security", "covers": "idor bola object authorization ownership"},
    {"code": "ADMIN_ROUTE_WITHOUT_ROLE_CHECK", "category": "security", "covers": "admin route role permission check"},
    {"code": "MUTATING_ROUTE_WITHOUT_AUTH", "category": "security", "covers": "post put patch delete auth"},
    {"code": "API_KEY_HANDLING_REVIEW_NEEDED", "category": "security", "covers": "api key token hashing storage"},
    # -- Payment Webhook --
    {"code": "WEBHOOK_SIGNATURE_NOT_VISIBLE", "category": "security", "covers": "webhook signature verification"},
    {"code": "PAYMENT_IDEMPOTENCY_NOT_VISIBLE", "category": "security", "covers": "payment duplicate event idempotency"},
    {"code": "PAYMENT_AMOUNT_RECHECK_NOT_VISIBLE", "category": "security", "covers": "amount currency verification server-side"},
    {"code": "BALANCE_LEDGER_FIELDS_NOT_VISIBLE", "category": "security", "covers": "balance ledger before after"},
    {"code": "BALANCE_UPDATED_WITHOUT_VISIBLE_WEBHOOK_VERIFICATION", "category": "security", "covers": "balance update webhook verify"},
    {"code": "SUCCESS_REDIRECT_TRUSTED_AS_PAYMENT_RISK", "category": "security", "covers": "success redirect payment proof"},
    {"code": "REFUND_DISPUTE_FLOW_NOT_VISIBLE", "category": "security", "covers": "refund dispute chargeback"},
    # -- Docker --
    {"code": "DOCKER_BASE_IMAGE_LATEST", "category": "infrastructure", "covers": "docker base image latest tag pin"},
    {"code": "DOCKER_RUNS_AS_ROOT", "category": "infrastructure", "covers": "docker non-root user"},
    {"code": "DOCKER_MISSING_HEALTHCHECK", "category": "infrastructure", "covers": "docker healthcheck"},
    {"code": "DOCKER_REMOTE_ADD", "category": "infrastructure", "covers": "docker add remote url"},
    {"code": "DOCKER_PRIVILEGED_CONTAINER", "category": "infrastructure", "covers": "docker privileged mode"},
    {"code": "DOCKER_HOST_NETWORK", "category": "infrastructure", "covers": "docker host network"},
    {"code": "DOCKER_HOST_PID", "category": "infrastructure", "covers": "docker host pid namespace"},
    {"code": "DOCKER_SOCKET_MOUNTED", "category": "infrastructure", "covers": "docker socket mount"},
    {"code": "DOCKER_DANGEROUS_CAPABILITY", "category": "infrastructure", "covers": "docker capabilities sys_admin"},
    {"code": "DOCKER_SECRET_IN_ENV", "category": "infrastructure", "covers": "docker env secret compose"},
    {"code": "DOCKERIGNORE_MISSING", "category": "infrastructure", "covers": "dockerignore"},
    # -- Code Quality --
    {"code": "POSSIBLE_SECRET", "category": "code_quality", "covers": "secret key credential stripe slack aws"},
    {"code": "TODO_LEFT_IN_CODE", "category": "code_quality", "covers": "todo fixme marker"},
    {"code": "WEAK_EXCEPTION_HANDLING", "category": "code_quality", "covers": "broad except exception handling"},
    {"code": "RISKY_COMMAND_EXECUTION", "category": "code_quality", "covers": "os.system subprocess shell=True"},
    {"code": "DEBUG_STATEMENT_LEFT", "category": "code_quality", "covers": "console.log debugger breakpoint pdb"},
    {"code": "HARDCODED_LOCAL_URL", "category": "code_quality", "covers": "localhost 127.0.0.1 hardcoded url"},
    {"code": "COMMENTED_OUT_CODE", "category": "code_quality", "covers": "commented code blocks"},
    {"code": "EMPTY_CATCH_BLOCK", "category": "code_quality", "covers": "empty catch except pass"},
    {"code": "LARGE_FILE", "category": "code_quality", "covers": "large file line count"},
    {"code": "ASYNC_WITHOUT_ERROR_HANDLING", "category": "code_quality", "covers": "async await error handling try catch"},
    {"code": "AMBIGUOUS_BUTTON", "category": "code_quality", "covers": "button type action placeholder"},
    {"code": "NO_TEST_FILES", "category": "code_quality", "covers": "test files missing"},
    # -- SEO --
    {"code": "MISSING_TITLE", "category": "seo", "covers": "title tag"},
    {"code": "TITLE_LENGTH_ISSUE", "category": "seo", "covers": "title length characters"},
    {"code": "MISSING_META_DESCRIPTION", "category": "seo", "covers": "meta description"},
    {"code": "META_DESCRIPTION_LENGTH", "category": "seo", "covers": "meta description length"},
    {"code": "MISSING_CANONICAL", "category": "seo", "covers": "canonical link url"},
    {"code": "MULTIPLE_CANONICAL", "category": "seo", "covers": "multiple canonical tags"},
    {"code": "CANONICAL_NOT_HTTPS", "category": "seo", "covers": "canonical https"},
    {"code": "MISSING_OG_TAGS", "category": "seo", "covers": "opengraph og tags social"},
    {"code": "INCOMPLETE_OG_TAGS", "category": "seo", "covers": "opengraph og image url type description"},
    {"code": "MISSING_TWITTER_CARD", "category": "seo", "covers": "twitter card meta"},
    {"code": "MISSING_H1", "category": "seo", "covers": "h1 heading"},
    {"code": "MULTIPLE_H1", "category": "seo", "covers": "multiple h1 headings"},
    {"code": "HEADING_HIERARCHY_SKIP", "category": "seo", "covers": "heading hierarchy skip levels"},
    {"code": "MISSING_VIEWPORT", "category": "seo", "covers": "viewport meta mobile"},
    {"code": "MISSING_LANG_ATTR", "category": "seo", "covers": "html lang attribute"},
    {"code": "NOINDEX_TRAP", "category": "seo", "covers": "noindex robots meta"},
    {"code": "IMAGE_MISSING_ALT", "category": "seo", "covers": "image alt text accessibility"},
    {"code": "IMAGE_MISSING_DIMENSIONS", "category": "seo", "covers": "image width height cls"},
    {"code": "MISSING_STRUCTURED_DATA", "category": "seo", "covers": "json-ld structured data schema"},
    {"code": "DEPRECATED_SCHEMA_TYPE", "category": "seo", "covers": "deprecated schema howto faqpage"},
    {"code": "THIN_CONTENT", "category": "seo", "covers": "word count content depth thin"},
    {"code": "MISSING_LEGAL_FOOTER_LINKS", "category": "seo", "covers": "privacy terms footer legal links"},
    {"code": "MISSING_SITEMAP_XML", "category": "seo", "covers": "sitemap xml"},
    {"code": "MISSING_ROBOTS_TXT", "category": "seo", "covers": "robots.txt"},
    {"code": "COMPRESSION_NOT_ENABLED", "category": "seo", "covers": "gzip brotli compression"},
    {"code": "STATIC_CACHE_HEADERS_MISSING", "category": "seo", "covers": "cache-control headers static"},
    {"code": "CANONICAL_MISMATCH", "category": "seo", "covers": "canonical mismatch duplicate pages"},
    {"code": "GENERIC_OG_IMAGE", "category": "seo", "covers": "og:image unique social sharing"},
    {"code": "INTERNAL_LINKING_WEAK", "category": "seo", "covers": "internal links navigation"},
    {"code": "MISSING_BREADCRUMB_SCHEMA", "category": "seo", "covers": "breadcrumb breadcrumblist schema"},
    # -- Anti-slop --
    {"code": "LOREM_IPSUM", "category": "code_quality", "covers": "lorem ipsum placeholder text"},
    {"code": "PLACEHOLDER_TEXT", "category": "code_quality", "covers": "placeholder coming soon under construction"},
    {"code": "FAKE_SOCIAL_PROOF", "category": "code_quality", "covers": "fake social proof trusted thousands"},
    {"code": "GENERIC_AI_COPY", "category": "code_quality", "covers": "generic ai copy seamless revolutionize"},
    {"code": "FAKE_INTEGRATION", "category": "code_quality", "covers": "fake integration stripe paypal openai"},
    {"code": "AI_BOILERPLATE_PHRASES", "category": "code_quality", "covers": "ai boilerplate game-changer next-level"},
    {"code": "FAKE_METRICS", "category": "code_quality", "covers": "fake metrics 99.9% uptime 10x faster"},
    {"code": "STUB_CODE", "category": "code_quality", "covers": "stub pass NotImplemented placeholder"},
    {"code": "PLACEHOLDER_BRACKETS", "category": "code_quality", "covers": "placeholder brackets your company TBD"},
    {"code": "EMPTY_SECTION", "category": "code_quality", "covers": "empty section heading no content"},
    {"code": "EXCLAMATION_SPAM", "category": "code_quality", "covers": "exclamation marks spam"},
    {"code": "CONTRADICTORY_PRIVACY_CLAIMS", "category": "code_quality", "covers": "privacy claim tracking analytics contradiction"},
    {"code": "TEXT_TOO_SHORT", "category": "code_quality", "covers": "text too short length"},
    # -- UX --
    {"code": "MOBILE_LAYOUT_MISSING", "category": "ux", "covers": "mobile layout responsive"},
    {"code": "PRIMARY_ACTION_MISSING", "category": "ux", "covers": "primary action cta button"},
    {"code": "EMPTY_STATES_MISSING", "category": "ux", "covers": "empty states ui"},
    {"code": "ERROR_STATES_MISSING", "category": "ux", "covers": "error states messages"},
    {"code": "LOADING_STATES_MISSING", "category": "ux", "covers": "loading states spinner"},
    {"code": "ACCESSIBLE_LABELS_MISSING", "category": "ux", "covers": "accessible labels a11y form"},
    # -- File Plan --
    {"code": "FILE_PLAN_TOO_SMALL", "category": "code_quality", "covers": "file plan small too few files"},
    {"code": "UNSAFE_PATH", "category": "security", "covers": "unsafe path traversal file plan"},
    {"code": "NO_PYTHON_FILES", "category": "code_quality", "covers": "python files missing"},
    {"code": "NO_TESTS", "category": "code_quality", "covers": "tests missing plan"},
    {"code": "NO_SHARED_LAYOUT", "category": "ux", "covers": "shared layout base template"},
    {"code": "NO_STATIC_STRUCTURE", "category": "ux", "covers": "static assets css js structure"},
    {"code": "NO_MODEL_SCHEMA", "category": "code_quality", "covers": "model schema database"},
    {"code": "NO_ROUTES", "category": "code_quality", "covers": "routes controllers api"},
    # -- Paid Launch --
    {"code": "MISSING_TERMS_PAGE", "category": "ux", "covers": "terms of service legal page"},
    {"code": "MISSING_PRIVACY_PAGE", "category": "ux", "covers": "privacy policy legal page"},
    {"code": "MISSING_REFUND_PAGE", "category": "ux", "covers": "refund policy page"},
    {"code": "MISSING_CONTACT_PAGE", "category": "ux", "covers": "contact support page"},
    {"code": "SIGNUP_AGREEMENT_AUDIT_INCOMPLETE", "category": "code_quality", "covers": "signup agreement audit fields"},
    {"code": "PAYMENT_RECORDS_INCOMPLETE", "category": "code_quality", "covers": "payment records fields"},
    {"code": "ORDER_CONFIRMATION_INCOMPLETE", "category": "ux", "covers": "order confirmation fields"},
    {"code": "BALANCE_LEDGER_INCOMPLETE", "category": "code_quality", "covers": "balance ledger fields"},
    {"code": "ADMIN_ACCOUNTING_EXPORTS_INCOMPLETE", "category": "code_quality", "covers": "admin accounting exports csv"},
    {"code": "PROCESSORS_NOT_LISTED", "category": "code_quality", "covers": "processors listed privacy"},
    # -- Project Request --
    {"code": "REQUEST_TOO_SHORT", "category": "code_quality", "covers": "project request short detail"},
    {"code": "TARGET_USERS_UNCLEAR", "category": "ux", "covers": "target users unclear"},
    {"code": "CORE_FEATURES_UNCLEAR", "category": "code_quality", "covers": "core features unclear"},
    {"code": "MOBILE_UX_NOT_MENTIONED", "category": "ux", "covers": "mobile ux responsive mentioned"},
    {"code": "CLONE_RISK", "category": "code_quality", "covers": "clone copy trademark brand"},
]

EXISTING_CODES = {c["code"] for c in EXISTING_CHECKS}

# ---------------------------------------------------------------------------
# 2. Session action patterns — what happened in the session
# ---------------------------------------------------------------------------

# Maps action keywords to what the session summary might mention
# Each tuple: (action_keywords_to_match, topic_words_for_coverage_check)
SESSION_ACTION_TOPICS: list[tuple[list[str], str]] = [
    # (match any of these in summary, check if this topic is covered by existing checks)
    (["database", "migration", "schema", "migration file", "alembic", "prisma", "typeorm"], "database migration schema"),
    (["env file", ".env", "environment variable", "config", "configuration"], "environment variable config secrets"),
    (["log", "logging", "logger", "log level", "structured logging"], "logging structured log level"),
    (["error page", "404", "500", "error handling", "error boundary"], "error page 404 500 handling"),
    (["redirect", "301", "302", "redirect rule", "rewrite"], "redirect 301 302 http"),
    (["cors", "cross-origin", "preflight"], "cors cross-origin wildcard"),
    (["authentication", "auth", "login", "signup", "register", "oauth", "jwt", "session"], "authentication auth login jwt"),
    (["authorization", "permission", "role", "admin", "rbac", "access control"], "authorization permission role admin rbac"),
    (["validation", "input validation", "sanitize", "sanitize input", "form validation"], "validation input sanitize form"),
    (["email", "send email", "smtp", "mail", "email template"], "email smtp send mail"),
    (["cron", "scheduled", "scheduler", "background job", "task queue", "celery", "worker"], "cron scheduler background job queue"),
    (["websocket", "ws", "socket", "real-time", "sse", "server-sent"], "websocket real-time socket"),
    (["file upload", "upload", "multipart", "attachment"], "file upload validation extension type"),
    (["payment", "stripe", "paypal", "checkout", "billing", "invoice"], "payment stripe webhook billing"),
    (["docker", "container", "dockerfile", "compose", "deployment"], "docker container dockerfile compose"),
    (["cdn", "cloudfront", "cloudflare", "cache", "caching"], "cdn caching cloudfront"),
    (["https", "ssl", "tls", "certificate", "letsencrypt"], "https ssl tls certificate"),
    (["dns", "domain", "subdomain", "cname", "a record"], "dns domain subdomain"),
    (["backup", "restore", "snapshot", "disaster recovery"], "backup restore snapshot disaster"),
    (["monitoring", "alert", "alerting", "metric", "dashboard", "grafana", "prometheus"], "monitoring alert metric"),
    (["test", "testing", "unit test", "integration test", "coverage", "jest", "pytest"], "test testing unit integration coverage"),
    (["ci", "ci/cd", "github actions", "pipeline", "build", "deploy"], "ci cd pipeline build deploy"),
    (["dependency", "package", "npm", "pip", "yarn", "lock", "outdated", "vulnerability"], "dependency package npm pip vulnerability"),
    (["performance", "optimization", "lazy load", "bundle", "minif", "tree-shaking", "code split"], "performance optimization lazy bundle"),
    (["accessibility", "a11y", "aria", "screen reader", "contrast", "wcag"], "accessibility a11y aria screen reader"),
    (["i18n", "internationalization", "localization", "locale", "translation"], "i18n localization translation locale"),
    (["migration", "data migration", "seed", "fixture"], "migration data seed fixture"),
    (["rate limit", "throttle", "limiter"], "rate limiting throttle"),
    (["cookie", "cookie consent", "cookie banner", "gdpr"], "cookie consent gdpr banner"),
    (["sitemap", "robots.txt", "seo"], "sitemap robots.txt seo"),
    (["database index", "index", "query optimization", "slow query"], "database index query optimization"),
    (["pagination", "paginate", "page size", "cursor"], "pagination paginate"),
    (["search", "search engine", "elasticsearch", "full-text", "algolia"], "search engine full-text elasticsearch"),
    (["websocket", "real-time", "live update", "push notification"], "websocket real-time push notification"),
    (["batch", "bulk", "bulk operation", "batch job"], "batch bulk operation"),
    (["encryption", "encrypt", "decrypt", "aes", "rsa", "hash"], "encryption aes rsa hash"),
    (["temporal", "time zone", "timezone", "utc", "datetime"], "timezone time zone utc datetime"),
    (["queue", "message queue", "rabbitmq", "kafka", "redis queue"], "queue message rabbitmq kafka"),
    (["feature flag", "feature toggle", "ab test", "experiment"], "feature flag toggle ab test"),
]


def _extract_actions(summary: str, files: dict[str, str] | None) -> list[str]:
    """Extract session actions by matching topic keywords in summary + file content."""
    text = (summary or "").lower()
    if files:
        text += " " + " ".join(files.values()).lower()[:20000]

    matched_topics: list[str] = []
    for keywords, topic in SESSION_ACTION_TOPICS:
        if any(kw in text for kw in keywords):
            matched_topics.append(topic)
    return matched_topics


def _check_covers_topic(check_covers: str, topic: str) -> bool:
    """Check if a single existing check's 'covers' words overlap with a topic."""
    topic_words = set(topic.lower().split())
    covers_words = set(check_covers.lower().split())
    return bool(topic_words & covers_words)


def _find_covering_checks(topic: str) -> list[str]:
    """Return existing check codes that cover a given topic."""
    return [c["code"] for c in EXISTING_CHECKS if _check_covers_topic(c["covers"], topic)]


def _suggest_gap(topic: str, summary: str) -> dict[str, str] | None:
    """Generate a suggested check for an uncovered topic."""
    topic_words = topic.lower().split()
    category_map = {
        "security": ["authentication", "authorization", "encryption", "cors", "jwt", "csrf", "xss",
                      "sql", "ssrf", "injection", "vulnerability", "ssl", "tls", "https", "cookie"],
        "seo": ["sitemap", "robots", "meta", "canonical", "opengraph", "schema", "structured",
                "redirect", "301", "302", "seo", "search engine"],
        "performance": ["performance", "optimization", "lazy", "bundle", "cache", "cdn", "minif",
                        "pagination", "index", "query optimization"],
        "infrastructure": ["docker", "container", "ci", "cd", "pipeline", "deploy", "backup",
                           "monitoring", "alert", "cron", "scheduler", "queue"],
        "ux": ["accessibility", "a11y", "aria", "error page", "mobile", "i18n", "localization",
               "empty states", "loading"],
    }

    category = "code_quality"
    for cat, cat_words in category_map.items():
        if any(w in " ".join(topic_words) for w in cat_words):
            category = cat
            break

    # Generate a check name from the topic
    primary = topic_words[0] if topic_words else "unknown"
    check_name = f"MISSING_{primary.upper()}_CHECK"

    # Generate detection hints based on the topic
    hints = {
        "logging": "Look for: logging config, logger setup, log handlers, structured logging format, log levels in config files",
        "email": "Look for: SMTP config, email send calls, email template files, mailer setup",
        "cron scheduler": "Look for: cron expressions, celery config, scheduler definitions, periodic task setup",
        "websocket": "Look for: WebSocket connections, socket.io, ws://, real-time event handlers",
        "cdn caching": "Look for: CDN headers, Cache-Control, CloudFront/Cloudflare config, static asset versioning",
        "backup restore": "Look for: backup scripts, database dump commands, restore procedures, snapshot config",
        "monitoring alert": "Look for: monitoring setup, alert rules, health check endpoints, metrics exporters",
        "ci cd pipeline": "Look for: CI config files (.github/workflows, .gitlab-ci.yml), build scripts, deploy scripts",
        "dependency vulnerability": "Look for: package.json requirements.txt, lock files, audit commands, Dependabot config",
        "database index": "Look for: CREATE INDEX, db.index(), migration files with add_index, query analysis",
        "pagination": "Look for: page/offset/limit params, cursor-based pagination, paginate() calls",
        "search engine": "Look for: search index config, Elasticsearch mappings, full-text search setup",
        "encryption": "Look for: encryption functions, AES/GCM/RSA usage, key management, at-rest encryption",
        "timezone": "Look for: timezone config, UTC normalization, datetime with tz, pytz/zoneinfo usage",
        "feature flag": "Look for: feature flag config, toggle definitions, A/B test setup, experiment config",
        "cookie consent": "Look for: cookie banner, consent script, GDPR compliance, tracking opt-in",
        "validation input sanitize": "Look for: input validation, sanitization calls, schema validation, type checking",
    }

    detection_hint = "Look for relevant configuration, setup code, and usage patterns in project files."
    for key, hint in hints.items():
        if any(w in topic for w in key.split()):
            detection_hint = hint
            break

    # Find real example from the summary
    sentences = re.split(r'[.!?\n]', summary)
    real_example = ""
    for sentence in sentences:
        s = sentence.strip().lower()
        if any(w in s for w in topic.split()):
            real_example = sentence.strip()
            break
    if not real_example:
        real_example = f"Session involved: {topic}"

    return {
        "category": category,
        "check_name": check_name,
        "severity": "medium",
        "description": f"No check exists for: {topic}",
        "detection_hint": detection_hint,
        "real_example": real_example,
    }


def analyze_session_gaps(
    session_summary: str,
    project_type: str,
    files: dict[str, str] | None = None,
) -> dict:
    """Compare session actions against existing MCP checks to find coverage gaps."""
    files = files or {}

    # 1. Extract what the session did
    session_topics = _extract_actions(session_summary, files)

    # 2. For each topic, find which existing checks cover it
    existing_coverage: list[dict[str, str | list[str]]] = []
    gaps: list[dict[str, str]] = []

    for topic in session_topics:
        covering = _find_covering_checks(topic)
        if covering:
            existing_coverage.append({"topic": topic, "covered_by": covering})
        else:
            gap = _suggest_gap(topic, session_summary)
            if gap and gap["check_name"] not in {g["check_name"] for g in gaps}:
                gaps.append(gap)

    # 3. Suggest new reviewer modules if 3+ gaps share a category
    category_counts: dict[str, int] = {}
    for gap in gaps:
        category_counts[gap["category"]] = category_counts.get(gap["category"], 0) + 1

    suggested_new_tools: list[dict[str, str]] = []
    for cat, count in category_counts.items():
        if count >= 3:
            suggested_new_tools.append({
                "suggested_reviewer": f"review_{cat.replace(' ', '_')}",
                "reason": f"{count} gaps found in '{cat}' category — enough for a dedicated reviewer module",
                "gap_codes": [g["check_name"] for g in gaps if g["category"] == cat],
            })

    return {
        "session_topics_detected": session_topics,
        "existing_coverage": existing_coverage,
        "gaps": gaps,
        "gap_count": len(gaps),
        "suggested_new_tools": suggested_new_tools,
        "summary": (
            f"Detected {len(session_topics)} session topics. "
            f"{len(existing_coverage)} covered by existing checks. "
            f"{len(gaps)} gaps found."
        ),
    }
