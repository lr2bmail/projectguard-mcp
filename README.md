# ProjectGuard MCP

ProjectGuard MCP is a review-only quality gate for AI coding agents. It helps stop AI-built apps, websites, SaaS products, dashboards, APIs, and scripts from becoming generic, unsafe, incomplete, or hard to maintain.

It is designed for tools like **Claude Code**, **Codex**, and other MCP-capable coding agents.

ProjectGuard does **not** edit files, run arbitrary shell commands, deploy apps, or delete anything. It gives the AI structured checks before and after coding.

## Recommended mode

For local coding agents, use **stdio**.

```text
Recommended local mode: stdio
Optional shared/server mode: streamable-http
Deprecated/avoid for new setup: SSE
```

Stdio does not require you to run a separate HTTP server. Claude Code or Codex starts ProjectGuard as a local MCP process when needed.

Use HTTP only when you want a long-running shared MCP endpoint, Docker deployment, MCP Inspector testing, or multiple clients connecting to the same ProjectGuard server.

## Why use it

AI agents are fast, but they often create:

- generic landing pages
- weak file structures
- fake features and placeholder buttons
- filler text and fake testimonials
- missing mobile/error/loading states
- missing SEO basics
- weak security checks
- paid SaaS flows without invoices, refund logic, consent records, or abuse controls

ProjectGuard gives the agent a workflow:

```text
project request
→ start project review
→ create project brief
→ create build rules
→ review file plan
→ implement
→ review text/code/security/SEO/paid-launch readiness
→ final project score
```

## Features

ProjectGuard exposes these MCP tools:

| Tool | Purpose |
|---|---|
| `start_project_review` | Main entry point. Tells the agent required workflow, risks, reviews, and next tool. |
| `classify_project_risk` | Detects project risk and required review modules. |
| `analyze_project_request` | Checks if the user request is clear enough before coding. |
| `create_project_brief` | Creates a structured brief the agent must follow. |
| `create_build_rules` | Returns anti-slop rules based on project type and risk flags. |
| `review_file_plan` | Reviews planned files before the agent writes code. |
| `review_project_text` | Detects filler text, fake claims, placeholders, and generic AI copy. |
| `review_code_quality` | Runs lightweight code-quality checks on generated files. |
| `review_security` | Checks for common security risks. |
| `review_seo` | Checks public pages for SEO basics. |
| `review_paid_launch_readiness` | Checks paid SaaS/payment/account-balance/abuse-sensitive launch readiness. |
| `final_project_score` | Calculates final approval score. |

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
pytest
```

## Run modes

### Stdio mode — recommended for Claude Code/Codex

```bash
PROJECTGUARD_TRANSPORT=stdio projectguard-mcp
```

The code default is also stdio, so this works too:

```bash
projectguard-mcp
```

### HTTP mode — optional shared/server mode

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
```

Default HTTP endpoint:

```text
http://127.0.0.1:8000/mcp
```

## Add to Claude Code

Recommended stdio setup:

```bash
claude mcp add --transport stdio --scope user projectguard \
  --env PROJECTGUARD_TRANSPORT=stdio \
  -- projectguard-mcp
```

Check it inside Claude Code:

```text
/mcp
```

For persistent project behavior, copy this file into the project Claude Code will work on:

```text
examples/claude-code/CLAUDE.md
```

Optional project-scoped MCP config:

```text
examples/claude-code/.mcp.json
```

HTTP alternative for Claude Code:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
claude mcp add --transport http --scope local projectguard http://127.0.0.1:8000/mcp
```

## Add to Codex

Recommended stdio setup:

Copy this config into `~/.codex/config.toml` or a trusted project `.codex/config.toml`:

```text
examples/codex/config.toml
```

Then copy this into the project Codex will work on:

```text
examples/codex/AGENTS.md
```

Check MCP servers inside Codex:

```text
/mcp
```

HTTP alternative for Codex:

```text
examples/codex/config-http.toml
```

## Test with MCP Inspector

MCP Inspector is easier with HTTP mode:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
npx -y @modelcontextprotocol/inspector
```

Connect to:

```text
http://127.0.0.1:8000/mcp
```

## Required agent workflow

Use this instruction in any MCP-capable coding agent:

```text
You are connected to ProjectGuard MCP.

Before creating or editing any app, website, SaaS, script, dashboard, or API project:
1. Call start_project_review.
2. Call create_project_brief.
3. Call create_build_rules.
4. Call review_file_plan before creating files.
5. Do not create or edit files until review_file_plan passes.
6. After implementation, call review_project_text, review_code_quality, review_security, and final_project_score.
7. For public websites, call review_seo.
8. For paid SaaS, checkout, account balance, invoices, refunds, proxies, VPN, email API, scanners, or other abuse-sensitive services, call review_paid_launch_readiness.
9. Never create fake features, fake integrations, fake testimonials, placeholder buttons, or filler text as if real.
10. Never rewrite unrelated files.
11. Do not mark the task complete unless final_project_score.approved is true.
```

## MCP resources

ProjectGuard also exposes resources that agents can reference:

```text
projectguard://workflow/agent
projectguard://workflow/claude-code
projectguard://workflow/codex
projectguard://rules/general
projectguard://rules/website
projectguard://rules/saas
projectguard://rules/paid-launch
projectguard://examples/good-file-plan
projectguard://examples/bad-file-plan
```

## MCP prompts

Available prompts:

```text
coding_agent_workflow
projectguard_start
projectguard_final_review
claude_code_projectguard_workflow
codex_projectguard_workflow
```

## Docker

Docker uses HTTP mode because containers are easier to expose through a local port:

```bash
docker compose up --build
```

This binds the MCP server to:

```text
127.0.0.1:8000
```

## Repo structure

```text
src/projectguard_mcp/
  server.py
  rules.py
  scoring.py
  reviewers/

tests/
docs/
examples/
docker/
```

Important user files:

```text
README.md
CLAUDE.md
AGENTS.md
docs/CLIENT_SETUP.md
examples/claude-code/CLAUDE.md
examples/claude-code/.mcp.json
examples/codex/AGENTS.md
examples/codex/config.toml
examples/codex/config-http.toml
```

## Safety model

ProjectGuard v1 is intentionally safe:

- review-only
- no arbitrary command execution
- no file editing tools
- no deploy tools
- no delete tools
- no access to secrets unless the client sends code/content for review

Future write/deploy tools should require:

- strict allowlists
- audit logs
- human approval for risky actions
- no broad shell command execution
- local-only or authenticated access

## Production notes

- Use stdio for local Claude Code/Codex usage.
- Use HTTP only for shared/team/server mode.
- Keep HTTP bound to `127.0.0.1` unless protected by authentication and rate limiting.
- Do not expose HTTP publicly without auth.
- Keep v1 as a quality gate, not an autonomous deployer.
- Add CI checks before using it as a hard gate in production.
- For paid SaaS, use `review_paid_launch_readiness` before public launch.

## Development

Run tests:

```bash
pytest
```

Run lint:

```bash
ruff check .
```

Install editable dev version:

```bash
pip install -e ".[dev]"
```

## License

MIT
