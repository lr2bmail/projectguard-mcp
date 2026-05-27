from projectguard_mcp.reviewers.classifier import classify_project_risk


def test_paid_proxy_project_requires_paid_and_aup_review():
    result = classify_project_risk(
        "paid SaaS",
        "A proxy service with Stripe checkout, add funds balance, invoices, refunds, and admin dashboard.",
        ["IPv6 proxies", "account balance"],
    )
    assert result["risk_level"] == "high"
    assert result["requires_paid_launch_review"] is True
    assert result["requires_aup_review"] is True
    assert "account_balance" in result["flags"]


def test_paid_without_abuse_is_medium():
    result = classify_project_risk(
        "saas",
        "A simple subscription SaaS with Stripe billing",
        ["subscription"],
    )
    assert result["risk_level"] in {"medium", "high"}


def test_low_risk_project():
    result = classify_project_risk(
        "static website",
        "A portfolio page with contact form",
    )
    assert result["risk_level"] == "low"
    assert result["flags"] == []
