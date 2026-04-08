#!/usr/bin/env python3
"""
CEO Dashboard Generator for the AI Startup Engine.
Reads workspace state and produces an executive summary.

Usage: python3 generate_dashboard.py --workspace ~/startup-workspace
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_jsonl(path: Path, days: int = 3) -> list:
    """Load JSONL file, optionally filtering to last N days."""
    if not path.exists():
        return []
    entries = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                # Try to filter by timestamp if present
                ts = entry.get("timestamp", entry.get("ts", ""))
                if ts:
                    try:
                        entry_time = datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))
                        if entry_time < cutoff:
                            continue
                    except (ValueError, TypeError):
                        pass
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def find_latest_file(directory: Path, pattern: str) -> Path | None:
    """Find the most recently modified file matching a pattern."""
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def generate_dashboard(workspace: Path) -> str:
    state = load_json(workspace / "state" / "company_state.json")
    if not state:
        return "# CEO Dashboard\n\nNo company state found. Run /startup-engine to initialize."

    sprint = state.get("sprint", {})
    sdlc = state.get("sdlc", {})
    quality = state.get("quality", {})
    costs = state.get("costs", {})
    blockers = state.get("blockers", [])
    ceo = state.get("ceo", {})
    agents = state.get("agents", {})

    # Load logs
    activity = load_jsonl(workspace / "logs" / "agent_activity.jsonl", days=3)
    decisions = load_jsonl(workspace / "logs" / "decisions.jsonl", days=3)
    cost_log = load_jsonl(workspace / "logs" / "costs.jsonl", days=3)

    # Find latest intel
    latest_competitive = find_latest_file(workspace / "intel", "competitive_report_*.md")
    latest_market = find_latest_file(workspace / "intel", "market_pulse_*.md")

    # Build dashboard
    lines = []
    lines.append("# CEO Dashboard")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Section 1: Status at a Glance
    lines.append("## 1. Status at a Glance")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Sprint | #{sprint.get('number', '?')} — {sprint.get('epic', 'No epic')} |")
    lines.append(f"| Phase | {sdlc.get('current_phase', '?')} ({sdlc.get('phase_number', '?')}/10) |")
    lines.append(f"| Started | {sprint.get('started_at', 'N/A')} |")
    lines.append(f"| COO Cycles | {agents.get('coo_cycles_completed', 0)} |")
    lines.append(f"| Blockers | {len(blockers)} |")
    lines.append(f"| Pending Approvals | {len(ceo.get('pending_approvals', []))} |")
    lines.append("")

    # Section 2: Phase Progress
    lines.append("## 2. Phase Progress")
    lines.append("")
    lines.append("| Phase | Status | Started | Completed |")
    lines.append("|-------|--------|---------|-----------|")
    for phase_name, phase_data in sdlc.get("phases", {}).items():
        status = phase_data.get("status", "pending")
        started = phase_data.get("started_at", "-") or "-"
        completed = phase_data.get("completed_at", "-") or "-"
        if isinstance(started, str) and len(started) > 16:
            started = started[:16]
        if isinstance(completed, str) and len(completed) > 16:
            completed = completed[:16]
        status_icon = {"complete": "DONE", "in_progress": "ACTIVE", "pending": "---", "blocked": "BLOCKED"}.get(status, status)
        lines.append(f"| {phase_name} | {status_icon} | {started} | {completed} |")
    lines.append("")

    # Section 3: Decisions Made
    lines.append("## 3. Autonomous Decisions (Last 3 Days)")
    lines.append("")
    if decisions:
        for d in decisions[-10:]:  # Last 10 decisions
            lines.append(f"- **{d.get('agent', '?')}** ({d.get('timestamp', '?')[:16]}): {d.get('decision', '?')}")
            if d.get('rationale'):
                lines.append(f"  - Rationale: {d['rationale']}")
    else:
        lines.append("No autonomous decisions logged yet.")
    lines.append("")

    # Section 4: Quality Metrics
    lines.append("## 4. Quality Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for metric, value in quality.items():
        display = value if value is not None else "N/A"
        lines.append(f"| {metric.replace('_', ' ').title()} | {display} |")
    lines.append("")

    # Section 5: Costs
    lines.append("## 5. Cost Report")
    lines.append("")
    lines.append(f"| Period | Amount | Budget |")
    lines.append(f"|--------|--------|--------|")
    lines.append(f"| This Sprint | ${costs.get('sprint_total', 0):.2f} | $150 |")
    lines.append(f"| This 3-Day Cycle | ${costs.get('cycle_total', 0):.2f} | $300 |")
    lines.append(f"| Monthly Total | ${costs.get('monthly_total', 0):.2f} | $750 |")
    lines.append(f"| **Budget Remaining** | **${costs.get('budget_remaining', 750):.2f}** | |")
    lines.append("")

    # Section 6: Blockers
    lines.append("## 6. Blockers & Escalations")
    lines.append("")
    if blockers:
        for b in blockers:
            lines.append(f"- **{b.get('description', '?')}**")
            lines.append(f"  - Phase: {b.get('phase', '?')}")
            lines.append(f"  - Cycles blocked: {b.get('cycles', '?')}")
            lines.append(f"  - Suggested fix: {b.get('suggestion', 'N/A')}")
            lines.append(f"  - CEO action needed: {'YES' if b.get('needs_ceo', False) else 'No'}")
    else:
        lines.append("No blockers. All systems nominal.")
    lines.append("")

    # Section 7: Pending CEO Actions
    lines.append("## 7. Pending CEO Actions")
    lines.append("")
    pending = ceo.get("pending_approvals", [])
    if pending:
        for p in pending:
            lines.append(f"- [ ] {p}")
    else:
        lines.append("No pending actions. Company is operating autonomously.")
    lines.append("")

    # Section 8: Intel Summary
    lines.append("## 8. Latest Intelligence")
    lines.append("")
    if latest_competitive:
        lines.append(f"- Latest competitive report: `{latest_competitive.name}`")
    if latest_market:
        lines.append(f"- Latest market pulse: `{latest_market.name}`")
    if not latest_competitive and not latest_market:
        lines.append("No intelligence reports generated yet.")
    lines.append("")

    # Section 9: Agent Activity
    lines.append("## 9. Agent Activity (Last 3 Days)")
    lines.append("")
    lines.append(f"- Total agent invocations: {len(activity)}")
    lines.append(f"- COO cycles completed: {agents.get('coo_cycles_completed', 0)}")
    lines.append(f"- Total agents spawned (lifetime): {agents.get('total_spawned', 0)}")
    lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--workspace":
        print("Usage: python3 generate_dashboard.py --workspace ~/startup-workspace")
        sys.exit(1)

    workspace = Path(sys.argv[2]).expanduser()
    if not workspace.exists():
        print(f"ERROR: Workspace not found: {workspace}")
        sys.exit(1)

    dashboard = generate_dashboard(workspace)

    # Write to file
    reviews_dir = workspace / "reviews" / "ceo_reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_file = reviews_dir / f"dashboard_{date_str}.md"
    with open(output_file, "w") as f:
        f.write(dashboard)

    print(f"Dashboard written to: {output_file}")
    print("")
    print("=== QUICK SUMMARY ===")
    # Print first 20 lines as preview
    for line in dashboard.split("\n")[:25]:
        print(line)


if __name__ == "__main__":
    main()
