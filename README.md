# ProjectGuard MCP

ProjectGuard MCP is a quality gate for AI coding agents.

It helps Claude Code, Codex, and other MCP clients avoid building sloppy apps, websites, SaaS products, dashboards, APIs, and scripts.

It checks things like:

- weak project plans
- bad file structure
- fake features
- placeholder text
- generic AI copy
- basic code quality
- baseline security
- focused API/payment/Docker security
- SEO basics
- paid SaaS launch readiness

ProjectGuard is **review-only**. It does not edit files, deploy apps, delete files, or run arbitrary shell commands.

---

## Install

### Option 1 — uv recommended

```bash
uv tool install git+https://github.com/lr2bmail/projectguard-mcp.git
```

Check that it works:

```bash
projectguard-mcp
```

For Claude Code or Codex, you normally do not run `projectguard-mcp` manually. The AI client starts it through MCP stdio.

---

### Option 2 — pipx alternative

```bash
pipx install git+https://github.com/lr2bmail/projectguard-mcp.git
```

Check that it works:

```bash
projectguard-mcp
```

---

### Development install

Use this only if you want to edit ProjectGuard itself.

Windows:

```bat
git clone https://github.com/lr2bmail/projectguard-mcp.git
cd projectguard-mcp

python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
git clone https://github.com/lr2bmail/projectguard-mcp.git
cd projectguard-mcp

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run lint:

```bash
ruff check .
```

---

## Add to Claude Code

Recommended setup:

```bash
claude mcp add --transport stdio --scope user projectguard \
  --env PROJECTGUARD_TRANSPORT=stdio \
  -- projectguard-mcp
```

Windows PowerShell:

```powershell
claude mcp add --transport stdio --scope user projectguard `
  --env PROJECTGUARD_TRANSPORT=stdio `
  -- projectguard-mcp
```

Check inside Claude Code:

```text
/mcp
```

You should see `projectguard`.

For better behavior, copy this file into the project Claude Code will work on:

```text
examples/claude-code/CLAUDE.md
```

---

## Add to Codex

Add this to:

```text
~/.codex/config.toml
```

```toml
[mcp_servers.projectguard]
command = "projectguard-mcp"
env = { PROJECTGUARD_TRANSPORT = "stdio" }
enabled = true
required = false
default_tools_approval_mode = "auto"
startup_timeout_sec = 20
tool_timeout_sec = 60
```

Check inside Codex:

```text
/mcp
```

For better behavior, copy this file into the project Codex will work on:

```text
examples/codex/AGENTS.md
```

---

## How to use

Tell Claude Code or Codex:

```text
Use ProjectGuard MCP before writing files.

Call start_project_review first.
Call review_file_plan before creating files.
Call recommend_security_reviews before final review.
After coding, call review_project_text, review_code_quality, review_security, and final_project_score.
Run the focused security reviews recommended by recommend_security_reviews.
For public websites, also call review_seo.
For paid SaaS or payment/account systems, also call review_paid_launch_readiness.
Do not mark the task complete unless final_project_score.approved is true.
```

---

## Main tools

ProjectGuard exposes these MCP tools:

```text
start_project_review
classify_project_risk
analyze_project_request
create_project_brief
create_build_rules
review_file_plan
review_project_text
review_code_quality
review_security
recommend_security_reviews
review_api_security
review_payment_webhook_security
review_docker_security
review_seo
review_ux_checklist
review_paid_launch_readiness
final_project_score
```

Most users should start with:

```text
start_project_review
```

For security-focused projects, use:

```text
recommend_security_reviews
```

It will tell the agent whether to also run:

```text
review_api_security
review_payment_webhook_security
review_docker_security
```

---

## SecuritySkillsGuard

SecuritySkillsGuard is the focused defensive security layer inside ProjectGuard.

It adds:

- `recommend_security_reviews` — chooses the right security reviews based on project type, files, and features
- `review_api_security` — checks API auth, object authorization, admin role checks, GraphQL limits, and rate limits
- `review_payment_webhook_security` — checks webhook signatures, idempotency, amount/currency checks, balance ledger, and refund/dispute handling
- `review_docker_security` — checks Dockerfile/Compose hardening, root containers, privileged mode, Docker socket mounts, host network, secrets in env, and `.dockerignore`

This is defensive only. It does not run scans, exploits, payloads, or offensive workflows.

---

## Transport mode

ProjectGuard uses **stdio** by default.

That means you do not need to run a separate HTTP server for local Claude Code or Codex usage.

Optional HTTP mode is available for MCP Inspector, Docker, or shared/server use:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
```

HTTP endpoint:

```text
http://127.0.0.1:8000/mcp
```

---

## Test with MCP Inspector

HTTP mode is easier for MCP Inspector:

```bash
PROJECTGUARD_TRANSPORT=streamable-http projectguard-mcp
```

Then run:

```bash
npx -y @modelcontextprotocol/inspector
```

Connect to:

```text
http://127.0.0.1:8000/mcp
```

---

## Windows notes

If `projectguard-mcp` is not found, use the Windows setup script from a development clone:

```bat
scripts\setup_windows.cmd
```

Then use:

```bat
scripts\run_projectguard.cmd
```

For Claude Code with local dev clone:

```bat
claude mcp add --transport stdio --scope user projectguard ^
  --env PROJECTGUARD_TRANSPORT=stdio ^
  -- D:\path\to\projectguard-mcp\scripts\run_projectguard.cmd
```

---

## Safety

ProjectGuard v1 is intentionally safe:

- no file editing tools
- no deploy tools
- no delete tools
- no arbitrary shell execution
- no access to secrets unless the AI client sends content for review

Future write/deploy tools should require human approval, strict allowlists, and audit logs.

---

## License

MIT
