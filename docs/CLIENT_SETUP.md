# ProjectGuard Client Setup

ProjectGuard works with MCP-capable coding agents. The server exposes tools, resources, and prompts, but the coding client should also receive persistent project instructions so it calls the tools in the right order.

## Required quality-gate flow

1. `start_project_review`
2. `create_project_brief`
3. `create_build_rules`
4. `review_file_plan` before writing files
5. Implement only the approved scope
6. `review_project_text`
7. `review_code_quality`
8. `review_security`
9. `review_seo` for public websites
10. `review_paid_launch_readiness` for paid/payment/account-balance/abuse-sensitive services
11. `final_project_score`

Do not mark the task complete unless `final_project_score.approved` is true.

## Claude Code

Run ProjectGuard:

```bash
projectguard-mcp
```

Add it to Claude Code:

```bash
claude mcp add --transport http --scope local projectguard http://127.0.0.1:8000/mcp
```

Check it:

```text
/mcp
```

Copy `examples/claude-code/CLAUDE.md` into the project where Claude Code will build apps. You can also copy `examples/claude-code/.mcp.json` into that project if you want project-scoped MCP config.

## Codex

Run ProjectGuard:

```bash
projectguard-mcp
```

Codex supports MCP through CLI/IDE configuration. Copy `examples/codex/config.toml` into either:

```text
~/.codex/config.toml
```

or a trusted project:

```text
.codex/config.toml
```

Then copy `examples/codex/AGENTS.md` into the project root so Codex knows the ProjectGuard workflow.

Inside Codex TUI, check MCP servers with:

```text
/mcp
```

Alternative stdio config is available in `examples/codex/config-stdio.toml`.

## Why client instructions are still needed

MCP exposes the tools, resources, and prompts. The client instructions (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex) tell the coding agent when to call those tools and what counts as done.
