from projectguard_mcp.reviewers.paid_launch import review_paid_launch_readiness


def test_paid_launch_fails_without_records():
    result = review_paid_launch_readiness(project_type="paid proxy saas", abuse_sensitive=True)
    assert result["approved"] is False
    codes = {f["code"] for f in result["findings"]}
    assert "SIGNUP_AGREEMENT_AUDIT_INCOMPLETE" in codes
    assert "BALANCE_LEDGER_INCOMPLETE" in codes


def test_paid_launch_passes_with_minimum_fields():
    result = review_paid_launch_readiness(
        project_type="paid proxy saas",
        legal_pages=["terms", "privacy", "refund", "contact", "aup", "fair_usage"],
        signup_audit_fields=["user_id", "policy_versions", "timestamp", "ip_address", "user_agent", "source_action"],
        payment_fields=["provider", "provider_payment_id", "invoice_id", "user_id", "amount", "currency", "status_history", "webhook_event_ids"],
        order_confirmation_fields=["total_cost", "balance_before", "balance_after", "delivery_state", "service_limits", "aup_reminder"],
        ledger_fields=["user_id", "amount", "before_balance", "after_balance", "reason", "related_id", "timestamp"],
        admin_features=["payments_csv", "invoices_csv", "refunds_csv", "ledger_csv", "refund_reason"],
        processors=["stripe", "cloudflare", "hosting"],
        abuse_sensitive=True,
    )
    assert result["approved"] is True
    assert result["score"] >= 88
