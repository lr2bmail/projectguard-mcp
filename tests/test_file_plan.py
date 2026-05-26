from projectguard_mcp.reviewers.file_plan import review_file_plan


def test_weak_file_plan_fails_for_saas():
    result = review_file_plan("saas", ["index.html", "style.css"])
    assert result["approved"] is False
    codes = {f["code"] for f in result["findings"]}
    assert "FILE_PLAN_TOO_SMALL" in codes


def test_reasonable_flask_saas_file_plan_scores_better():
    result = review_file_plan(
        "flask saas",
        [
            "app.py",
            "routes/billing.py",
            "models/user.py",
            "templates/base.html",
            "templates/dashboard.html",
            "static/css/app.css",
            "tests/test_billing.py",
        ],
    )
    assert result["score"] >= 82
