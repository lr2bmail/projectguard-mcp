"""Edge-case tests: None inputs, empty dicts, boundary values."""
from __future__ import annotations

from projectguard_mcp.reviewers.anti_slop import review_project_text
from projectguard_mcp.reviewers.code_quality import review_code_quality
from projectguard_mcp.reviewers.file_plan import review_file_plan
from projectguard_mcp.reviewers.project_request import analyze_project_request
from projectguard_mcp.reviewers.security import review_security
from projectguard_mcp.reviewers.seo import review_seo
from projectguard_mcp.utils import (
    contains_any,
    count_words,
    file_ext,
    normalize_text,
    safe_path_parts,
    strip_html_tags,
)

# -- utils edge cases --


def test_contains_any_empty():
    assert contains_any("", ["test"]) is False


def test_contains_any_none_text():
    assert contains_any(None, ["test"]) is False


def test_contains_any_empty_keywords():
    assert contains_any("hello world", []) is False


def test_count_words_empty():
    assert count_words("") == 0


def test_count_words_none():
    assert count_words(None) == 0


def test_safe_path_parts_empty():
    assert safe_path_parts("") == ()


def test_safe_path_parts_none():
    assert safe_path_parts(None) == ()


def test_file_ext_no_extension():
    assert file_ext("README") == ""


def test_file_ext_nested():
    assert file_ext("src/app.test.ts") == "ts"


def test_file_ext_uppercase():
    assert file_ext("component.HTML") == "html"


def test_strip_html_tags_empty():
    assert strip_html_tags("") == ""


def test_strip_html_tags_none():
    assert strip_html_tags(None) == ""


def test_strip_html_tags_no_tags():
    assert strip_html_tags("plain text") == "plain text"


def test_normalize_text_none():
    assert normalize_text(None) == ""


def test_normalize_text_whitespace():
    assert normalize_text("  hello  ") == "hello"


# -- reviewer edge cases --


def test_code_quality_empty_files():
    result = review_code_quality({})
    assert result["approved"] is False
    codes = {f["code"] for f in result["findings"]}
    assert "NO_CODE" in codes


def test_security_empty_files():
    result = review_security("web app", {})
    assert isinstance(result["score"], int)
    codes = {f["code"] for f in result["findings"]}
    assert "NO_FILES" in codes


def test_seo_empty_pages():
    result = review_seo({})
    assert isinstance(result["score"], int)
    codes = {f["code"] for f in result["findings"]}
    assert "NO_PUBLIC_PAGES" in codes


def test_file_plan_empty():
    result = review_file_plan("web app", [])
    assert result["approved"] is False
    codes = {f["code"] for f in result["findings"]}
    assert "NO_FILES" in codes


def test_project_request_empty():
    result = analyze_project_request("web app", "")
    codes = {f["code"] for f in result["findings"]}
    assert "REQUEST_TOO_SHORT" in codes


def test_project_request_none():
    result = analyze_project_request("web app", None)
    codes = {f["code"] for f in result["findings"]}
    assert "REQUEST_TOO_SHORT" in codes


def test_anti_slop_empty():
    result = review_project_text("")
    assert isinstance(result["score"], int)


def test_anti_slop_none():
    result = review_project_text(None)
    assert isinstance(result["score"], int)


# -- boundary value tests --


def test_sql_injection_fstring():
    files = {"app.py": 'query = f"SELECT * FROM users WHERE id={user_id}"'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "POSSIBLE_SQL_INJECTION" in codes


def test_sql_injection_concat():
    files = {"app.py": 'query = "SELECT * FROM users WHERE id=" + user_id'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "POSSIBLE_SQL_INJECTION" in codes


def test_security_credential_in_test_not_flagged():
    files = {"test_config.py": 'password = "testpass123"'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "HARDCODED_CREDENTIALS" not in codes


def test_security_credential_in_env_example_not_flagged():
    files = {".env.example": 'DATABASE_URL = "postgresql://user:pass@localhost/db"'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "HARDCODED_CREDENTIALS" not in codes


def test_seo_canonical_http_flagged():
    html = '<html><head><title>Test</title><link rel="canonical" href="http://example.com/"></head><body><h1>X</h1></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "CANONICAL_NOT_HTTPS" in codes


def test_seo_multiple_canonical_flagged():
    html = '<html><head><title>Test</title><link rel="canonical" href="https://a.com/"><link rel="canonical" href="https://b.com/"></head><body><h1>X</h1></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "MULTIPLE_CANONICAL" in codes


def test_seo_missing_og_image_flagged():
    html = '<html><head><title>Test</title><meta property="og:title" content="T"></head><body><h1>X</h1></body></html>'
    result = review_seo({"index.html": html})
    codes = {f["code"] for f in result["findings"]}
    assert "INCOMPLETE_OG_TAGS" in codes


def test_code_quality_secret_not_flagged_in_test():
    files = {"tests/test_api.py": 'key = "sk_live_abcdef1234567890"'}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "POSSIBLE_SECRET" not in codes


def test_security_framework_xss_with_sanitize_not_flagged():
    files = {"app.jsx": 'import DOMPurify from "dompurify";\n<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(data)}} />'}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "FRAMEWORK_XSS_PATTERN" not in codes


def test_security_weak_random_not_crypto_not_flagged():
    files = {"game.py": "import random\nx = random.randint(1, 100)"}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "WEAK_CRYPTO" not in codes


def test_code_quality_ambiguous_button_flagged():
    files = {"page.html": '<html><body><button>Click</button></body></html>'}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "AMBIGUOUS_BUTTON" in codes


def test_code_quality_disabled_button_not_flagged():
    files = {"page.html": '<html><body><button disabled>Coming soon</button></body></html>'}
    result = review_code_quality(files)
    codes = {f["code"] for f in result["findings"]}
    assert "AMBIGUOUS_BUTTON" not in codes


def test_security_insecure_session_flagged():
    files = {"app.py": "app.config['SESSION_COOKIE_SECURE'] = False"}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "INSECURE_SESSION_CONFIG" in codes


def test_security_csp_missing_on_html_flagged():
    files = {"index.html": "<html><head><title>Test</title></head><body></body></html>"}
    result = review_security("web app", files)
    codes = {f["code"] for f in result["findings"]}
    assert "MISSING_CSP" in codes


def test_file_plan_unsafe_path_flagged():
    result = review_file_plan("web app", ["../../../etc/passwd"])
    codes = {f["code"] for f in result["findings"]}
    assert "UNSAFE_PATH" in codes
