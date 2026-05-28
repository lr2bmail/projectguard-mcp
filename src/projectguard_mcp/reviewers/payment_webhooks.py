from __future__ import annotations

import re

from projectguard_mcp.models import Finding, ReviewResult, approval_from_score, score_from_findings

PROVIDER_WORDS = ["stripe", "paypal", "nowpayments", "paddle", "lemonsqueezy", "checkout"]
PAYMENT_CONTEXT_WORDS = ["payment", "checkout", "invoice", "refund", "balance", "wallet", "add funds"]
WEBHOOK_WORDS = ["webhook", "event", "payment_intent", "checkout.session", "ipn"]
SIGNATURE_WORDS = ["signature", "construct_event", "webhooksecret", "verify", "verify_signature", "x-paypal"]
IDEMPOTENCY_WORDS = ["idempot", "event_id", "provider_event_id", "webhook_event_id", "processed_events", "dedupe"]
AMOUNT_WORDS = ["amount", "currency", "total", "price", "paid_amount"]
BALANCE_WORDS = ["balance", "wallet", "credit", "add_funds", "add funds"]
REFUND_WORDS = ["refund", "chargeback", "dispute", "reversal"]
SUCCESS_REDIRECT_PATTERNS = [
    r"success(_|-)?url",
    r"payment_success",
    r"checkout_success",
    r"/success",
]


def _blob(files: dict[str, str]) -> str:
    return "\n".join(files.values()).lower()


def _has_any(text: str, words: list[str]) -> bool:
    return any(word.lower() in text for word in words)


def review_payment_webhook_security(
    project_type: str,
    files: dict[str, str] | None = None,
    features: list[str] | None = None,
) -> dict:
    """Review defensive payment webhook handling for paid SaaS/account-balance flows."""
    files = files or {}
    findings: list[Finding] = []
    all_text = _blob(files)
    context = " ".join([project_type or "", " ".join(features or []), all_text]).lower()
    payment_context = _has_any(context, PROVIDER_WORDS + PAYMENT_CONTEXT_WORDS)

    if not payment_context:
        findings.append(Finding(
            code="NO_PAYMENT_CONTEXT_DETECTED",
            severity="info",
            message="No obvious payment, checkout, invoice, refund, or balance context was detected.",
            recommendation="Run this review when the project accepts payments or changes account balance.",
        ))

    if payment_context and not _has_any(all_text, WEBHOOK_WORDS):
        findings.append(Finding(
            code="PAYMENT_WEBHOOK_NOT_VISIBLE",
            severity="critical",
            message="Payment context detected but no webhook handler is visible.",
            recommendation="Do not trust success redirects alone; verify provider webhook events server-side.",
        ))

    if _has_any(all_text, WEBHOOK_WORDS) and not _has_any(all_text, SIGNATURE_WORDS):
        findings.append(Finding(
            code="WEBHOOK_SIGNATURE_NOT_VISIBLE",
            severity="critical",
            message="Webhook handling is visible but signature verification is not.",
            recommendation="Verify provider webhook signatures before updating orders, invoices, or balances.",
        ))

    if payment_context and not _has_any(all_text, IDEMPOTENCY_WORDS):
        findings.append(Finding(
            code="PAYMENT_IDEMPOTENCY_NOT_VISIBLE",
            severity="high",
            message="No visible duplicate-event/idempotency handling for payment webhooks.",
            recommendation="Store provider event IDs and ignore duplicate webhook events.",
        ))

    if payment_context and not _has_any(all_text, AMOUNT_WORDS):
        findings.append(Finding(
            code="PAYMENT_AMOUNT_RECHECK_NOT_VISIBLE",
            severity="high",
            message="No visible server-side amount/currency verification for payment events.",
            recommendation="Match provider amount, currency, user, invoice, and order IDs before granting service/balance.",
        ))

    if _has_any(all_text, BALANCE_WORDS):
        if "before_balance" not in all_text or "after_balance" not in all_text:
            findings.append(Finding(
                code="BALANCE_LEDGER_FIELDS_NOT_VISIBLE",
                severity="high",
                message="Account balance flow detected without visible before/after ledger fields.",
                recommendation="Store every balance change with user, before/after balance, reason, related payment/order, and timestamp.",
            ))
        if re.search(r"balance\s*(\+=|=\s*balance\s*\+)", all_text) and not _has_any(all_text, SIGNATURE_WORDS):
            findings.append(Finding(
                code="BALANCE_UPDATED_WITHOUT_VISIBLE_WEBHOOK_VERIFICATION",
                severity="critical",
                message="Balance appears to be updated without visible webhook signature verification.",
                recommendation="Only update balance after verified provider webhook and idempotency checks.",
            ))

    if any(re.search(pattern, all_text, re.I) for pattern in SUCCESS_REDIRECT_PATTERNS):
        if not _has_any(all_text, WEBHOOK_WORDS):
            findings.append(Finding(
                code="SUCCESS_REDIRECT_TRUSTED_AS_PAYMENT_RISK",
                severity="critical",
                message="Payment success redirect exists without visible webhook verification.",
                recommendation="Use success pages only for UX; use verified webhooks as the source of truth.",
            ))

    if payment_context and not _has_any(all_text, REFUND_WORDS):
        findings.append(Finding(
            code="REFUND_DISPUTE_FLOW_NOT_VISIBLE",
            severity="medium",
            message="No visible refund/dispute/chargeback state handling for payment flow.",
            recommendation="Store refund, dispute, and chargeback states with admin reason and user notification history.",
        ))

    score = score_from_findings(findings)
    return ReviewResult(
        approved=approval_from_score(score, 88),
        score=score,
        findings=findings,
        summary="Payment webhook security passed." if score >= 88 else "Payment webhook security needs fixes.",
        metadata={
            "project_type": project_type,
            "payment_context_detected": payment_context,
            "frameworks": ["OWASP ASVS", "PCI-DSS design hygiene", "SaaS payment operations"],
        },
    ).to_dict()
