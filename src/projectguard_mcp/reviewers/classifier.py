from __future__ import annotations

from projectguard_mcp.utils import contains_any

PAID_KEYWORDS = [
    "paid", "checkout", "stripe", "paypal", "nowpayments", "crypto", "invoice", "billing",
    "subscription", "add funds", "balance", "refund", "order", "credit card", "payment",
]

ABUSE_SENSITIVE_KEYWORDS = [
    "proxy", "proxies", "vpn", "email api", "smtp", "bulk email", "scanner", "security scanner",
    "scraper", "automation", "account creator", "sms", "hosting", "api keys",
]

USER_DATA_KEYWORDS = [
    "login", "signup", "users", "accounts", "profile", "dashboard", "admin", "password",
]

DEPLOYMENT_KEYWORDS = ["deploy", "server", "production", "docker", "nginx", "systemd", "hosting"]


def classify_project_risk(project_type: str, description: str, features: list[str] | None = None) -> dict:
    text = " ".join([project_type or "", description or "", " ".join(features or [])])
    flags: list[str] = []
    reasons: list[str] = []

    if contains_any(text, PAID_KEYWORDS):
        flags.append("paid")
        flags.append("payment")
        reasons.append("The project appears to involve checkout, invoices, refunds, account balance, or paid access.")

    if contains_any(text, ["add funds", "balance", "wallet", "credit"]):
        flags.append("account_balance")
        reasons.append("The project appears to use prepaid balance or credits.")

    if contains_any(text, ABUSE_SENSITIVE_KEYWORDS):
        flags.append("abuse_sensitive")
        reasons.append("The project category has abuse/compliance risk and needs AUP/admin controls.")

    if contains_any(text, USER_DATA_KEYWORDS):
        flags.append("user_data")
        reasons.append("The project handles user accounts or personal data.")

    if contains_any(text, DEPLOYMENT_KEYWORDS):
        flags.append("deployment")
        reasons.append("The project mentions production/deployment/server operations.")

    risk_level = "low"
    if len(flags) >= 3 or "paid" in flags and "abuse_sensitive" in flags:
        risk_level = "high"
    elif flags:
        risk_level = "medium"

    return {
        "risk_level": risk_level,
        "flags": sorted(set(flags)),
        "requires_paid_launch_review": any(f in flags for f in ["paid", "payment", "account_balance"]),
        "requires_aup_review": "abuse_sensitive" in flags,
        "reasons": reasons,
    }
