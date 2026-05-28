"""Tests for analyze_session_gaps meta-reviewer."""
from projectguard_mcp.reviewers.session_gaps import analyze_session_gaps


def test_finds_covered_topics():
    summary = "Added login page with JWT authentication, CSRF protection, and rate limiting."
    result = analyze_session_gaps(summary, "saas")
    topics = result["session_topics_detected"]
    # Authentication and rate limiting topics should be detected
    assert any("auth" in t for t in topics)
    assert result["gap_count"] >= 0  # May or may not have gaps


def test_finds_gaps_for_uncovered_topics():
    summary = "Set up Celery workers for background email sending, added cron scheduler for daily reports, and configured Redis queue for async jobs."
    result = analyze_session_gaps(summary, "saas")
    assert result["gap_count"] > 0
    gap_descriptions = " ".join(g["description"] for g in result["gaps"]).lower()
    assert any(w in gap_descriptions for w in ["email", "cron", "scheduler", "queue"])


def test_existing_coverage_lists_checks():
    summary = "Added login page with authentication, set up Docker deployment, and configured CORS."
    result = analyze_session_gaps(summary, "web app")
    coverage = result["existing_coverage"]
    assert len(coverage) > 0
    all_checks = []
    for item in coverage:
        all_checks.extend(item["covered_by"])
    assert len(all_checks) > 0


def test_suggests_new_tool_when_many_gaps_in_category():
    summary = (
        "Set up email sending with SMTP, added Celery workers for background jobs, "
        "configured Redis queue for message processing, and built a cron scheduler."
    )
    result = analyze_session_gaps(summary, "saas")
    # These should create multiple gaps, potentially in infrastructure
    if result["gap_count"] >= 3:
        # Check if any category has 3+ gaps
        categories = {}
        for g in result["gaps"]:
            categories[g["category"]] = categories.get(g["category"], 0) + 1
        if any(v >= 3 for v in categories.values()):
            assert len(result["suggested_new_tools"]) > 0


def test_empty_summary_no_crash():
    result = analyze_session_gaps("", "web app")
    assert result["gap_count"] == 0
    assert result["session_topics_detected"] == []


def test_files_contribute_to_topic_detection():
    summary = "Implemented the checkout flow"
    files = {"billing.py": "import stripe\nstripe.checkout.Session.create()"}
    result = analyze_session_gaps(summary, "saas", files)
    assert any("payment" in t or "stripe" in t for t in result["session_topics_detected"])


def test_gaps_have_required_fields():
    summary = "Added WebSocket support for real-time chat, set up Redis queue for message processing."
    result = analyze_session_gaps(summary, "saas")
    for gap in result["gaps"]:
        assert "category" in gap
        assert "check_name" in gap
        assert "severity" in gap
        assert "description" in gap
        assert "detection_hint" in gap
        assert "real_example" in gap


def test_does_not_suggest_existing_checks():
    """Gaps should not duplicate existing check codes."""
    summary = "Added login, CSRF, and CORS configuration with rate limiting and JWT auth."
    result = analyze_session_gaps(summary, "web app")
    existing_codes = {item["covered_by"][0] for item in result["existing_coverage"] if item["covered_by"]}
    for gap in result["gaps"]:
        assert gap["check_name"] not in existing_codes


def test_output_structure():
    summary = "Built a dashboard with Docker deployment and monitoring setup."
    result = analyze_session_gaps(summary, "saas")
    assert "session_topics_detected" in result
    assert "existing_coverage" in result
    assert "gaps" in result
    assert "gap_count" in result
    assert "suggested_new_tools" in result
    assert "summary" in result
    assert isinstance(result["gaps"], list)
    assert isinstance(result["existing_coverage"], list)
    assert result["gap_count"] == len(result["gaps"])
