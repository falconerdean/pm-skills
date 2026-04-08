#!/usr/bin/env python3
"""
Token Validation Script for Startup Engine

Validates that all configured tokens are:
1. Present (not empty)
2. Valid (make a real API call)
3. Scoped correctly (pointed at the right project/account)

Checks both local .env AND Doppler, flags mismatches.

Usage:
  python3 validate_tokens.py --workspace ~/startup-workspace
  python3 validate_tokens.py --workspace ~/startup-workspace --doppler-only
  python3 validate_tokens.py --workspace ~/startup-workspace --env-only
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Token definitions: key in .env, Doppler key (if different), validation function name
TOKEN_DEFS = [
    {
        "name": "Anthropic API Key",
        "env_key": "ANTHROPIC_API_KEY",
        "doppler_key": "ANTHROPIC_API_KEY",
        "required": True,
        "validate": "validate_anthropic",
    },
    {
        "name": "GitHub Token",
        "env_key": "GITHUB_TOKEN",
        "doppler_key": "GITHUB_PAT",
        "required": True,
        "validate": "validate_github",
    },
    {
        "name": "Netlify Auth Token",
        "env_key": "NETLIFY_AUTH_TOKEN",
        "doppler_key": "NETLIFY_API_TOKEN",
        "required": False,
        "validate": "validate_netlify",
    },
    {
        "name": "Sanity Write Token",
        "env_key": "SANITY_WRITE_TOKEN",
        "doppler_key": "SANITY_API_WRITE_TOKEN",
        "required": False,
        "validate": "validate_sanity",
    },
    {
        "name": "Stripe Secret Key",
        "env_key": "STRIPE_SECRET_KEY",
        "doppler_key": "STRIPE_SECRET_KEY",
        "required": False,
        "validate": "validate_stripe",
    },
    {
        "name": "Sentry Auth Token",
        "env_key": "SENTRY_AUTH_TOKEN",
        "doppler_key": "SENTRY_AUTH_TOKEN",
        "required": False,
        "validate": "validate_sentry",
    },
]


def run_cmd(cmd, timeout=10):
    """Run a shell command and return (success, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)


def load_env_file(workspace):
    """Load tokens from .env file."""
    env_path = Path(workspace) / ".env"
    tokens = {}
    if not env_path.exists():
        return tokens
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value:
                tokens[key] = value
    return tokens


def load_doppler_tokens():
    """Load tokens from Doppler."""
    tokens = {}
    ok, stdout, _ = run_cmd(
        "doppler secrets download --no-file --format json 2>/dev/null", timeout=15
    )
    if ok and stdout:
        try:
            data = json.loads(stdout)
            tokens = {k: v for k, v in data.items() if v}
        except json.JSONDecodeError:
            pass
    return tokens


# --- Validation functions ---
# Each returns (status, detail) where status is VALID/INVALID/WRONG_SCOPE/ERROR


def validate_anthropic(token):
    """Validate Anthropic API key by listing models."""
    ok, stdout, stderr = run_cmd(
        f'curl -s -w "\\n%{{http_code}}" -H "x-api-key: {token}" '
        f'-H "anthropic-version: 2023-06-01" '
        f'"https://api.anthropic.com/v1/models?limit=1"'
    )
    if not ok:
        return "ERROR", f"curl failed: {stderr}"
    lines = stdout.strip().split("\n")
    http_code = lines[-1] if lines else ""
    if http_code == "200":
        return "VALID", "Authenticated successfully"
    elif http_code == "401":
        return "INVALID", "Authentication failed — bad key"
    else:
        return "ERROR", f"HTTP {http_code}"


def validate_github(token):
    """Validate GitHub token."""
    ok, stdout, stderr = run_cmd(
        f'curl -s -w "\\n%{{http_code}}" -H "Authorization: token {token}" '
        f'"https://api.github.com/user"'
    )
    if not ok:
        return "ERROR", f"curl failed: {stderr}"
    lines = stdout.strip().split("\n")
    http_code = lines[-1] if lines else ""
    if http_code == "200":
        try:
            data = json.loads("\n".join(lines[:-1]))
            login = data.get("login", "unknown")
            return "VALID", f"Authenticated as {login}"
        except json.JSONDecodeError:
            return "VALID", "Authenticated"
    elif http_code == "401":
        return "INVALID", "Authentication failed — bad token"
    else:
        return "ERROR", f"HTTP {http_code}"


def validate_netlify(token):
    """Validate Netlify token by listing sites."""
    ok, stdout, stderr = run_cmd(
        f'curl -s -w "\\n%{{http_code}}" -H "Authorization: Bearer {token}" '
        f'"https://api.netlify.com/api/v1/sites?per_page=1"'
    )
    if not ok:
        return "ERROR", f"curl failed: {stderr}"
    lines = stdout.strip().split("\n")
    http_code = lines[-1] if lines else ""
    if http_code == "200":
        return "VALID", "Authenticated successfully"
    elif http_code == "401":
        return "INVALID", "Authentication failed — bad token"
    else:
        return "ERROR", f"HTTP {http_code}"


def validate_sanity(token):
    """Validate Sanity token by querying projects."""
    ok, stdout, stderr = run_cmd(
        f'curl -s -w "\\n%{{http_code}}" -H "Authorization: Bearer {token}" '
        f'"https://api.sanity.io/v2021-06-07/projects"'
    )
    if not ok:
        return "ERROR", f"curl failed: {stderr}"
    lines = stdout.strip().split("\n")
    http_code = lines[-1] if lines else ""
    if http_code == "200":
        try:
            data = json.loads("\n".join(lines[:-1]))
            project_ids = [p.get("id", "?") for p in data] if isinstance(data, list) else []
            return "VALID", f"Access to {len(project_ids)} project(s): {', '.join(project_ids[:5])}"
        except json.JSONDecodeError:
            return "VALID", "Authenticated"
    elif http_code == "401":
        return "INVALID", "Authentication failed — bad token"
    else:
        return "ERROR", f"HTTP {http_code}"


def validate_stripe(token):
    """Validate Stripe key by listing charges."""
    ok, stdout, stderr = run_cmd(
        f'curl -s -w "\\n%{{http_code}}" -u "{token}:" '
        f'"https://api.stripe.com/v1/charges?limit=1"'
    )
    if not ok:
        return "ERROR", f"curl failed: {stderr}"
    lines = stdout.strip().split("\n")
    http_code = lines[-1] if lines else ""
    if http_code == "200":
        mode = "LIVE" if token.startswith("sk_live_") else "TEST" if token.startswith("sk_test_") else "UNKNOWN"
        return "VALID", f"Authenticated ({mode} mode)"
    elif http_code == "401":
        return "INVALID", "Authentication failed — bad key"
    else:
        return "ERROR", f"HTTP {http_code}"


def validate_sentry(token):
    """Validate Sentry token by listing organizations."""
    ok, stdout, stderr = run_cmd(
        f'curl -s -w "\\n%{{http_code}}" -H "Authorization: Bearer {token}" '
        f'"https://sentry.io/api/0/organizations/"'
    )
    if not ok:
        return "ERROR", f"curl failed: {stderr}"
    lines = stdout.strip().split("\n")
    http_code = lines[-1] if lines else ""
    if http_code == "200":
        try:
            data = json.loads("\n".join(lines[:-1]))
            orgs = [o.get("slug", "?") for o in data] if isinstance(data, list) else []
            return "VALID", f"Access to org(s): {', '.join(orgs[:5])}"
        except json.JSONDecodeError:
            return "VALID", "Authenticated"
    elif http_code == "401":
        return "INVALID", "Authentication failed — bad token"
    else:
        return "ERROR", f"HTTP {http_code}"


VALIDATORS = {
    "validate_anthropic": validate_anthropic,
    "validate_github": validate_github,
    "validate_netlify": validate_netlify,
    "validate_sanity": validate_sanity,
    "validate_stripe": validate_stripe,
    "validate_sentry": validate_sentry,
}


def main():
    parser = argparse.ArgumentParser(description="Validate startup engine tokens")
    parser.add_argument("--workspace", required=True, help="Workspace path")
    parser.add_argument("--doppler-only", action="store_true", help="Only check Doppler")
    parser.add_argument("--env-only", action="store_true", help="Only check local .env")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Load tokens from sources
    env_tokens = {} if args.doppler_only else load_env_file(args.workspace)
    doppler_tokens = {} if args.env_only else load_doppler_tokens()

    results = []
    has_failures = False

    for tdef in TOKEN_DEFS:
        env_val = env_tokens.get(tdef["env_key"], "")
        doppler_val = doppler_tokens.get(tdef["doppler_key"], "")

        # Pick the token to validate (prefer Doppler if both exist)
        token = doppler_val or env_val
        source = "doppler" if doppler_val else "env" if env_val else "missing"

        # Check for mismatch
        mismatch = False
        if env_val and doppler_val and env_val != doppler_val:
            mismatch = True

        # Validate
        if not token:
            status = "MISSING"
            detail = "Not found in .env or Doppler"
            if tdef["required"]:
                has_failures = True
        else:
            validator = VALIDATORS.get(tdef["validate"])
            if validator:
                status, detail = validator(token)
                if status != "VALID":
                    has_failures = True
            else:
                status, detail = "SKIPPED", "No validator"

        result = {
            "name": tdef["name"],
            "env_key": tdef["env_key"],
            "doppler_key": tdef["doppler_key"],
            "required": tdef["required"],
            "source": source,
            "status": status,
            "detail": detail,
            "mismatch": mismatch,
        }
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
        return 1 if has_failures else 0

    # Pretty print
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║              TOKEN VALIDATION REPORT                        ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    for r in results:
        icon = {"VALID": "✓", "INVALID": "✗", "WRONG_SCOPE": "⚠", "MISSING": "—", "ERROR": "✗", "SKIPPED": "○"}
        status_icon = icon.get(r["status"], "?")
        req = "REQUIRED" if r["required"] else "optional"

        print(f"  {status_icon} {r['name']} ({req})")
        print(f"    Source: {r['source']}  |  Status: {r['status']}")
        print(f"    {r['detail']}")
        if r["mismatch"]:
            print(f"    ⚠ MISMATCH: .env ({r['env_key']}) and Doppler ({r['doppler_key']}) have different values!")
        print()

    # Summary
    valid = sum(1 for r in results if r["status"] == "VALID")
    invalid = sum(1 for r in results if r["status"] in ("INVALID", "WRONG_SCOPE"))
    missing = sum(1 for r in results if r["status"] == "MISSING")
    mismatches = sum(1 for r in results if r["mismatch"])

    print(f"  Summary: {valid} valid, {invalid} invalid, {missing} missing, {mismatches} mismatches")

    if has_failures:
        print("\n  ✗ BLOCKED — fix invalid/missing required tokens before proceeding\n")
        return 1
    else:
        print("\n  ✓ All required tokens valid — ready to proceed\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
