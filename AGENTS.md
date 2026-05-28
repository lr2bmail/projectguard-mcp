# ProjectGuard MCP Rules for Codex

ProjectGuard MCP is the quality gate for this repository.

Before creating or editing any app, website, SaaS, dashboard, API, or script:

1. Call ProjectGuard `start_project_review`.
2. Call `create_project_brief` and `create_build_rules`.
3. Call `review_file_plan` before writing files.
4. Do not create or edit files until `review_file_plan.approved` is true.
5. Before final review, call `recommend_security_reviews`.
6. Run any blocking focused security reviews recommended by `recommend_security_reviews`, such as:
   - `review_api_security`
   - `review_payment_webhook_security`
   - `review_docker_security`
7. After implementation, call `review_project_text`, `review_code_quality`, `review_security`, and `final_project_score`.
8. For public websites, also call `review_seo`.
9. For paid SaaS, checkout, account balance, invoices, refunds, proxies, VPN, email API, scanners, or abuse-sensitive services, call `review_paid_launch_readiness`.
10. Never create fake features, fake integrations, fake testimonials, placeholder buttons, or filler text as if real.
11. Never rewrite unrelated files.
12. Do not mark work complete unless `final_project_score.approved` is true.

Repository checks:

- Run `pytest` after Python logic changes.
- Keep ProjectGuard v1 review-only; do not add tools that execute arbitrary shell commands, edit projects, deploy apps, or delete files.
- Use explicit allowlists and audit logs before adding any future write/deploy tools.
