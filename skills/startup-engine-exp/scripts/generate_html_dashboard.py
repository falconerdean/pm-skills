#!/usr/bin/env python3
"""
HTML CEO Dashboard Generator for the AI Startup Engine.
Generates a self-contained HTML dashboard that auto-refreshes every 5 minutes.
Opens in default browser.

Usage: python3 generate_html_dashboard.py --workspace ~/startup-workspace [--open]
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_jsonl(path: Path, days: int = 3) -> list:
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
                ts = entry.get("timestamp", entry.get("ts", ""))
                if ts:
                    try:
                        entry_time = datetime.fromisoformat(ts.replace("Z", ""))
                        if entry_time < cutoff:
                            continue
                    except (ValueError, TypeError):
                        pass
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def find_latest_file(directory: Path, pattern: str) -> Optional[Path]:
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[0] if files else None


def read_file_preview(path: Path, max_lines: int = 20) -> str:
    if not path or not path.exists():
        return ""
    with open(path) as f:
        lines = f.readlines()[:max_lines]
    return "".join(lines)


def count_files(directory: Path, pattern: str = "*") -> int:
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def phase_to_display(phase: str) -> dict:
    """Map phase key to display name and color."""
    mapping = {
        "continuous_intel": {"name": "Intel", "icon": "0", "color": "#6366f1"},
        "planning": {"name": "Planning", "icon": "1", "color": "#8b5cf6"},
        "research": {"name": "Research", "icon": "2", "color": "#a855f7"},
        "requirements": {"name": "Requirements", "icon": "3", "color": "#d946ef"},
        "ux_design": {"name": "UX/UI Design", "icon": "4", "color": "#ec4899"},
        "tech_design": {"name": "Tech Design", "icon": "5", "color": "#f43f5e"},
        "development": {"name": "Development", "icon": "6", "color": "#f97316"},
        "testing": {"name": "Testing", "icon": "7", "color": "#eab308"},
        "deployment": {"name": "Deployment", "icon": "8", "color": "#22c55e"},
        "growth": {"name": "Growth", "icon": "9", "color": "#14b8a6"},
        "evolution": {"name": "Evolution", "icon": "10", "color": "#06b6d4"},
    }
    return mapping.get(phase, {"name": phase, "icon": "?", "color": "#6b7280"})


def status_badge(status: str) -> str:
    colors = {
        "complete": ("DONE", "#16a34a", "#dcfce7"),
        "in_progress": ("ACTIVE", "#2563eb", "#dbeafe"),
        "pending": ("---", "#6b7280", "#f3f4f6"),
        "blocked": ("BLOCKED", "#dc2626", "#fee2e2"),
    }
    label, fg, bg = colors.get(status, (status, "#6b7280", "#f3f4f6"))
    return f'<span style="background:{bg};color:{fg};padding:2px 8px;font-size:11px;font-weight:600;letter-spacing:0.5px;">{label}</span>'


def generate_html(workspace: Path) -> str:
    state = load_json(workspace / "state" / "company_state.json")
    backlog = load_json(workspace / "state" / "backlog.json")
    sprint_state = load_json(workspace / "state" / "sprint_state.json")

    activity = load_jsonl(workspace / "logs" / "agent_activity.jsonl", days=3)
    decisions = load_jsonl(workspace / "logs" / "decisions.jsonl", days=3)
    cost_log = load_jsonl(workspace / "logs" / "costs.jsonl", days=3)

    sprint = state.get("sprint", {})
    sdlc = state.get("sdlc", {})
    quality = state.get("quality", {})
    costs = state.get("costs", {})
    blockers = state.get("blockers", [])
    ceo = state.get("ceo", {})
    agents_info = state.get("agents", {})
    company = state.get("company", {})

    current_phase = sdlc.get("current_phase", "unknown")
    phase_info = phase_to_display(current_phase)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Count artifacts
    artifact_count = count_files(workspace / "artifacts", "**/*.*")
    intel_count = count_files(workspace / "intel", "*.md")
    review_count = count_files(workspace / "reviews", "**/*.md")

    # Phase progress bar data
    phases_html = ""
    phase_order = ["planning", "research", "requirements", "ux_design", "tech_design",
                   "development", "testing", "deployment", "growth", "evolution"]
    for p in phase_order:
        pdata = sdlc.get("phases", {}).get(p, {})
        pstatus = pdata.get("status", "pending")
        pinfo = phase_to_display(p)
        is_current = (p == current_phase)

        if pstatus == "complete":
            bg = "#16a34a"
            text_color = "#fff"
        elif pstatus == "in_progress":
            bg = "#2563eb"
            text_color = "#fff"
        elif pstatus == "blocked":
            bg = "#dc2626"
            text_color = "#fff"
        else:
            bg = "#e5e7eb"
            text_color = "#6b7280"

        border = "3px solid #003d5c" if is_current else "1px solid #d1d5db"
        phases_html += f'''
        <div style="flex:1;text-align:center;padding:10px 4px;background:{bg};color:{text_color};
                    border:{border};font-size:11px;font-weight:600;min-width:0;">
            <div style="font-size:16px;margin-bottom:2px;">{pinfo["icon"]}</div>
            <div style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{pinfo["name"]}</div>
        </div>'''

    # Phase detail table
    phase_rows = ""
    for p in phase_order:
        pdata = sdlc.get("phases", {}).get(p, {})
        pinfo = phase_to_display(p)
        started = (pdata.get("started_at") or "-")[:16] if pdata.get("started_at") else "-"
        completed = (pdata.get("completed_at") or "-")[:16] if pdata.get("completed_at") else "-"
        phase_rows += f'''
        <tr>
            <td style="font-weight:500;">{pinfo["name"]}</td>
            <td>{status_badge(pdata.get("status", "pending"))}</td>
            <td style="font-size:12px;color:#6b7280;">{started}</td>
            <td style="font-size:12px;color:#6b7280;">{completed}</td>
        </tr>'''

    # Quality metrics
    quality_rows = ""
    for metric, value in quality.items():
        display = f"{value}" if value is not None else '<span style="color:#9ca3af;">N/A</span>'
        metric_name = metric.replace("_", " ").title()
        quality_rows += f"<tr><td>{metric_name}</td><td style='font-weight:600;'>{display}</td></tr>"

    # Blockers
    blockers_html = ""
    if blockers:
        for b in blockers:
            needs_ceo = b.get("needs_ceo", False)
            badge = '<span style="background:#fee2e2;color:#dc2626;padding:1px 6px;font-size:10px;font-weight:600;">CEO ACTION</span>' if needs_ceo else ""
            blockers_html += f'''
            <div style="padding:12px;border-left:3px solid #dc2626;background:#fef2f2;margin-bottom:8px;">
                <div style="font-weight:600;">{b.get("description", "Unknown blocker")} {badge}</div>
                <div style="font-size:12px;color:#6b7280;margin-top:4px;">
                    Phase: {b.get("phase", "?")} | Blocked for: {b.get("cycles", "?")} cycles |
                    Suggestion: {b.get("suggestion", "N/A")}
                </div>
            </div>'''
    else:
        blockers_html = '<div style="padding:16px;text-align:center;color:#16a34a;font-weight:500;">No blockers. All systems nominal.</div>'

    # Decisions
    decisions_html = ""
    if decisions:
        for d in decisions[-8:]:
            ts = (d.get("timestamp", "")[:16]) if d.get("timestamp") else "?"
            decisions_html += f'''
            <div style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">
                <div style="display:flex;justify-content:space-between;">
                    <span style="font-weight:600;font-size:13px;">{d.get("agent", "?")}</span>
                    <span style="font-size:11px;color:#9ca3af;">{ts}</span>
                </div>
                <div style="font-size:13px;margin-top:2px;">{d.get("decision", "?")}</div>
            </div>'''
    else:
        decisions_html = '<div style="padding:16px;text-align:center;color:#9ca3af;">No autonomous decisions yet.</div>'

    # Pending CEO actions
    pending = ceo.get("pending_approvals", [])
    pending_html = ""
    if pending:
        for p_item in pending:
            pending_html += f'''
            <div style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">
                <input type="checkbox" disabled style="margin-right:8px;">
                <span style="font-size:13px;">{p_item}</span>
            </div>'''
    else:
        pending_html = '<div style="padding:16px;text-align:center;color:#16a34a;">No pending actions.</div>'

    # Activity feed
    activity_html = ""
    if activity:
        for a in activity[-12:]:
            ts = (a.get("timestamp", "")[:16]) if a.get("timestamp") else "?"
            activity_html += f'''
            <div style="padding:6px 12px;border-bottom:1px solid #f3f4f6;font-size:12px;">
                <span style="color:#9ca3af;">{ts}</span>
                <span style="margin-left:8px;font-weight:500;">{a.get("agent", "?")}</span>
                <span style="margin-left:4px;color:#4b5563;">{a.get("action", a.get("description", "?"))}</span>
            </div>'''
    else:
        activity_html = '<div style="padding:16px;text-align:center;color:#9ca3af;">No activity logged yet.</div>'

    # Cost gauge
    budget = 750
    monthly = costs.get("monthly_total", 0)
    cost_pct = min((monthly / budget) * 100, 100) if budget > 0 else 0
    cost_color = "#16a34a" if cost_pct < 60 else "#eab308" if cost_pct < 80 else "#dc2626"

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="300">
    <title>CEO Dashboard — {company.get("name", "AI Startup")}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 14px;
               line-height: 1.5; color: #1a1a1a; background: #f8f9fa; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; min-height: 100vh; }}
        .header {{ background: #003d5c; color: white; padding: 20px 30px; border-bottom: 3px solid #002840; }}
        .header h1 {{ font-size: 22px; font-weight: 600; letter-spacing: -0.5px; }}
        .header-meta {{ font-size: 12px; color: #b8d4e6; display: flex; gap: 20px; margin-top: 6px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 0;
                    border-bottom: 2px solid #003d5c; }}
        .metric {{ padding: 16px 20px; background: #f8f9fa; border-right: 1px solid #d1d5db;
                  text-align: center; }}
        .metric:last-child {{ border-right: none; }}
        .metric-number {{ font-size: 28px; font-weight: 700; color: #003d5c; display: block; }}
        .metric-label {{ font-size: 10px; color: #4a5568; text-transform: uppercase;
                        letter-spacing: 0.5px; font-weight: 500; }}
        .grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 0; }}
        .section {{ padding: 20px 24px; border-bottom: 1px solid #e5e7eb; }}
        .section-title {{ font-size: 13px; font-weight: 700; text-transform: uppercase;
                         letter-spacing: 0.5px; color: #003d5c; margin-bottom: 12px;
                         padding-bottom: 6px; border-bottom: 2px solid #003d5c; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
             color: #6b7280; padding: 6px 8px; border-bottom: 1px solid #d1d5db; }}
        td {{ padding: 8px; border-bottom: 1px solid #f3f4f6; font-size: 13px; }}
        .sidebar {{ border-left: 1px solid #e5e7eb; }}
        .progress-bar {{ display: flex; gap: 2px; margin-bottom: 16px; }}
        .cost-bar {{ height: 8px; background: #e5e7eb; margin-top: 8px; }}
        .cost-fill {{ height: 100%; transition: width 0.5s; }}
        .refresh-note {{ text-align: center; padding: 8px; font-size: 11px; color: #9ca3af;
                        background: #f8f9fa; border-top: 1px solid #e5e7eb; }}
    </style>
</head>
<body>
<div class="container">
    <!-- Header -->
    <div class="header">
        <h1>CEO Dashboard — {company.get("name", "AI Startup")}</h1>
        <div class="header-meta">
            <span>Sprint #{sprint.get("number", "?")}</span>
            <span>Epic: {sprint.get("epic", "None")}</span>
            <span>Phase: {phase_info["name"]}</span>
            <span>Generated: {now}</span>
        </div>
    </div>

    <!-- Top Metrics -->
    <div class="metrics">
        <div class="metric">
            <span class="metric-number">{sprint.get("number", 0)}</span>
            <span class="metric-label">Sprint</span>
        </div>
        <div class="metric">
            <span class="metric-number" style="color:{phase_info['color']};">{sdlc.get("phase_number", "?")}/10</span>
            <span class="metric-label">Phase</span>
        </div>
        <div class="metric">
            <span class="metric-number">{agents_info.get("coo_cycles_completed", 0)}</span>
            <span class="metric-label">COO Cycles</span>
        </div>
        <div class="metric">
            <span class="metric-number">{len(activity)}</span>
            <span class="metric-label">Agent Actions (3d)</span>
        </div>
        <div class="metric">
            <span class="metric-number" style="color:{cost_color};">${monthly:.0f}</span>
            <span class="metric-label">Cost (Monthly)</span>
        </div>
        <div class="metric">
            <span class="metric-number" style="color:{"#dc2626" if len(blockers) > 0 else "#16a34a"};">{len(blockers)}</span>
            <span class="metric-label">Blockers</span>
        </div>
    </div>

    <!-- Phase Progress Bar -->
    <div style="padding:16px 24px;border-bottom:1px solid #e5e7eb;">
        <div style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:#6b7280;margin-bottom:8px;">SDLC Progress</div>
        <div class="progress-bar">{phases_html}</div>
    </div>

    <!-- Main Grid -->
    <div class="grid">
        <!-- Left Column -->
        <div>
            <!-- Phase Detail -->
            <div class="section">
                <div class="section-title">Phase Status</div>
                <table>
                    <tr><th>Phase</th><th>Status</th><th>Started</th><th>Completed</th></tr>
                    {phase_rows}
                </table>
            </div>

            <!-- Blockers -->
            <div class="section">
                <div class="section-title">Blockers & Escalations</div>
                {blockers_html}
            </div>

            <!-- Autonomous Decisions -->
            <div class="section">
                <div class="section-title">Autonomous Decisions (Last 3 Days)</div>
                {decisions_html}
            </div>

            <!-- Activity Feed -->
            <div class="section">
                <div class="section-title">Agent Activity Feed</div>
                {activity_html}
            </div>
        </div>

        <!-- Right Sidebar -->
        <div class="sidebar">
            <!-- CEO Actions -->
            <div class="section">
                <div class="section-title" style="color:#dc2626;border-color:#dc2626;">Pending CEO Actions</div>
                {pending_html}
            </div>

            <!-- Quality -->
            <div class="section">
                <div class="section-title">Quality Metrics</div>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    {quality_rows}
                </table>
            </div>

            <!-- Cost -->
            <div class="section">
                <div class="section-title">Cost Budget</div>
                <table>
                    <tr><td>This Sprint</td><td style="font-weight:600;">${costs.get("sprint_total", 0):.2f}</td></tr>
                    <tr><td>This 3-Day Cycle</td><td style="font-weight:600;">${costs.get("cycle_total", 0):.2f}</td></tr>
                    <tr><td>Monthly Total</td><td style="font-weight:600;">${monthly:.2f}</td></tr>
                    <tr><td>Budget Remaining</td><td style="font-weight:700;color:{cost_color};">${costs.get("budget_remaining", 750):.2f}</td></tr>
                </table>
                <div class="cost-bar">
                    <div class="cost-fill" style="width:{cost_pct:.0f}%;background:{cost_color};"></div>
                </div>
                <div style="text-align:right;font-size:11px;color:#9ca3af;margin-top:4px;">{cost_pct:.0f}% of $750 budget</div>
            </div>

            <!-- Artifacts -->
            <div class="section">
                <div class="section-title">Workspace Stats</div>
                <table>
                    <tr><td>Artifacts</td><td style="font-weight:600;">{artifact_count}</td></tr>
                    <tr><td>Intel Reports</td><td style="font-weight:600;">{intel_count}</td></tr>
                    <tr><td>Reviews</td><td style="font-weight:600;">{review_count}</td></tr>
                    <tr><td>Total Agents Spawned</td><td style="font-weight:600;">{agents_info.get("total_spawned", 0)}</td></tr>
                </table>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <div class="refresh-note">
        Auto-refreshes every 5 minutes | Regenerate: python3 generate_html_dashboard.py --workspace ~/startup-workspace --open
    </div>
</div>
</body>
</html>'''

    return html


def main():
    auto_open = "--open" in sys.argv
    if "--workspace" not in sys.argv:
        print("Usage: python3 generate_html_dashboard.py --workspace ~/startup-workspace [--open]")
        sys.exit(1)

    ws_idx = sys.argv.index("--workspace")
    workspace = Path(sys.argv[ws_idx + 1]).expanduser()

    if not workspace.exists():
        print(f"ERROR: Workspace not found: {workspace}")
        sys.exit(1)

    html = generate_html(workspace)

    # Write dashboard
    reviews_dir = workspace / "reviews" / "ceo_reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    output_file = reviews_dir / "dashboard.html"
    with open(output_file, "w") as f:
        f.write(html)

    print(f"Dashboard written to: {output_file}")

    if auto_open:
        if sys.platform == "darwin":
            subprocess.run(["open", str(output_file)])
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", str(output_file)])
        print("Dashboard opened in browser.")


if __name__ == "__main__":
    main()
