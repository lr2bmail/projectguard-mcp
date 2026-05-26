from __future__ import annotations

COMMON_BUILD_RULES = [
    "Do not create fake features, fake integrations, fake testimonials, or fake metrics.",
    "Do not use lorem ipsum, TODO-only sections, or meaningless filler text as final content.",
    "Do not create placeholder buttons unless they are disabled or clearly labeled as unavailable.",
    "Do not expose secrets, API keys, tokens, or credentials in source code.",
    "Do not rewrite unrelated files or change unrelated app behavior.",
    "Use a clear file structure with separation between UI, routes, business logic, and configuration.",
    "Add validation for all user inputs.",
    "Handle loading, empty, success, and error states.",
    "Make the UI mobile responsive.",
    "Keep the MVP simple and useful before adding advanced features.",
]

WEBSITE_RULES = [
    "Every public page needs a unique title and meta description.",
    "Homepage must explain the product value in the first screen.",
    "Navigation must expose core pages without hiding important flows.",
    "Footer must include Contact, Privacy Policy, and Terms where relevant.",
    "Use semantic HTML and accessible labels for forms.",
]

SAAS_RULES = [
    "Define real user flows before coding screens.",
    "Do not create screens that are not connected to real actions.",
    "Protect admin routes and sensitive actions.",
    "Store durable audit records for payment, order, refund, and admin events.",
    "Use least-privilege roles for admin/customer actions.",
]

PAID_LAUNCH_RULES = [
    "Paid services need Terms, Privacy Policy, Refund Policy, Contact/support, and where relevant AUP/Fair Usage pages.",
    "Signup must use an unchecked agreement checkbox and store accepted policy versions with timestamp, IP, and user agent.",
    "Payment/add-funds flow must show amount, currency, method, what the user is buying, and refund-policy link before redirecting to provider.",
    "Order confirmation must show quantity, duration, total cost, balance before/after, delivery state, and service limitations.",
    "Every balance change must have a ledger row with before/after amount, reason, related IDs, and timestamp.",
    "Admin needs basic CSV exports for payments, invoices, refunds, and balance ledger before public paid launch.",
]

ABUSE_SENSITIVE_RULES = [
    "Add a visible Acceptable Use Policy for abuse-sensitive products.",
    "Ban spam, phishing, credential stuffing, payment fraud, malware, DDoS, unauthorized access, and illegal activity.",
    "Add abuse reporting contact and admin tools to suspend users/orders and record abuse notes.",
]


def rules_for_project(project_type: str, risk_flags: list[str] | None = None) -> list[str]:
    flags = set(risk_flags or [])
    pt = project_type.lower()
    rules = list(COMMON_BUILD_RULES)
    if any(word in pt for word in ["website", "seo", "landing", "tools"]):
        rules.extend(WEBSITE_RULES)
    if any(word in pt for word in ["saas", "app", "dashboard", "api", "admin"]):
        rules.extend(SAAS_RULES)
    if "paid" in flags or "payment" in flags or "account_balance" in flags:
        rules.extend(PAID_LAUNCH_RULES)
    if "abuse_sensitive" in flags:
        rules.extend(ABUSE_SENSITIVE_RULES)
    return rules
