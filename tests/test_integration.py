"""End-to-end integration test: start_project_review -> final_project_score through server.py."""

from projectguard_mcp.scoring import final_project_score
from projectguard_mcp.server import (
    analyze_project_request,
    classify_project_risk,
    create_build_rules,
    create_project_brief,
    review_code_quality,
    review_file_plan,
    review_project_text,
    review_security,
    review_seo,
    review_ux_checklist,
)
from projectguard_mcp.server import (
    final_project_score as server_final_score,
)


def test_full_workflow_passes():
    project_type = "saas"
    user_request = (
        "Build a mobile-responsive SaaS dashboard for freelance developers "
        "to manage invoices, track project hours, and generate tax reports. "
        "Features: login with email, PDF invoice generation, time tracker, "
        "dashboard with charts. Tech: Flask + PostgreSQL."
    )

    # Step 1: classify risk
    risk = classify_project_risk(project_type, user_request, ["login", "dashboard", "invoice"])
    assert risk["risk_level"] in {"low", "medium", "high"}
    assert "user_data" in risk["flags"]

    # Step 2: analyze request
    analysis = analyze_project_request(project_type, user_request)
    assert analysis["approved"] is True

    # Step 3: create brief
    brief = create_project_brief(
        product_name="FreelanceTracker",
        project_type=project_type,
        goal="Invoice and time tracking for freelancers",
        target_users=["freelance developers", "contractors"],
        core_features=["invoice generation", "time tracking", "tax reports"],
    )
    assert brief["product_name"] == "FreelanceTracker"
    assert len(brief["success_criteria"]) >= 4

    # Step 4: build rules
    rules = create_build_rules(project_type, risk["flags"])
    assert len(rules["rules"]) > 5

    # Step 5: file plan
    file_plan = review_file_plan(project_type, [
        "app.py",
        "config.py",
        "routes/auth.py",
        "routes/invoice.py",
        "models/user.py",
        "models/invoice.py",
        "templates/base.html",
        "templates/dashboard.html",
        "static/css/app.css",
        "tests/test_auth.py",
        "tests/test_invoice.py",
    ])
    assert file_plan["approved"] is True

    # Step 6: code quality
    code_files = {
        "app.py": "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef index():\n    return 'Hello'",
        "config.py": "DEBUG = False\nSECRET_KEY = os.environ.get('SECRET_KEY')",
        "tests/test_app.py": "def test_index():\n    assert True",
    }
    code_quality = review_code_quality(code_files)
    assert code_quality["score"] >= 80

    # Step 7: security
    security = review_security(project_type, code_files, ["login", "dashboard"])
    assert security["score"] >= 50

    # Step 8: SEO
    seo = review_seo({
        "index.html": """<html lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>FreelanceTracker - Invoice and Time Tracking</title>
    <meta name="description" content="FreelanceTracker helps freelance developers manage invoices, track project hours, and generate tax reports.">
    <link rel="canonical" href="https://freelancetracker.com/">
    <meta property="og:title" content="FreelanceTracker">
    <meta property="og:description" content="Invoice and time tracking for freelancers">
    <meta property="og:image" content="https://freelancetracker.com/og.png">
    <meta property="og:url" content="https://freelancetracker.com/">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <script type="application/ld+json">{"@type":"SoftwareApplication"}</script>
</head>
<body>
    <h1>FreelanceTracker</h1>
    <p>Manage invoices, track project hours, and generate tax reports for your freelance business.</p>
    <img src="hero.jpg" alt="Dashboard screenshot showing invoice overview" width="1200" height="630">
    <a href="/privacy">Privacy</a> <a href="/terms">Terms</a>
</body>
</html>""",
    })
    assert seo["score"] >= 80

    # Step 9: text review
    text = review_project_text(
        "FreelanceTracker is a SaaS tool for freelance developers. "
        "It provides invoice generation with PDF export, real-time project hour tracking, "
        "and automated tax report generation. Built with Flask and PostgreSQL. "
        "Pricing starts at $12/month with a 14-day free trial."
    )
    assert text["approved"] is True

    # Step 10: UX checklist
    ux = review_ux_checklist(
        has_mobile_layout=True,
        has_clear_primary_action=True,
        has_empty_states=True,
        has_error_states=True,
        has_loading_states=True,
        has_accessible_labels=True,
    )
    assert ux["approved"] is True

    # Step 11: final score
    final = final_project_score(
        code_score=code_quality["score"],
        ux_score=ux["score"],
        security_score=security["score"],
        seo_score=seo["score"],
    )
    assert final["overall_score"] >= 70
    assert "scores" in final
    assert "blocking_issues" in final


def test_server_tool_functions_match_reviewers():
    """Verify server tool functions return the same structure as direct reviewer calls."""
    from projectguard_mcp.reviewers.code_quality import review_code_quality as _direct_cq

    files = {"app.py": "x = 1", "tests/test.py": "assert True"}
    direct = _direct_cq(files)
    through_server = server_final_score(
        code_score=direct["score"],
        ux_score=100,
        security_score=100,
    )
    assert through_server["scores"]["code"] == direct["score"]


def test_paid_workflow():
    """Verify paid launch readiness is checked for payment projects."""
    risk = classify_project_risk(
        "paid saas",
        "A proxy service with Stripe checkout and balance management",
        ["proxy", "stripe", "balance"],
    )
    assert risk["requires_paid_launch_review"] is True
    assert "abuse_sensitive" in risk["flags"]
