"""
GRC Alerting — Slack & Microsoft Teams Webhook Notifications

Sends push alerts when GRC conditions breach thresholds:
  • Expired or expiring evidence artifacts
  • Overdue control tests
  • Open Major Non-Conformity findings

Environment variables (both optional — alerting is gracefully skipped if unset):
  SLACK_WEBHOOK_URL   Slack Incoming Webhook URL
  TEAMS_WEBHOOK_URL   Microsoft Teams Incoming Webhook URL

SWOT Remediation (Prompt 8 — 2026-04-07):
  Added send_webhook_alert(), run_alert_checks(), and send_test_alert().
"""

import json
import logging
import os
from datetime import date
from typing import Optional

try:
    import requests as _requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

SLACK_WEBHOOK_URL  = os.environ.get("SLACK_WEBHOOK_URL", "")
TEAMS_WEBHOOK_URL  = os.environ.get("TEAMS_WEBHOOK_URL", "")

# Alert severity → Slack colour attachment colour
_SLACK_COLOURS = {
    "critical": "#FF0000",
    "warning":  "#FFA500",
    "info":     "#36A64F",
}

# ─────────────────────────────────────────────────────────────────────────────
# WEBHOOK TRANSPORT
# ─────────────────────────────────────────────────────────────────────────────

def _post_slack(url: str, title: str, body: str, level: str = "warning") -> bool:
    """
    Post a message to a Slack Incoming Webhook.
    Returns True on success, False on failure.
    """
    if not _REQUESTS_AVAILABLE:
        logger.warning("[Alert/Slack] requests library not installed — cannot send.")
        return False

    colour  = _SLACK_COLOURS.get(level, _SLACK_COLOURS["warning"])
    payload = {
        "attachments": [
            {
                "color":  colour,
                "title":  title,
                "text":   body,
                "footer": f"ISO 27001 GRC Automation · {date.today().isoformat()}",
            }
        ]
    }
    try:
        resp = _requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("[Alert/Slack] Message sent: %s", title)
            return True
        logger.warning("[Alert/Slack] Non-200 response (%d): %s",
                       resp.status_code, resp.text[:200])
        return False
    except Exception as exc:
        logger.error("[Alert/Slack] Failed to send: %s", exc)
        return False


def _post_teams(url: str, title: str, body: str, level: str = "warning") -> bool:
    """
    Post a message to a Microsoft Teams Incoming Webhook.
    Returns True on success, False on failure.
    """
    if not _REQUESTS_AVAILABLE:
        logger.warning("[Alert/Teams] requests library not installed — cannot send.")
        return False

    colour_map = {"critical": "FF0000", "warning": "FFA500", "info": "36A64F"}
    colour     = colour_map.get(level, colour_map["warning"])

    payload = {
        "@type":      "MessageCard",
        "@context":   "http://schema.org/extensions",
        "themeColor": colour,
        "summary":    title,
        "sections": [
            {
                "activityTitle":    f"**{title}**",
                "activitySubtitle": f"ISO 27001 GRC Automation · {date.today().isoformat()}",
                "text":             body,
            }
        ],
    }
    try:
        resp = _requests.post(url, json=payload, timeout=10)
        if resp.status_code in (200, 202):
            logger.info("[Alert/Teams] Message sent: %s", title)
            return True
        logger.warning("[Alert/Teams] Non-200 response (%d): %s",
                       resp.status_code, resp.text[:200])
        return False
    except Exception as exc:
        logger.error("[Alert/Teams] Failed to send: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def send_webhook_alert(title: str, body: str, level: str = "warning") -> dict:
    """
    Send an alert to all configured webhooks.

    Args:
        title:  Short summary headline.
        body:   Detailed message body (plain text).
        level:  'info' | 'warning' | 'critical'

    Returns:
        Dict with keys 'slack' and 'teams', each True/False/None (None = not configured).
    """
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", SLACK_WEBHOOK_URL)
    teams_url = os.environ.get("TEAMS_WEBHOOK_URL", TEAMS_WEBHOOK_URL)

    results = {"slack": None, "teams": None}

    if slack_url:
        results["slack"] = _post_slack(slack_url, title, body, level)
    else:
        logger.debug("[Alert] SLACK_WEBHOOK_URL not set — skipping Slack notification.")

    if teams_url:
        results["teams"] = _post_teams(teams_url, title, body, level)
    else:
        logger.debug("[Alert] TEAMS_WEBHOOK_URL not set — skipping Teams notification.")

    if results["slack"] is None and results["teams"] is None:
        logger.info("[Alert] No webhooks configured. Set SLACK_WEBHOOK_URL or "
                    "TEAMS_WEBHOOK_URL to enable push notifications.")

    return results


def send_test_alert() -> dict:
    """
    Send a test notification to all configured webhooks.
    Used by --alert-test CLI flag to verify webhook connectivity.
    """
    title = "✅ GRC Alert Test"
    body  = (
        "This is a test notification from the ISO 27001 GRC Automation Framework.\n"
        "If you received this message, your webhook is configured correctly.\n\n"
        f"Sent at: {date.today().isoformat()}"
    )
    results = send_webhook_alert(title, body, level="info")
    _log_alert_results(results, "test")
    return results


def run_alert_checks(days_ahead: int = 30, major_nc_threshold: int = 0) -> dict:
    """
    Run all GRC alert condition checks and fire notifications for any breaches.

    Checks performed:
      1. Expired artifacts (already past expiry date)
      2. Expiring artifacts (expiring within `days_ahead` days)
      3. Overdue control tests (next_test_date has passed)
      4. Open Major Non-Conformity findings (count > major_nc_threshold)

    Returns a dict summarising what was checked and which alerts fired.
    """
    from grc_engine import get_expiring_artifacts, get_overdue_tests, get_open_findings

    fired   = []
    summary = {}

    # ── 1. Expired artifacts ──────────────────────────────────────────────────
    today         = date.today().isoformat()
    all_expiring  = get_expiring_artifacts(days_ahead=days_ahead)
    expired       = [a for a in all_expiring if a.get("expiry_date", "") < today]
    soon_expiring = [a for a in all_expiring if a.get("expiry_date", "") >= today]

    if expired:
        names = "\n".join(
            f"  • {a['artifact_name']} (expired {a['expiry_date']})"
            for a in expired[:10]
        )
        more  = f"\n  … and {len(expired) - 10} more" if len(expired) > 10 else ""
        results = send_webhook_alert(
            title=f"🔴 {len(expired)} Evidence Artifact(s) EXPIRED",
            body=(
                f"{len(expired)} artifact(s) have passed their expiry date and "
                f"must be recollected urgently:\n{names}{more}"
            ),
            level="critical",
        )
        fired.append("expired_artifacts")
        summary["expired_artifacts"] = {"count": len(expired), "alert": results}

    if soon_expiring:
        names = "\n".join(
            f"  • {a['artifact_name']} (expires {a['expiry_date']})"
            for a in soon_expiring[:10]
        )
        more  = f"\n  … and {len(soon_expiring) - 10} more" if len(soon_expiring) > 10 else ""
        results = send_webhook_alert(
            title=f"⚠️ {len(soon_expiring)} Evidence Artifact(s) Expiring Within {days_ahead} Days",
            body=(
                f"{len(soon_expiring)} artifact(s) will expire within "
                f"{days_ahead} days:\n{names}{more}"
            ),
            level="warning",
        )
        fired.append("expiring_artifacts")
        summary["expiring_artifacts"] = {"count": len(soon_expiring), "alert": results}

    # ── 2. Overdue control tests ───────────────────────────────────────────────
    overdue = get_overdue_tests()
    if overdue:
        lines = "\n".join(
            f"  • {o['control_id']}: {o['title'][:50]} (due {o['next_test_date'][:10]})"
            for o in overdue[:10]
        )
        more  = f"\n  … and {len(overdue) - 10} more" if len(overdue) > 10 else ""
        results = send_webhook_alert(
            title=f"⚠️ {len(overdue)} Control Test(s) Overdue",
            body=(
                f"{len(overdue)} control(s) are overdue for re-testing:\n{lines}{more}"
            ),
            level="warning",
        )
        fired.append("overdue_tests")
        summary["overdue_tests"] = {"count": len(overdue), "alert": results}

    # ── 3. Open Major Non-Conformities ─────────────────────────────────────────
    open_findings = get_open_findings()
    major_ncs     = [f for f in open_findings if f.get("severity") == "Major"]
    if len(major_ncs) > major_nc_threshold:
        lines = "\n".join(
            f"  • [{f['finding_id']}] {f['title'][:55]} ({f.get('audit_id', 'N/A')})"
            for f in major_ncs[:10]
        )
        more  = f"\n  … and {len(major_ncs) - 10} more" if len(major_ncs) > 10 else ""
        results = send_webhook_alert(
            title=f"🔴 {len(major_ncs)} Open Major Non-Conformit{'y' if len(major_ncs) == 1 else 'ies'}",
            body=(
                f"{len(major_ncs)} Major NC(s) are currently open and require "
                f"immediate attention:\n{lines}{more}"
            ),
            level="critical",
        )
        fired.append("major_ncs")
        summary["major_ncs"] = {"count": len(major_ncs), "alert": results}

    if not fired:
        logger.info("[Alert] All checks passed — no alert conditions detected.")
    else:
        logger.warning("[Alert] %d alert condition(s) fired: %s", len(fired), fired)

    summary["checks_fired"] = fired
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _log_alert_results(results: dict, context: str = ""):
    prefix = f"[Alert/{context}]" if context else "[Alert]"
    for channel, ok in results.items():
        if ok is None:
            logger.info("%s %s: not configured", prefix, channel.capitalize())
        elif ok:
            logger.info("%s %s: sent successfully", prefix, channel.capitalize())
        else:
            logger.warning("%s %s: send FAILED", prefix, channel.capitalize())
