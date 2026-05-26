# ProjectGuard MCP

ProjectGuard MCP is a production-oriented MCP server that acts as a quality gate for AI-built projects. It helps prevent AI agents from creating sloppy apps, websites, SaaS products, dashboards, scripts, and paid digital services by forcing planning, file-structure review, anti-slop checks, security checks, SEO checks, paid-launch readiness, and a final approval score.

The first version is intentionally review-only. It does not edit files, run arbitrary shell commands, deploy apps, or delete anything.

## What it does

ProjectGuard exposes MCP tools that an AI coding agent can call before and after implementation:

- `start_project_review`
- `classify_project_risk`
- `analyze_project_request`
- `create_project_brief`
- `create_build_rules`
- `review_file_plan`
- `review_project_text`
- `review_code_quality`
- `review_security`
- `review_seo`
- `review_paid_launch_readiness`
- `final_project_score`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For MCP development tools:

```bash
pip install -e ".[dev]"
```

## Run MCP server

```bash
projectguard-mcp
```

Default endpoint:

```text
http://127.0.0.1:8000/mcp
```

## Run in stdio mode

```bash
PROJECTGUARD_TRANSPORT=stdio projectguard-mcp
```

## Test with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector
```

Connect to:

```text
http://127.0.0.1:8000/mcp
```

## Run tests

```bash
pip install -e ".[dev]"
pytest
```

## Claude Code and Codex support

ProjectGuard includes client guidance for both Claude Code and Codex. MCP exposes the tools, resources, and prompts; persistent client instructions tell the coding agent when to call them.

### Claude Code

Run ProjectGuard:

```bash
projectguard-mcp
```

Add it to Claude Code:

```bash
claude mcp add --transport http --scope local projectguard http://127.0.0.1:8000/mcp
```

Then copy this into the project Claude Code will work on:

```text
examples/claude-code/CLAUDE.md
```

Optional project-scoped MCP config:

```text
examples/claude-code/.mcp.json
```

### Codex

Run ProjectGuard:

```bash
projectguard-mcp
```

Then copy the Codex MCP config into `~/.codex/config.toml` or a trusted project `.codex/config.toml`:

```text
examples/codex/config.toml
```

For stdio mode, use:

```text
examples/codex/config-stdio.toml
```

Then copy this into the project Codex will work on:

```text
examples/codex/AGENTS.md
```

In Claude Code or Codex, use `/mcp` to confirm the server is connected.

See `docs/CLIENT_SETUP.md` for the full client setup.

## Example system prompt for an AI coding agent

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

## Production notes

- Keep v1 review-only.
- Run behind local-only access or an authenticated reverse proxy.
- Do not expose risky tools like arbitrary command execution.
- Keep audit logs if you later add write/deploy tools.
- Add CI checks before using it as a hard gate in production.
