# ProjectGuard Client Setup

ProjectGuard works with MCP-capable coding agents. The server exposes tools, resources, and prompts, but the coding client should also receive persistent project instructions so it calls the tools in the right order.

## Transport choice

Use **stdio** for local Claude Code/Codex usage.

```text
Recommended local mode: stdio
Optional shared/server mode: streamable-http
Avoid for new setup: SSE
```

Stdio does not require a separate HTTP server. The coding client starts ProjectGuard as a local process.

Use HTTP only when you want a shared/server endpoint, Docker mode, MCP Inspector testing, or multiple clients connecting to the same ProjectGuard instance.

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

Recommended stdio setup:

```bash
claude mcp add --transport stdio --scope user projectguard \
  --env PROJECTGUARD_TRANSPORT=stdio \
  -- projectguard-mcp
```

Check it:

```text
/mcp
```

Copy `examples/claude-code/CLAUDE.md` into the project where Claude Code will build apps. You can also copy `examples/claude-code/.mcp.json` into that project if you want project-scoped MCP config.

HTTP alternative:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
claude mcp add --transport http --scope local projectguard http://127.0.0.1:8000/mcp
```

## Codex

Recommended stdio setup:

Copy `examples/codex/config.toml` into either:

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

HTTP alternative is available in:

```text
examples/codex/config-http.toml
```

## MCP Inspector

MCP Inspector is easiest with HTTP mode:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
npx -y @modelcontextprotocol/inspector
```

Connect to:

```text
http://127.0.0.1:8000/mcp
```

## Why client instructions are still needed

MCP exposes the tools, resources, and prompts. The client instructions (`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex) tell the coding agent when to call those tools and what counts as done.
