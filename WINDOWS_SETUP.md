# Windows Setup

Use this setup if Claude Code or Codex cannot find `projectguard-mcp`, or if `python -m projectguard_mcp.server` says `ModuleNotFoundError`.

## 1. Run setup

From the repo root:

```bat
scripts\setup_windows.cmd
```

PowerShell alternative:

```powershell
.\scripts\setup_windows.ps1
```

This creates `.venv`, installs ProjectGuard editable, and verifies the import.

## 2. Add to Claude Code

Use the launcher, not the global `projectguard-mcp` command:

```bat
claude mcp remove projectguard
claude mcp add --transport stdio --scope user projectguard --env PROJECTGUARD_TRANSPORT=stdio -- D:\Downloads\projectguard-mcp\projectguard-mcp\scripts\run_projectguard.cmd
```

Change the path if your repo is somewhere else.

## 3. Test

Inside Claude Code:

```text
/mcp
```

You should see `projectguard` connected.

## Why this works better

The launcher runs ProjectGuard through the repo-local `.venv` and `run_projectguard.py`. The Python script adds `src/` to `sys.path`, so it still works even when Windows PATH points to an old global `projectguard-mcp.exe`.
