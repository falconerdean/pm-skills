#!/usr/bin/env python3
"""
Environment Setup Manager for the AI Startup Engine.

Three modes:
  --check                   Audit current .env and report what's missing
  --set KEY=VALUE           Write a single variable to .env
  --set-batch K1=V1 K2=V2  Write multiple variables at once
  --init                    Copy template to workspace if .env doesn't exist

Usage:
  python3 env_setup.py --workspace ~/startup-workspace --check
  python3 env_setup.py --workspace ~/startup-workspace --set GITHUB_TOKEN=ghp_xxx
  python3 env_setup.py --workspace ~/startup-workspace --set-batch GITHUB_TOKEN=ghp_xxx NETLIFY_AUTH_TOKEN=nfp_xxx
  python3 env_setup.py --workspace ~/startup-workspace --init
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / ".env.template"

# Credential registry: what each var is, where to get it, which phases need it
CREDENTIALS = {
    # Critical — API access
    "ANTHROPIC_API_KEY": {
        "tier": "critical",
        "description": "Anthropic API key — ensures the engine runs on metered API, not a consumer subscription that can be rate-limited or shut down mid-sprint",
        "where_to_get": "https://console.anthropic.com/settings/keys → Create Key",
        "phases": "all",
        "format_hint": "sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "note": "Set this as a SYSTEM env var (export ANTHROPIC_API_KEY=...) not just in .env. Claude Code reads it from the shell environment.",
    },
    # Required
    "GITHUB_TOKEN": {
        "tier": "required",
        "description": "GitHub personal access token for pushing code, creating PRs, and tagging releases",
        "where_to_get": "https://github.com/settings/tokens → Generate new token (classic) → select 'repo' scope",
        "phases": [6, 7, 8],
        "format_hint": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
    "NETLIFY_AUTH_TOKEN": {
        "tier": "required",
        "description": "Netlify personal access token for deploying sites",
        "where_to_get": "https://app.netlify.com/user/applications#personal-access-tokens → New access token",
        "phases": [8],
        "format_hint": "nfp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
    "NETLIFY_SITE_ID": {
        "tier": "required",
        "description": "Netlify site ID (set after first deploy or site creation)",
        "where_to_get": "Run 'netlify sites:create --name your-app' or find in Netlify dashboard → Site settings → General → Site ID",
        "phases": [8],
        "format_hint": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "note": "Can be set later — only needed at Phase 8 (Deployment)",
    },
    # Full pipeline
    "BRIGHT_DATA_API_TOKEN": {
        "tier": "pipeline",
        "description": "Bright Data API token for web scraping and market research",
        "where_to_get": "https://brightdata.com → Account settings → API tokens",
        "phases": [0, 2],
        "format_hint": "API token string",
    },
    "GHL_API_KEY": {
        "tier": "pipeline",
        "description": "GoHighLevel API key for blogs, social posts, email campaigns, and CRM",
        "where_to_get": "GoHighLevel → Settings → Business Profile → API Key, or via OAuth app",
        "phases": [9],
        "format_hint": "API key string",
    },
    "GHL_LOCATION_ID": {
        "tier": "pipeline",
        "description": "GoHighLevel location/sub-account ID",
        "where_to_get": "GoHighLevel → Settings → Business Profile → Location ID",
        "phases": [9],
        "format_hint": "Location ID string",
    },
    "SANITY_PROJECT_ID": {
        "tier": "pipeline",
        "description": "Sanity CMS project ID",
        "where_to_get": "https://www.sanity.io/manage → Select project → Project ID shown in header",
        "phases": [4, 9],
        "format_hint": "alphanumeric string (e.g., a1b2c3d4)",
    },
    "SANITY_DATASET": {
        "tier": "pipeline",
        "description": "Sanity dataset name",
        "where_to_get": "https://www.sanity.io/manage → Project → Datasets tab",
        "phases": [4, 9],
        "format_hint": "production or develop",
    },
    "SANITY_TOKEN": {
        "tier": "pipeline",
        "description": "Sanity API token with write access",
        "where_to_get": "https://www.sanity.io/manage → Project → API tab → Add API token → Editor permission",
        "phases": [4, 9],
        "format_hint": "sk-prefixed token string",
    },
    "FIGMA_ACCESS_TOKEN": {
        "tier": "pipeline",
        "description": "Figma personal access token for creating designs and reading design systems",
        "where_to_get": "https://www.figma.com/developers/api#access-tokens → Generate new token",
        "phases": [4],
        "format_hint": "figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
}

# CLI tools to check
CLI_TOOLS = {
    "gh": {
        "check_cmd": "gh auth status",
        "description": "GitHub CLI — needed for PR creation and issue management",
        "install": "brew install gh && gh auth login",
    },
    "netlify": {
        "check_cmd": "netlify status",
        "description": "Netlify CLI — needed for deployment",
        "install": "npm install -g netlify-cli && netlify login",
    },
    "git": {
        "check_cmd": "git config user.name",
        "description": "Git — needed for version control",
        "install": "git config --global user.name 'Your Name' && git config --global user.email 'you@example.com'",
    },
    "node": {
        "check_cmd": "node --version",
        "description": "Node.js — needed for most web projects",
        "install": "brew install node (or use nvm: https://github.com/nvm-sh/nvm)",
    },
}

# MCP servers to check
MCP_SERVERS = [
    {"name": "Bright Data", "phases": [0, 2], "tier": "pipeline"},
    {"name": "GoHighLevel", "phases": [9], "tier": "pipeline"},
    {"name": "Figma", "phases": [4], "tier": "pipeline"},
    {"name": "Sanity", "phases": [4, 9], "tier": "pipeline"},
    {"name": "Chrome DevTools", "phases": [4, 7, 8], "tier": "recommended"},
]


def read_env(env_path: Path) -> dict:
    """Read .env file into a dict. Returns empty dict if file doesn't exist."""
    if not env_path.exists():
        return {}
    values = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value:  # Only count non-empty values
                    values[key] = value
    return values


def write_env_var(env_path: Path, key: str, value: str):
    """Write or update a single variable in .env file."""
    lines = []
    found = False

    if env_path.exists():
        with open(env_path) as f:
            lines = f.readlines()

    # Try to update existing line
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"# {key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break

    # If not found, append
    if not found:
        lines.append(f"\n{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(lines)


def check_env(workspace: Path) -> dict:
    """Audit the environment and return a structured report."""
    env_path = workspace / ".env"
    current_values = read_env(env_path)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "env_file_exists": env_path.exists(),
        "api_mode": None,  # "api" or "subscription"
        "credentials": {"critical": {}, "required": {}, "pipeline": {}, "optional": {}},
        "cli_tools": {},
        "mcp_servers": {},
        "summary": {"ready": [], "missing_critical": [], "missing_required": [], "missing_pipeline": [], "warnings": []},
    }

    # Check credentials — for ANTHROPIC_API_KEY, also check system environment
    for key, info in CREDENTIALS.items():
        tier = info["tier"]
        # Check both .env and system environment
        is_set = key in current_values or bool(os.environ.get(key))
        source = None
        if key in current_values:
            source = ".env"
        elif os.environ.get(key):
            source = "system env"

        entry = {
            "set": is_set,
            "source": source,
            "description": info["description"],
            "where_to_get": info["where_to_get"],
            "phases": info["phases"],
        }
        if "note" in info:
            entry["note"] = info["note"]

        report["credentials"][tier][key] = entry

        if is_set:
            report["summary"]["ready"].append(key)
        elif tier == "critical":
            report["summary"]["missing_critical"].append(key)
        elif tier == "required":
            report["summary"]["missing_required"].append(key)
        elif tier == "pipeline":
            report["summary"]["missing_pipeline"].append(key)

    # Determine API mode
    api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY")) or "ANTHROPIC_API_KEY" in current_values
    report["api_mode"] = "api" if api_key_set else "subscription"

    # Check CLI tools
    for tool, info in CLI_TOOLS.items():
        available = shutil.which(tool) is not None
        report["cli_tools"][tool] = {
            "available": available,
            "description": info["description"],
            "install": info["install"],
        }
        if available:
            report["summary"]["ready"].append(f"cli:{tool}")
        else:
            report["summary"]["warnings"].append(f"CLI tool '{tool}' not found: {info['install']}")

    # MCP servers can't be checked programmatically — just list what's needed
    for server in MCP_SERVERS:
        report["mcp_servers"][server["name"]] = {
            "phases": server["phases"],
            "tier": server["tier"],
            "note": "Check Claude Code MCP settings — cannot verify programmatically",
        }

    return report


def print_report(report: dict):
    """Print a human-readable environment report."""
    print("=" * 60)
    print("  AI STARTUP ENGINE — ENVIRONMENT CHECK")
    print("=" * 60)
    print()

    # API MODE CHECK — most important
    api_mode = report.get("api_mode", "unknown")
    if api_mode == "api":
        print("API MODE: [+] Using Anthropic API (metered, reliable)")
        source = report["credentials"].get("critical", {}).get("ANTHROPIC_API_KEY", {}).get("source", "")
        print(f"  ANTHROPIC_API_KEY found in: {source}")
    else:
        print("!" * 60)
        print("  WARNING: NO ANTHROPIC_API_KEY DETECTED")
        print("!" * 60)
        print()
        print("  You appear to be running on a Claude subscription (Max/Pro).")
        print("  This is RISKY for autonomous multi-agent workloads because:")
        print("    - Rate limits can throttle or halt agents mid-sprint")
        print("    - Subscription can be flagged for automated usage patterns")
        print("    - No cost visibility — you can't track spend per phase")
        print("    - Session limits may kill long-running agent chains")
        print()
        print("  STRONGLY RECOMMENDED: Switch to the Anthropic API.")
        print("  1. Get an API key: https://console.anthropic.com/settings/keys")
        print("  2. Add billing: https://console.anthropic.com/settings/billing")
        print("  3. Set it in your shell profile (~/.zshrc or ~/.bashrc):")
        print('     export ANTHROPIC_API_KEY="sk-ant-api03-..."')
        print("  4. Restart Claude Code for it to take effect.")
        print()
        print("  The API gives you: metered billing, no rate limits within")
        print("  your plan, cost tracking, and reliable multi-agent execution.")
    print()

    # Required credentials
    print("REQUIRED CREDENTIALS (blocks startup if missing):")
    print("-" * 50)
    for key, info in report["credentials"]["required"].items():
        status = "SET" if info["set"] else "MISSING"
        icon = "[+]" if info["set"] else "[!]"
        print(f"  {icon} {key}: {status}")
        if not info["set"]:
            print(f"      Get it: {info['where_to_get']}")
            if "note" in info:
                print(f"      Note: {info['note']}")
    print()

    # Pipeline credentials
    print("PIPELINE CREDENTIALS (needed for full SDLC):")
    print("-" * 50)
    for key, info in report["credentials"]["pipeline"].items():
        status = "SET" if info["set"] else "MISSING"
        icon = "[+]" if info["set"] else "[ ]"
        phases = ", ".join(str(p) for p in info["phases"])
        print(f"  {icon} {key}: {status} (Phases: {phases})")
        if not info["set"]:
            print(f"      Get it: {info['where_to_get']}")
    print()

    # CLI tools
    print("CLI TOOLS:")
    print("-" * 50)
    for tool, info in report["cli_tools"].items():
        status = "AVAILABLE" if info["available"] else "NOT FOUND"
        icon = "[+]" if info["available"] else "[!]"
        print(f"  {icon} {tool}: {status}")
        if not info["available"]:
            print(f"      Install: {info['install']}")
    print()

    # MCP servers
    print("MCP SERVERS (verify in Claude Code settings):")
    print("-" * 50)
    for name, info in report["mcp_servers"].items():
        phases = ", ".join(str(p) for p in info["phases"])
        print(f"  [ ] {name} (Phases: {phases}) — {info['tier']}")
    print()

    # Summary
    summary = report["summary"]
    total_required = len(report["credentials"]["required"])
    set_required = sum(1 for v in report["credentials"]["required"].values() if v["set"])
    total_pipeline = len(report["credentials"]["pipeline"])
    set_pipeline = sum(1 for v in report["credentials"]["pipeline"].values() if v["set"])

    print("=" * 60)
    print(f"  SUMMARY: {set_required}/{total_required} required, {set_pipeline}/{total_pipeline} pipeline")
    print("=" * 60)

    if summary.get("missing_critical"):
        print(f"\n  CRITICAL: {', '.join(summary['missing_critical'])}")
        print("  → The engine will run unreliably without API access.")

    if summary["missing_required"]:
        print(f"\n  BLOCKING: {', '.join(summary['missing_required'])}")
        print("  → Set these before starting the engine.")
    elif not summary.get("missing_critical"):
        print("\n  All required credentials are set. Ready to build.")

    if summary["missing_pipeline"]:
        print(f"\n  OPTIONAL: {', '.join(summary['missing_pipeline'])}")
        print("  → These phases will warn when reached but won't block startup.")

    print()


def init_env(workspace: Path):
    """Copy .env.template to workspace if .env doesn't exist."""
    env_path = workspace / ".env"
    if env_path.exists():
        print(f"SKIP: {env_path} already exists. Use --check to audit it.")
        return
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: Template not found at {TEMPLATE_PATH}")
        sys.exit(1)
    shutil.copy2(TEMPLATE_PATH, env_path)
    print(f"CREATED: {env_path}")
    print(f"  Copied from: {TEMPLATE_PATH}")
    print(f"  Edit this file or use --set KEY=VALUE to configure credentials.")


def main():
    args = sys.argv[1:]

    # Parse --workspace
    workspace = None
    for i, arg in enumerate(args):
        if arg == "--workspace" and i + 1 < len(args):
            workspace = Path(args[i + 1]).expanduser()
            break
    if not workspace:
        print("Usage: python3 env_setup.py --workspace ~/startup-workspace [--check|--init|--set K=V|--set-batch K=V ...]")
        sys.exit(1)

    if "--init" in args:
        workspace.mkdir(parents=True, exist_ok=True)
        init_env(workspace)

    elif "--check" in args:
        report = check_env(workspace)
        print_report(report)
        # Also save to logs
        logs_dir = workspace / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        with open(logs_dir / "env_check.json", "w") as f:
            json.dump(report, f, indent=2)
        print(f"  Report saved to: {logs_dir / 'env_check.json'}")

    elif "--set" in args:
        idx = args.index("--set")
        if idx + 1 >= len(args):
            print("ERROR: --set requires KEY=VALUE argument")
            sys.exit(1)
        pair = args[idx + 1]
        if "=" not in pair:
            print(f"ERROR: Invalid format '{pair}'. Use KEY=VALUE")
            sys.exit(1)
        key, _, value = pair.partition("=")
        env_path = workspace / ".env"
        if not env_path.exists():
            init_env(workspace)
        write_env_var(env_path, key.strip(), value.strip())
        print(f"SET: {key.strip()} in {env_path}")

    elif "--set-batch" in args:
        idx = args.index("--set-batch")
        pairs = args[idx + 1:]
        # Filter out --workspace and its value
        pairs = [p for p in pairs if p != "--workspace" and not p.startswith(str(workspace))]
        env_path = workspace / ".env"
        if not env_path.exists():
            init_env(workspace)
        for pair in pairs:
            if "=" not in pair:
                continue
            key, _, value = pair.partition("=")
            write_env_var(env_path, key.strip(), value.strip())
            print(f"SET: {key.strip()}")
        print(f"\nAll values written to {env_path}")

    else:
        print("Usage: python3 env_setup.py --workspace ~/startup-workspace [--check|--init|--set K=V|--set-batch K=V ...]")
        sys.exit(1)


if __name__ == "__main__":
    main()
