# PaidLaunchGuard

PaidLaunchGuard is a conditional module. It should run only when a project accepts money, sells access, uses account balance/credits, handles invoices/refunds, or belongs to abuse-sensitive categories like proxies, VPN, email APIs, scanners, scraping, or automation.

## Minimum checks

- Public business identity is visible where needed.
- Terms, Privacy, Refund, Contact/support pages exist.
- AUP and Fair Usage exist for abuse-sensitive services.
- Signup agreement uses an unchecked checkbox.
- Accepted policy versions, timestamp, IP, user agent, user ID, and source action are stored.
- Payment consent shows amount, currency, provider/method, and what the user is buying.
- Provider payment/session IDs and webhook event IDs are stored.
- Order confirmation shows cost, balance before/after, delivery state, service limits, and AUP reminder.
- Every balance movement has a durable ledger entry.
- Admin can export payments, invoices, refunds, and ledger rows.
- Refund reason, admin approval, original invoice/payment, destination, and user notification are stored.
- Abuse reporting contact and suspension/note tooling exist for abuse-sensitive products.

This module is an operational readiness check, not legal or tax advice.
