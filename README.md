# ProjectGuard MCP

ProjectGuard MCP is a small MCP server that helps AI coding agents avoid messy, generic, or unsafe projects.

It is made for tools like:

- Claude Code
- Codex
- other MCP-compatible coding agents

ProjectGuard is **review-only**. It does not edit files, run shell commands, deploy apps, or delete anything.

## What it checks

ProjectGuard gives your AI agent quality checks for:

- project planning
- file structure
- fake/placeholder content
- code quality
- security basics
- SEO basics
- paid SaaS/payment launch readiness

Main tools:

- `start_project_review`
- `review_file_plan`
- `review_project_text`
- `review_code_quality`
- `review_security`
- `review_seo`
- `review_paid_launch_readiness`
- `final_project_score`

## Install

```bash
git clone https://github.com/lr2bmail/projectguard-mcp.git
cd projectguard-mcp

python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .
```

On Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Windows quick setup

```bat
scripts\setup_windows.cmd
```

## Add to Claude Code

Recommended Windows command:

```bat
claude mcp remove projectguard

claude mcp add --transport stdio --scope user projectguard ^
  --env PROJECTGUARD_TRANSPORT=stdio ^
  -- D:\Downloads\projectguard-mcp\projectguard-mcp\scripts\run_projectguard.cmd
```

Change the path if your repo is in another folder.

Check inside Claude Code:

```text
/mcp
```

For better behavior, copy this file into the project Claude Code will work on:

```text
examples/claude-code/CLAUDE.md
```

## Add to Codex

Copy this file to your Codex config:

```text
examples/codex/config.toml
```

Usually to:

```text
~/.codex/config.toml
```

Then copy this into the project Codex will work on:

```text
examples/codex/AGENTS.md
```

Check inside Codex:

```text
/mcp
```

## Recommended agent rule

Use this instruction with Claude Code, Codex, or another agent:

```text
Use ProjectGuard MCP before creating or editing any app, website, SaaS, dashboard, API, or script.

Start with start_project_review.
Create the project brief and build rules.
Call review_file_plan before writing files.
After coding, call review_project_text, review_code_quality, review_security, and final_project_score.
For public websites, call review_seo.
For paid SaaS, payments, account balance, proxies, VPN, email API, scanners, or abuse-sensitive services, call review_paid_launch_readiness.
Do not mark the task complete unless final_project_score.approved is true.
```

## Run manually

Stdio mode, used by Claude Code/Codex:

```bash
projectguard-mcp
```

HTTP mode, useful for MCP Inspector or shared/server usage:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
```

HTTP endpoint:

```text
http://127.0.0.1:8000/mcp
```

## Test

```bash
pytest
```

## More docs

- `docs/CLIENT_SETUP.md`
- `WINDOWS_SETUP.md`
- `examples/claude-code/CLAUDE.md`
- `examples/codex/AGENTS.md`

## License

MIT
