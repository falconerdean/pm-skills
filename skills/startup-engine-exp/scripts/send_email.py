#!/usr/bin/env python3
"""
Send CEO email notifications via GoHighLevel API (MCP).

This script is called by the startup engine to notify the CEO at checkpoints,
blockers, retros, and any time the engine is waiting.

It sends emails through the GoHighLevel conversations API, which handles
delivery via GHL's configured email provider — no SMTP setup needed.

Usage from Claude Code agents:
    The agent should call the GHL MCP tool directly:

    mcp__GoHighLevel__conversations_send-a-new-message(
        body_type="Email",
        body_contactId="M6SGycSNsrBUq2Elzn6o",
        body_emailTo="dean@try-insite.com",
        body_subject="[Startup Engine] Subject here",
        body_html="<html>...</html>"
    )

Usage from bash (generates the HTML and prints the MCP call params):
    python3 send_email.py --type retro --product "MyApp" --sprint 3 --details "<p>Summary</p>"
    python3 send_email.py --type ceo_gate --product "MyApp" --phase "Deployment" --details "Ready to deploy"
    python3 send_email.py --type blocker --product "MyApp" --phase "Testing" --details "Tests failing"

GHL Configuration:
    Contact ID: M6SGycSNsrBUq2Elzn6o (dean falconer)
    Email: dean@try-insite.com
    Location: lziB58iPKyFrOb8uQsNd
"""

import argparse
import json
import sys
from datetime import datetime, timezone

# CEO contact in GoHighLevel
CEO_CONTACT_ID = "M6SGycSNsrBUq2Elzn6o"
CEO_EMAIL = "dean@try-insite.com"


def build_notification_html(event_type, product_name, details):
    """Build a clean HTML email for engine notifications."""
    colors = {
        "ceo_gate": "#003d5c",
        "waiting": "#b45309",
        "retro": "#065f46",
        "blocker": "#991b1b",
        "budget": "#991b1b",
        "stall": "#b45309",
        "info": "#1e40af",
    }
    color = colors.get(event_type, "#003d5c")

    labels = {
        "ceo_gate": "CEO REVIEW REQUIRED",
        "waiting": "WAITING ON CEO",
        "retro": "SPRINT RETRO COMPLETE",
        "blocker": "BLOCKER ALERT",
        "budget": "BUDGET ALERT",
        "stall": "STALL DETECTED",
        "info": "STATUS UPDATE",
    }
    label = labels.get(event_type, "NOTIFICATION")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 20px;">
<div style="background: {color}; color: white; padding: 16px 20px; margin-bottom: 0;">
    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; margin-bottom: 4px;">Startup Engine</div>
    <div style="font-size: 20px; font-weight: 600;">{label}</div>
    <div style="font-size: 12px; opacity: 0.7; margin-top: 4px;">{product_name} | {timestamp}</div>
</div>
<div style="background: #f8f9fa; padding: 20px; border-left: 4px solid {color}; margin-bottom: 20px;">
{details}
</div>
<div style="font-size: 11px; color: #6b7280; border-top: 1px solid #e5e7eb; padding-top: 12px;">
    Sent by Startup Engine via GoHighLevel. Use <code>/btw</code> in Claude Code to respond.
</div>
</div>"""


def build_subject(event_type, product_name, extra=""):
    """Build email subject line."""
    prefixes = {
        "ceo_gate": "[Action Required]",
        "waiting": "[Waiting]",
        "retro": "[Retro]",
        "blocker": "[Blocker]",
        "budget": "[Budget]",
        "stall": "[Stall]",
        "info": "[Info]",
    }
    prefix = prefixes.get(event_type, "[Engine]")
    suffix = f" — {extra}" if extra else ""
    return f"{prefix} {product_name}{suffix}"


# --- Pre-built notification types ---

def build_ceo_gate(product_name, phase, summary):
    details = f"""<h3 style="margin: 0 0 12px 0; color: #003d5c;">Phase {phase} Complete — Your Approval Needed</h3>
<p>{summary}</p>
<p style="margin-top: 16px;"><strong>To approve:</strong> SSH into the droplet and run <code>/btw approve</code></p>"""
    return {
        "subject": build_subject("ceo_gate", product_name, f"Phase {phase} needs CEO approval"),
        "html": build_notification_html("ceo_gate", product_name, details),
    }


def build_waiting(product_name, reason):
    details = f"""<h3 style="margin: 0 0 12px 0; color: #b45309;">Engine Paused — Waiting on You</h3>
<p>{reason}</p>
<p style="margin-top: 16px;"><strong>To resume:</strong> Address the above and run <code>/btw resume</code></p>"""
    return {
        "subject": build_subject("waiting", product_name, "Engine paused, needs CEO input"),
        "html": build_notification_html("waiting", product_name, details),
    }


def build_blocker(product_name, phase, description):
    details = f"""<h3 style="margin: 0 0 12px 0; color: #991b1b;">Blocker in Phase {phase}</h3>
<p>{description}</p>
<p style="margin-top: 16px;"><strong>To resolve:</strong> <code>/btw blocker resolve</code> or <code>/btw skip-phase</code></p>"""
    return {
        "subject": build_subject("blocker", product_name, f"Phase {phase} blocked"),
        "html": build_notification_html("blocker", product_name, details),
    }


def build_budget(product_name, spent, budget):
    details = f"""<h3 style="margin: 0 0 12px 0; color: #991b1b;">Budget Limit Reached</h3>
<p>Sprint spending: <strong>${spent:.2f}</strong> / ${budget:.2f} budget</p>
<p>The engine has been paused to prevent further spending.</p>
<p style="margin-top: 16px;"><strong>To resume:</strong> <code>/btw budget {budget * 2:.0f}</code> and remove STOP file.</p>"""
    return {
        "subject": build_subject("budget", product_name, f"Sprint budget exceeded (${spent:.2f}/${budget:.2f})"),
        "html": build_notification_html("budget", product_name, details),
    }


def build_stall(product_name, phase, cycles_stuck, last_activity):
    details = f"""<h3 style="margin: 0 0 12px 0; color: #b45309;">Phase {phase} Stalled</h3>
<p>Same phase for <strong>{cycles_stuck} consecutive COO cycles</strong> ({cycles_stuck * 30} minutes) with no new artifacts.</p>
<p>Last activity: {last_activity}</p>
<p style="margin-top: 16px;"><strong>To investigate:</strong> <code>/btw status</code> then <code>/btw skip-phase</code> if needed.</p>"""
    return {
        "subject": build_subject("stall", product_name, f"Phase {phase} stuck for {cycles_stuck * 30}min"),
        "html": build_notification_html("stall", product_name, details),
    }


def build_retro(product_name, sprint_num, summary_html):
    details = f"""<h3 style="margin: 0 0 12px 0; color: #065f46;">Sprint {sprint_num} Complete</h3>
{summary_html}
<p style="margin-top: 16px;">Full retro in repo: <code>.claude-engine/reviews/retrospectives/</code></p>"""
    return {
        "subject": build_subject("retro", product_name, f"Sprint {sprint_num} retrospective"),
        "html": build_notification_html("retro", product_name, details),
    }


def print_mcp_call(subject, html):
    """Print the MCP tool call parameters as JSON for agents to use."""
    call = {
        "tool": "mcp__GoHighLevel__conversations_send-a-new-message",
        "params": {
            "body_type": "Email",
            "body_contactId": CEO_CONTACT_ID,
            "body_emailTo": CEO_EMAIL,
            "body_subject": subject,
            "body_html": html,
        }
    }
    print(json.dumps(call, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build CEO notification email for Startup Engine (via GHL)")
    parser.add_argument("--type", required=True,
                        choices=["ceo_gate", "waiting", "blocker", "budget", "stall", "retro"],
                        help="Notification type")
    parser.add_argument("--product", default="Startup", help="Product name")
    parser.add_argument("--phase", help="Phase name")
    parser.add_argument("--details", help="Details text/HTML")
    parser.add_argument("--spent", type=float, help="Amount spent (budget type)")
    parser.add_argument("--budget-limit", type=float, help="Budget limit (budget type)")
    parser.add_argument("--sprint", type=int, help="Sprint number (retro type)")
    parser.add_argument("--cycles", type=int, help="Cycles stuck (stall type)")
    parser.add_argument("--json", action="store_true", help="Output MCP call params as JSON")

    args = parser.parse_args()

    if args.type == "ceo_gate":
        result = build_ceo_gate(args.product, args.phase or "Unknown", args.details or "Review needed.")
    elif args.type == "waiting":
        result = build_waiting(args.product, args.details or "Waiting for CEO input.")
    elif args.type == "blocker":
        result = build_blocker(args.product, args.phase or "Unknown", args.details or "Blocker detected.")
    elif args.type == "budget":
        result = build_budget(args.product, args.spent or 0, args.budget_limit or 150)
    elif args.type == "stall":
        result = build_stall(args.product, args.phase or "Unknown", args.cycles or 6, args.details or "No recent activity")
    elif args.type == "retro":
        result = build_retro(args.product, args.sprint or 0, args.details or "<p>Sprint complete.</p>")

    if args.json:
        print_mcp_call(result["subject"], result["html"])
    else:
        # Print the subject and HTML so agents can use them directly
        print(f"SUBJECT: {result['subject']}")
        print(f"CONTACT_ID: {CEO_CONTACT_ID}")
        print(f"EMAIL_TO: {CEO_EMAIL}")
        print("---HTML---")
        print(result["html"])
