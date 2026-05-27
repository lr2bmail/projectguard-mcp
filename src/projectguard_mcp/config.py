from __future__ import annotations

# -- Severity weights (used by models.py score_from_findings) --
SEVERITY_WEIGHTS: dict[str, int] = {
    "info": 0,
    "low": 4,
    "medium": 8,
    "high": 15,
    "critical": 25,
}

# -- Approval thresholds per reviewer --
APPROVAL_THRESHOLDS: dict[str, int] = {
    "default": 85,
    "file_plan": 82,
    "project_request": 80,
    "paid_launch_public": 88,
    "paid_launch_beta": 70,
    "final_overall": 85,
}

# -- Scoring weights for final_project_score --
SCORING_WEIGHTS_WITH_PAID: dict[str, float] = {
    "code": 0.30,
    "ux": 0.25,
    "security": 0.25,
    "seo": 0.10,
    "paid_launch": 0.10,
}

SCORING_WEIGHTS_WITHOUT_PAID: dict[str, float] = {
    "code": 0.35,
    "ux": 0.30,
    "security": 0.25,
    "seo": 0.10,
}

# -- Blocking thresholds --
BLOCKING_THRESHOLDS: dict[str, int] = {
    "code_score": 75,
    "security_score": 80,
    "paid_launch_score": 70,
}

# -- Anti-slop patterns: code -> (regex, severity) --
ANTI_SLOP_PATTERNS: dict[str, tuple[str, str]] = {
    "LOREM_IPSUM": (r"lorem ipsum|dolor sit amet", "medium"),
    "PLACEHOLDER_TEXT": (r"placeholder|coming soon|under construction|todo\b|fixme\b|dummy data", "medium"),
    "FAKE_SOCIAL_PROOF": (r"trusted by thousands|millions of users|world.?class|industry.?leading|#1\b", "medium"),
    "GENERIC_AI_COPY": (
        r"unlock your potential|seamless experience|revolutionize|transform your workflow|cutting-edge solution",
        "medium",
    ),
    "FAKE_INTEGRATION": (r"integrates with (stripe|paypal|openai|slack|github|google)", "high"),
}

# -- Additional slop patterns (commit 4) --
ADDITIONAL_SLOP_PATTERNS: dict[str, tuple[str, str]] = {
    "AI_BOILERPLATE_PHRASES": (
        r"in today'?s fast.?paced|it'?s worth noting|rest assured|the power of|"
        r"at the end of the day|in this (?:article|guide|post) we(?:'ll| will)|"
        r"game.?changer|next.?level|supercharge your|"
        r"elevate your|empower(?:ing)? (?:your|you|users)|future.?proof|"
        r"stay ahead of the curve|leverage (?:the power of|our)",
        "medium",
    ),
    "FAKE_METRICS": (
        r"99\.9%\s*(?:uptime|availability|reliability)|10x\s*(?:faster|improvement|growth)|"
        r"proven\s*results|100%\s*(?:guarantee|secure|reliable|free)|"
        r"(?:thousands|millions)\s+of\s+(?:happy\s+)?(?:users|customers|clients)",
        "high",
    ),
    "STUB_CODE": (
        r"(?:^|\n)\s*(?:pass|NotImplemented|raise\s+NotImplementedError|\.\.\.)\s*(?:\n|$)",
        "high",
    ),
    "PLACEHOLDER_BRACKETS": (
        r"\[(?:Your?\s+)?(?:Company|Product|Name|Service|Brand|App|Tool|URL|Link|Email|Phone)\s*\]|"
        r"\bTBD\b",
        "high",
    ),
}

# -- Content thresholds --
MIN_TEXT_LENGTH: int = 80
MIN_WORD_COUNT: int = 25
MIN_FILES_FOR_TEST_CHECK: int = 3
LARGE_FILE_LINE_THRESHOLD: int = 500
EMPTY_SECTION_MIN_WORDS: int = 5
EMPTY_SECTION_MAX_HEADING_LEN: int = 200
COMMENTED_CODE_MIN_LINES: int = 3
RISK_FLAGS_FOR_HIGH_RISK: int = 3
DEFAULT_PAGE_WORD_COUNT: int = 300

# -- Secret detection patterns --
SECRET_PATTERNS: list[str] = [
    r"sk_live_[A-Za-z0-9_\-]+",
    r"xox[baprs]-[A-Za-z0-9\-]+",
    r"AKIA[0-9A-Z]{16}",
    r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]",
]

# -- SEO thresholds --
SEO_TITLE_MIN_LENGTH: int = 30
SEO_TITLE_MAX_LENGTH: int = 70
SEO_META_DESC_MIN_LENGTH: int = 100
SEO_META_DESC_MAX_LENGTH: int = 170

# -- Page type word count minimums --
PAGE_WORD_COUNT_MINIMUMS: dict[str, int] = {
    "homepage": 500,
    "service": 800,
    "blog": 1500,
    "product": 300,
}

# -- Deprecated/restricted schema types --
DEPRECATED_SCHEMA_TYPES: list[str] = [
    "HowTo",
    "FAQPage",
    "SpecialAnnouncement",
]

# -- Security patterns --
SQL_INJECTION_PATTERN: str = r"SELECT\s+.+\s+FROM\s+.+\+"

# -- Debug/local URL patterns --
LOCAL_URL_PATTERNS: list[str] = [
    r"http://localhost[:\d]",
    r"https?://127\.0\.0\.1",
    r"https?://0\.0\.0\.0",
]

# -- Exclamation spam threshold (marks per 100 words) --
EXCLAMATION_SPAM_THRESHOLD: float = 5.0
