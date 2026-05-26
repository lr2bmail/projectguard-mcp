from __future__ import annotations

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings

REQUIRED_LEGAL_PAGES = {
    "terms": "Terms of Service",
    "privacy": "Privacy Policy",
    "refund": "Refund Policy",
    "contact": "Contact/support page",
}

ABUSE_PAGES = {
    "aup": "Acceptable Use Policy",
    "fair_usage": "Fair Usage Policy",
}


def review_paid_launch_readiness(
    project_type: str,
    legal_pages: list[str] | None = None,
    signup_audit_fields: list[str] | None = None,
    payment_fields: list[str] | None = None,
    order_confirmation_fields: list[str] | None = None,
    ledger_fields: list[str] | None = None,
    admin_features: list[str] | None = None,
    processors: list[str] | None = None,
    abuse_sensitive: bool = False,
) -> dict:
    """Review minimum paid-launch readiness for SaaS/digital services.

    This is an operational readiness check, not legal/tax advice.
    """
    findings: list[Finding] = []
    legal = {item.lower().strip() for item in legal_pages or []}
    signup = {item.lower().strip() for item in signup_audit_fields or []}
    payment = {item.lower().strip() for item in payment_fields or []}
    order = {item.lower().strip() for item in order_confirmation_fields or []}
    ledger = {item.lower().strip() for item in ledger_fields or []}
    admin = {item.lower().strip() for item in admin_features or []}
    processors_set = {item.lower().strip() for item in processors or []}

    for key, label in REQUIRED_LEGAL_PAGES.items():
        if key not in legal:
            findings.append(Finding(
                code=f"MISSING_{key.upper()}_PAGE",
                severity="high",
                message=f"Missing required legal/support page: {label}.",
                recommendation="Add public legal/support pages linked from footer, signup, and checkout where relevant.",
            ))

    if abuse_sensitive:
        for key, label in ABUSE_PAGES.items():
            if key not in legal:
                findings.append(Finding(
                    code=f"MISSING_{key.upper()}_PAGE",
                    severity="high",
                    message=f"Missing abuse-sensitive service page: {label}.",
                    recommendation="Add visible AUP/Fair Usage rules for proxy/VPN/email/scanner/automation products.",
                ))

    required_signup = {"user_id", "policy_versions", "timestamp", "ip_address", "user_agent", "source_action"}
    missing_signup = sorted(required_signup - signup)
    if missing_signup:
        findings.append(Finding(
            code="SIGNUP_AGREEMENT_AUDIT_INCOMPLETE",
            severity="high",
            message=f"Signup agreement audit is missing: {', '.join(missing_signup)}.",
            recommendation="Store explicit unchecked-checkbox agreement with policy versions and request metadata.",
        ))

    required_payment = {"provider", "provider_payment_id", "invoice_id", "user_id", "amount", "currency", "status_history", "webhook_event_ids"}
    missing_payment = sorted(required_payment - payment)
    if missing_payment:
        findings.append(Finding(
            code="PAYMENT_RECORDS_INCOMPLETE",
            severity="high",
            message=f"Payment records are missing: {', '.join(missing_payment)}.",
            recommendation="Store durable payment/session/webhook records before redirecting to providers.",
        ))

    required_order = {"total_cost", "balance_before", "balance_after", "delivery_state", "service_limits", "aup_reminder"}
    missing_order = sorted(required_order - order)
    if missing_order:
        findings.append(Finding(
            code="ORDER_CONFIRMATION_INCOMPLETE",
            severity="medium",
            message=f"Order confirmation is missing: {', '.join(missing_order)}.",
            recommendation="Show user exactly what they are buying before order creation.",
        ))

    required_ledger = {"user_id", "amount", "before_balance", "after_balance", "reason", "related_id", "timestamp"}
    missing_ledger = sorted(required_ledger - ledger)
    if missing_ledger:
        findings.append(Finding(
            code="BALANCE_LEDGER_INCOMPLETE",
            severity="high",
            message=f"Balance ledger is missing: {', '.join(missing_ledger)}.",
            recommendation="Every balance change needs a ledger row for accounting and disputes.",
        ))

    required_admin = {"payments_csv", "invoices_csv", "refunds_csv", "ledger_csv", "refund_reason"}
    missing_admin = sorted(required_admin - admin)
    if missing_admin:
        findings.append(Finding(
            code="ADMIN_ACCOUNTING_EXPORTS_INCOMPLETE",
            severity="medium",
            message=f"Admin/accounting features are missing: {', '.join(missing_admin)}.",
            recommendation="Add basic exports and refund/audit fields before public paid launch.",
        ))

    if not processors_set and any(payment):
        findings.append(Finding(
            code="PROCESSORS_NOT_LISTED",
            severity="medium",
            message="Payment/data processors are not listed for privacy documentation.",
            recommendation="List Stripe/PayPal/NOWPayments/email/hosting/analytics processors used by the system.",
        ))

    score = score_from_findings(findings)
    approved_beta = score >= 70
    approved_public = approval_from_score(score, 88)

    return ReviewResult(
        approved=approved_public,
        score=score,
        findings=findings,
        summary=(
            "Paid launch readiness passed." if approved_public
            else "Paid launch is not fully ready; beta may be acceptable only if blocking issues are understood."
        ),
        metadata={
            "project_type": project_type,
            "approved_for_beta": approved_beta,
            "approved_for_public_paid_launch": approved_public,
            "note": "Operational readiness check only; lawyer/accountant should confirm final policies and tax treatment.",
        },
    ).to_dict()
