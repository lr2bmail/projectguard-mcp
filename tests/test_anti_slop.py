from projectguard_mcp.reviewers.anti_slop import review_project_text


def test_lorem_ipsum_detected():
    result = review_project_text("Lorem ipsum dolor sit amet consectetur adipiscing elit.")
    codes = {f["code"] for f in result["findings"]}
    assert "LOREM_IPSUM" in codes


def test_fake_social_proof_detected():
    result = review_project_text("Trusted by thousands of users worldwide. Industry-leading platform.")
    codes = {f["code"] for f in result["findings"]}
    assert "FAKE_SOCIAL_PROOF" in codes


def test_generic_ai_copy_detected():
    result = review_project_text("Unlock your potential with our seamless experience. Transform your workflow today.")
    codes = {f["code"] for f in result["findings"]}
    assert "GENERIC_AI_COPY" in codes


def test_ai_boilerplate_detected():
    result = review_project_text("In today's fast-paced world, it's worth noting that the power of AI is a game-changer.")
    codes = {f["code"] for f in result["findings"]}
    assert "AI_BOILERPLATE_PHRASES" in codes


def test_fake_metrics_detected():
    result = review_project_text("Our platform provides 99.9% uptime with 10x faster performance and proven results.")
    codes = {f["code"] for f in result["findings"]}
    assert "FAKE_METRICS" in codes


def test_stub_code_detected():
    result = review_project_text("def process():\n    pass\n")
    codes = {f["code"] for f in result["findings"]}
    assert "STUB_CODE" in codes


def test_placeholder_brackets_detected():
    result = review_project_text("Welcome to [Your Company] - the best [Product Name] for your needs.")
    codes = {f["code"] for f in result["findings"]}
    assert "PLACEHOLDER_BRACKETS" in codes


def test_text_too_short():
    result = review_project_text("Short")
    codes = {f["code"] for f in result["findings"]}
    assert "TEXT_TOO_SHORT" in codes


def test_clean_text_passes():
    result = review_project_text(
        "TaskFlow is a project management tool for remote teams. "
        "It provides Kanban boards, time tracking, and sprint planning. "
        "Built with Flask and PostgreSQL, deployed on Railway. "
        "Pricing starts at $8 per user per month with a 14-day free trial."
    )
    assert result["approved"] is True
    assert result["score"] >= 85
