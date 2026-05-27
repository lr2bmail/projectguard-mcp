from projectguard_mcp.reviewers.project_request import analyze_project_request, create_project_brief


def test_short_request_flagged():
    result = analyze_project_request("web app", "Build a website")
    codes = {f["code"] for f in result["findings"]}
    assert "REQUEST_TOO_SHORT" in codes


def test_unclear_target_users():
    result = analyze_project_request(
        "web app",
        "Build a system for managing inventory with barcode scanning and stock alerts",
    )
    codes = {f["code"] for f in result["findings"]}
    assert "TARGET_USERS_UNCLEAR" in codes


def test_unclear_core_features():
    result = analyze_project_request(
        "web app",
        "A platform for users and customers to manage their accounts, update their profiles, "
        "and interact with each other through messaging and notifications",
    )
    codes = {f["code"] for f in result["findings"]}
    assert "CORE_FEATURES_UNCLEAR" in codes


def test_mobile_not_mentioned_for_web_app():
    result = analyze_project_request(
        "web app",
        "Build a dashboard for admin users with login, analytics dashboard, and user management features",
    )
    codes = {f["code"] for f in result["findings"]}
    assert "MOBILE_UX_NOT_MENTIONED" in codes


def test_clone_risk_detected():
    result = analyze_project_request(
        "web app",
        "Make it like Stripe with payment features for customers",
    )
    codes = {f["code"] for f in result["findings"]}
    assert "CLONE_RISK" in codes


def test_detailed_request_passes():
    result = analyze_project_request(
        "web app",
        "Build a mobile-responsive SaaS dashboard for freelance developers "
        "to manage invoices, track project hours, and generate tax reports. "
        "Features: login with email, PDF invoice generation, time tracker, "
        "dashboard with charts. Tech: Flask + PostgreSQL.",
    )
    assert result["approved"] is True


def test_create_project_brief_returns_structure():
    brief = create_project_brief(
        product_name="TaskFlow",
        project_type="saas",
        goal="Project management for remote teams",
        target_users=["remote workers", "team leads"],
        core_features=["kanban boards", "time tracking", "sprint planning"],
    )
    assert brief["product_name"] == "TaskFlow"
    assert len(brief["success_criteria"]) > 0
    assert brief["v1_rule"]
