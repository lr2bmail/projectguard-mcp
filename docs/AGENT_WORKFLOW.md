# Agent Workflow

Use this workflow in any AI coding system connected to ProjectGuard MCP.

## Before coding

1. Call `classify_project_risk`.
2. Call `analyze_project_request`.
3. Create assumptions only when the user request is incomplete.
4. Call `create_project_brief`.
5. Call `create_build_rules`.
6. Submit the planned files to `review_file_plan`.
7. Do not create/edit files until the file plan passes or the agent clearly explains the remaining risk.

## During coding

- Keep v1 small.
- Do not add fake features.
- Do not add placeholder buttons as final features.
- Do not rewrite unrelated files.
- Keep config/secrets out of source code.

## After coding

1. Call `review_project_text` on public copy, README, and final answer.
2. Call `review_code_quality` on changed files.
3. Call `review_security` if there are users, auth, uploads, payments, admin, APIs, or sensitive actions.
4. Call `review_seo` for public websites.
5. Call `review_paid_launch_readiness` for paid SaaS/digital-service products.
6. Call `final_project_score`.

## Completion rule

The agent must not say the project is production-ready unless `final_project_score.approved = true` and no required review has failed.
