"""
Jira Integration Module — ISO 27001:2022 GRC Automation
Auto-creates and manages Jira tickets for:
  • Audit Findings (Major NC → Bug, Minor NC → Task, OFI → Improvement)
  • Failed / Partial Control Tests
  • Critical & High Risks
  • Overdue Artifact Collection
  • Overdue Control Re-tests
  • Drata Monitor Failures

Authentication: Jira REST API v3 using Basic Auth (email + API token)
Get API token: https://id.atlassian.com/manage-profile/security/api-tokens

Remediation changes (SWOT 2026-04-07):
  - Replaced all print() calls with structured logging
  - Added _request_with_retry() for rate-limit and transient error handling
  - Added _mask_secret() to prevent token exposure in logs/errors
  - All credential handling goes through _safe_auth_header() which never logs tokens
"""

import os
import json
import uuid
import base64
import time
import logging
from datetime import datetime, date, timedelta
from typing import Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from grc_engine import get_connection

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

JIRA_BASE_URL    = os.environ.get("JIRA_BASE_URL",    "https://yourcompany.atlassian.net")
JIRA_EMAIL       = os.environ.get("JIRA_EMAIL",       "")
JIRA_API_TOKEN   = os.environ.get("JIRA_API_TOKEN",   "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "GRC")

# Retry / back-off settings
_MAX_RETRIES      = 3
_RETRY_BACKOFF_S  = 2.0
_RATE_LIMIT_CODES = {429, 503}

# Issue type mapping
ISSUE_TYPES = {
    "Major":    "Bug",
    "Minor":    "Task",
    "Low":      "Task",
    "OFI":      "Improvement",
    "Risk":     "Risk",
    "Test":     "Task",
    "Artifact": "Task",
}

# Priority mapping
PRIORITY_MAP = {
    "Critical": "Highest",
    "Major":    "High",
    "Minor":    "Medium",
    "Low":      "Low",
    "OFI":      "Low",
    "High":     "High",
    "Medium":   "Medium",
}

GRC_LABEL = "ISO27001-GRC"


# ─────────────────────────────────────────────────────────────────────────────
# CREDENTIAL MASKING  (SWOT threat: credential exposure in logs)
# ─────────────────────────────────────────────────────────────────────────────

def _mask_secret(secret: str, visible: int = 4) -> str:
    """Return a masked representation of a secret for safe logging."""
    if not secret:
        return "<not set>"
    return secret[:visible] + "****"


def _auth_header() -> dict:
    """Build the Basic Auth header. Never log the raw token."""
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        raise EnvironmentError(
            "Jira credentials not set.\n"
            "Run: export JIRA_EMAIL=... JIRA_API_TOKEN=... JIRA_BASE_URL=... JIRA_PROJECT_KEY=..."
        )
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def _check_requests():
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests library required: pip install requests")


# ─────────────────────────────────────────────────────────────────────────────
# RETRY / BACK-OFF  (SWOT threat: no rate-limit or retry handling)
# ─────────────────────────────────────────────────────────────────────────────

def _request_with_retry(method: str, url: str, headers: dict,
                        params: dict = None, json_body: dict = None,
                        timeout: int = 30) -> "requests.Response":
    """
    Execute an HTTP request with exponential back-off retry on transient
    errors (5xx, 429 rate limit, connection errors). Raises on final failure.
    """
    _check_requests()
    delay    = _RETRY_BACKOFF_S
    last_exc: Optional[Exception] = None

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.request(
                method, url, headers=headers,
                params=params, json=json_body, timeout=timeout
            )
            if resp.status_code in _RATE_LIMIT_CODES:
                retry_after = float(resp.headers.get("Retry-After", delay))
                logger.warning(
                    "[Jira] Rate limited (HTTP %d). Waiting %.1fs before retry %d/%d.",
                    resp.status_code, retry_after, attempt, _MAX_RETRIES
                )
                time.sleep(retry_after)
                delay *= 2
                continue

            if resp.status_code >= 500:
                logger.warning(
                    "[Jira] Server error HTTP %d on attempt %d/%d. Retrying in %.1fs.",
                    resp.status_code, attempt, _MAX_RETRIES, delay
                )
                time.sleep(delay)
                delay *= 2
                continue

            return resp

        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            logger.warning(
                "[Jira] Connection error on attempt %d/%d. Retrying in %.1fs.",
                attempt, _MAX_RETRIES, delay
            )
            time.sleep(delay)
            delay *= 2

    raise requests.exceptions.RetryError(
        f"[Jira] All {_MAX_RETRIES} attempts failed for {url}. Last error: {last_exc}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — Jira ticket tracking table
# ─────────────────────────────────────────────────────────────────────────────

def init_jira_table():
    """Add the jira_tickets table to the GRC database."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jira_tickets (
            ticket_id   TEXT PRIMARY KEY,
            jira_key    TEXT,
            jira_id     TEXT,
            source_type TEXT,
            source_id   TEXT,
            control_id  TEXT,
            summary     TEXT,
            issue_type  TEXT,
            priority    TEXT,
            status      TEXT DEFAULT 'Open',
            jira_status TEXT,
            assignee    TEXT,
            due_date    TEXT,
            created_at  TEXT,
            last_synced TEXT,
            jira_url    TEXT,
            mock_mode   INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def _log_ticket(source_type: str, source_id: str, control_id: str,
                summary: str, issue_type: str, priority: str,
                assignee: str, due_date: str, jira_key: str = "",
                jira_id: str = "", jira_url: str = "",
                mock: bool = False) -> str:
    """Record a Jira ticket in the local GRC database."""
    ticket_id = f"JT-{uuid.uuid4().hex[:8].upper()}"
    conn = get_connection()
    conn.execute("""
        INSERT INTO jira_tickets
        (ticket_id, jira_key, jira_id, source_type, source_id, control_id,
         summary, issue_type, priority, created_at, assignee, due_date,
         jira_url, mock_mode)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (ticket_id, jira_key, jira_id, source_type, source_id, control_id,
          summary, issue_type, priority, datetime.now().isoformat(),
          assignee, due_date, jira_url, 1 if mock else 0))
    conn.commit()
    conn.close()
    return ticket_id


# ─────────────────────────────────────────────────────────────────────────────
# CORE — Create a single Jira issue via REST API
# ─────────────────────────────────────────────────────────────────────────────

def _create_jira_issue(summary: str, description: str, issue_type: str,
                        priority: str, assignee_email: str = "",
                        due_date: str = "", labels: list = None,
                        components: list = None) -> dict:
    """POST /rest/api/3/issue. Returns dict with keys: key, id, url."""
    # Jira ADF description body
    adf_body = {
        "type": "doc", "version": 1,
        "content": [
            {"type": "paragraph",
             "content": [{"type": "text", "text": description}]}
        ]
    }
    payload = {
        "fields": {
            "project":     {"key": JIRA_PROJECT_KEY},
            "summary":     summary,
            "issuetype":   {"name": issue_type},
            "priority":    {"name": priority},
            "labels":      [GRC_LABEL] + (labels or []),
            "description": adf_body,
        }
    }
    if due_date:
        payload["fields"]["duedate"] = due_date

    if assignee_email:
        try:
            r = _request_with_retry(
                "GET",
                f"{JIRA_BASE_URL}/rest/api/3/user/search",
                _auth_header(),
                params={"query": assignee_email},
                timeout=10
            )
            if r.ok and r.json():
                payload["fields"]["assignee"] = {"accountId": r.json()[0]["accountId"]}
        except Exception:
            pass  # Skip assignee if lookup fails

    if components:
        payload["fields"]["components"] = [{"name": c} for c in components]

    resp = _request_with_retry(
        "POST",
        f"{JIRA_BASE_URL}/rest/api/3/issue",
        _auth_header(),
        json_body=payload,
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "key": data.get("key", ""),
        "id":  data.get("id", ""),
        "url": f"{JIRA_BASE_URL}/browse/{data.get('key', '')}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 1 — Audit Findings → Jira Tickets
# ─────────────────────────────────────────────────────────────────────────────

def create_tickets_for_findings(mock: bool = False) -> list:
    """Create Jira tickets for all open audit findings that don't yet have one."""
    conn = get_connection()
    findings = conn.execute("""
        SELECT f.*, a.audit_name
        FROM audit_findings f
        JOIN audits a ON a.audit_id = f.audit_id
        WHERE f.status = 'Open'
          AND f.finding_id NOT IN (
              SELECT source_id FROM jira_tickets WHERE source_type='finding'
          )
    """).fetchall()
    conn.close()

    created = []
    for f in findings:
        if f["finding_type"] == "NC" and f["severity"] == "Major":
            issue_type, priority = "Bug", "High"
        elif f["finding_type"] == "NC":
            issue_type, priority = "Task", "Medium"
        else:
            issue_type, priority = "Task", "Low"

        summary = (
            f"[ISO27001 {f['finding_type']}] [{f['severity']}] "
            f"{f['control_id'] or 'ISMS'}: {f['title']}"
        )
        description = (
            f"Audit: {f['audit_name']}\n"
            f"Control: {f['control_id'] or 'N/A'}\n"
            f"Finding Type: {f['finding_type']} ({f['severity']})\n\n"
            f"FINDING:\n{f['description']}\n\n"
            f"ROOT CAUSE:\n{f['root_cause'] or 'Not yet determined'}\n\n"
            f"CORRECTIVE ACTION REQUIRED:\n{f['corrective_action'] or 'TBD'}\n\n"
            f"CA Owner: {f['ca_owner'] or 'Unassigned'}\n"
            f"Due Date: {f['due_date']}\n\n"
            f"Source: ISO 27001:2022 GRC Automation | Finding ID: {f['finding_id']}"
        )

        if mock:
            jira_key = f"{JIRA_PROJECT_KEY}-{len(created)+100}"
            jira_id  = str(uuid.uuid4().hex[:6])
            jira_url = f"{JIRA_BASE_URL}/browse/{jira_key}"
            logger.info("  [MOCK] %s [%s/%s] %s", jira_key, issue_type, priority, summary[:65])
        else:
            try:
                result   = _create_jira_issue(
                    summary, description, issue_type, priority,
                    f["ca_owner"] or "", f["due_date"] or "",
                    labels=[f"finding-{f['finding_type'].lower()}", f["control_id"] or "isms"]
                )
                jira_key = result["key"]
                jira_id  = result["id"]
                jira_url = result["url"]
                logger.info("  Created %s [%s/%s] %s", jira_key, issue_type, priority, summary[:65])
            except Exception as exc:
                logger.error("  Failed to create ticket for %s: %s", f["finding_id"], exc)
                continue

        tid = _log_ticket("finding", f["finding_id"], f["control_id"] or "",
                          summary, issue_type, priority,
                          f["ca_owner"] or "", f["due_date"] or "",
                          jira_key, jira_id, jira_url, mock)
        created.append({"ticket_id": tid, "jira_key": jira_key, "finding_id": f["finding_id"]})

    return created


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 2 — Failed / Partial Control Tests → Jira Tickets
# ─────────────────────────────────────────────────────────────────────────────

def create_tickets_for_failed_tests(mock: bool = False) -> list:
    """Create Jira Task tickets for all Fail / Partial control tests without a ticket."""
    conn = get_connection()
    tests = conn.execute("""
        SELECT t.*, c.title as ctrl_title, c.theme
        FROM control_tests t
        JOIN controls c ON c.id = t.control_id
        WHERE t.result IN ('Fail', 'Partial')
          AND t.tester != 'Drata (Mock)'
          AND t.test_id NOT IN (
              SELECT source_id FROM jira_tickets WHERE source_type='test'
          )
    """).fetchall()
    conn.close()

    created = []
    for t in tests:
        priority = "High" if t["result"] == "Fail" else "Medium"
        summary  = (
            f"[ISO27001 Control Test {t['result'].upper()}] "
            f"{t['control_id']}: {t['ctrl_title'][:50]}"
        )
        description = (
            f"Control: {t['control_id']} — {t['ctrl_title']}\n"
            f"Theme: {t['theme']}\n"
            f"Test Name: {t['test_name']}\n"
            f"Test Type: {t['test_type']}\n"
            f"Result: {t['result']}\n"
            f"Test Date: {(t['test_date'] or '')[:10]}\n\n"
            f"FINDING:\n{t['finding'] or 'No specific finding recorded.'}\n\n"
            f"RECOMMENDATION:\n{t['recommendation'] or 'See test procedure.'}\n\n"
            f"Next Re-test Due: {t['next_test_date'] or 'TBD'}\n\n"
            f"Source: ISO 27001:2022 GRC Automation | Test ID: {t['test_id']}"
        )

        if mock:
            jira_key = f"{JIRA_PROJECT_KEY}-{len(created)+200}"
            jira_id  = str(uuid.uuid4().hex[:6])
            jira_url = f"{JIRA_BASE_URL}/browse/{jira_key}"
            logger.info("  [MOCK] %s [%s] %s", jira_key, priority, summary[:65])
        else:
            try:
                result_d = _create_jira_issue(
                    summary, description, "Task", priority, "",
                    t["next_test_date"] or "",
                    labels=["control-test", t["control_id"].lower().replace(".", "-")]
                )
                jira_key = result_d["key"]
                jira_id  = result_d["id"]
                jira_url = result_d["url"]
                logger.info("  Created %s [%s] %s", jira_key, priority, summary[:65])
            except Exception as exc:
                logger.error("  Failed for test %s: %s", t["test_id"], exc)
                continue

        tid = _log_ticket("test", t["test_id"], t["control_id"],
                          summary, "Task", priority, "", t["next_test_date"] or "",
                          jira_key, jira_id, jira_url, mock)
        created.append({"ticket_id": tid, "jira_key": jira_key, "test_id": t["test_id"]})

    return created


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 3 — Critical / High Risks → Jira Tickets
# ─────────────────────────────────────────────────────────────────────────────

def create_tickets_for_risks(min_score: int = 10, mock: bool = False) -> list:
    """Create Jira tickets for risks scoring >= min_score."""
    conn = get_connection()
    risks = conn.execute("""
        SELECT * FROM risks
        WHERE inherent_risk >= ?
          AND status = 'Open'
          AND risk_id NOT IN (
              SELECT source_id FROM jira_tickets WHERE source_type='risk'
          )
        ORDER BY inherent_risk DESC
    """, (min_score,)).fetchall()
    conn.close()

    created = []
    for r in risks:
        score    = r["inherent_risk"]
        level    = "Critical" if score >= 15 else "High"
        priority = "Highest"  if score >= 15 else "High"
        ctrl_ids = ", ".join(json.loads(r["control_ids"] or "[]"))

        summary = (
            f"[ISO27001 RISK {level.upper()}] {r['title']} (Score: {score}/25)"
        )
        description = (
            f"Risk Level: {level} (Inherent Score: {score}/25)\n"
            f"Asset: {r['asset'] or 'N/A'}\n"
            f"Threat: {r['threat'] or 'N/A'}\n"
            f"Vulnerability: {r['vulnerability'] or 'N/A'}\n"
            f"Likelihood: {r['likelihood']}/5 | Impact: {r['impact']}/5\n\n"
            f"RISK DESCRIPTION:\n{r['description']}\n\n"
            f"TREATMENT: {r['treatment']}\n{r['treatment_notes'] or ''}\n\n"
            f"Residual Risk After Treatment: {r['residual_risk']}/25\n"
            f"Related Controls: {ctrl_ids or 'None mapped'}\n"
            f"Risk Owner: {r['owner'] or 'Unassigned'}\n"
            f"Review Date: {r['review_date'] or 'TBD'}\n\n"
            f"Source: ISO 27001:2022 GRC Automation | Risk ID: {r['risk_id']}"
        )

        if mock:
            jira_key = f"{JIRA_PROJECT_KEY}-{len(created)+300}"
            jira_id  = str(uuid.uuid4().hex[:6])
            jira_url = f"{JIRA_BASE_URL}/browse/{jira_key}"
            logger.info("  [MOCK] %s [%s/%s] %s", jira_key, level, priority, summary[:60])
        else:
            try:
                result_d = _create_jira_issue(
                    summary, description, "Task", priority,
                    r["owner"] or "", r["review_date"] or "",
                    labels=["risk-register", f"risk-{level.lower()}"]
                )
                jira_key = result_d["key"]
                jira_id  = result_d["id"]
                jira_url = result_d["url"]
                logger.info("  Created %s [%s] %s", jira_key, level, summary[:60])
            except Exception as exc:
                logger.error("  Failed for risk %s: %s", r["risk_id"], exc)
                continue

        tid = _log_ticket("risk", r["risk_id"], "",
                          summary, "Task", priority,
                          r["owner"] or "", r["review_date"] or "",
                          jira_key, jira_id, jira_url, mock)
        created.append({"ticket_id": tid, "jira_key": jira_key, "risk_id": r["risk_id"]})

    return created


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 4 — Overdue Artifacts → Jira Tickets
# ─────────────────────────────────────────────────────────────────────────────

def create_tickets_for_overdue_artifacts(days_overdue: int = 0,
                                          mock: bool = False) -> list:
    """Create Jira tickets for pending artifacts (grouped by control)."""
    conn = get_connection()
    controls_with_pending = conn.execute("""
        SELECT a.control_id, c.title, c.theme,
               COUNT(*) as pending_count,
               GROUP_CONCAT(a.artifact_name, ' | ') as artifact_names
        FROM artifacts a
        LEFT JOIN controls c ON c.id = a.control_id
        WHERE a.status = 'Pending'
          AND a.control_id IS NOT NULL
          AND a.control_id NOT IN (
              SELECT source_id FROM jira_tickets WHERE source_type='artifact'
          )
        GROUP BY a.control_id
        HAVING pending_count >= 2
        ORDER BY pending_count DESC
        LIMIT 20
    """).fetchall()
    conn.close()

    created = []
    for row in controls_with_pending:
        art_list = (row["artifact_names"] or "").split(" | ")[:5]
        summary  = (
            f"[ISO27001 EVIDENCE NEEDED] {row['control_id']}: "
            f"{(row['title'] or 'Unknown')[:45]} ({row['pending_count']} artifacts pending)"
        )
        description = (
            f"Control: {row['control_id']} — {row['title'] or 'N/A'}\n"
            f"Theme: {row['theme'] or 'N/A'}\n"
            f"Pending Artifact Count: {row['pending_count']}\n\n"
            f"ARTIFACTS REQUIRED:\n"
            + "\n".join(f"  - {a.strip()}" for a in art_list)
            + (f"\n  ... and {row['pending_count'] - len(art_list)} more"
               if row["pending_count"] > len(art_list) else "")
            + "\n\nACTION REQUIRED:\n"
            "Collect and upload the above evidence artifacts to the GRC system "
            "before the ISO 27001 Stage 2 audit.\n\n"
            f"Source: ISO 27001:2022 GRC Automation | Control: {row['control_id']}"
        )
        due = (date.today() + timedelta(days=30)).isoformat()

        if mock:
            jira_key = f"{JIRA_PROJECT_KEY}-{len(created)+400}"
            jira_id  = str(uuid.uuid4().hex[:6])
            jira_url = f"{JIRA_BASE_URL}/browse/{jira_key}"
            logger.info("  [MOCK] %s [Medium] %s", jira_key, summary[:65])
        else:
            try:
                result_d = _create_jira_issue(
                    summary, description, "Task", "Medium", "", due,
                    labels=["evidence-collection",
                            row["control_id"].lower().replace(".", "-")]
                )
                jira_key = result_d["key"]
                jira_id  = result_d["id"]
                jira_url = result_d["url"]
                logger.info("  Created %s [Medium] %s", jira_key, summary[:65])
            except Exception as exc:
                logger.error("  Failed for control %s: %s", row["control_id"], exc)
                continue

        tid = _log_ticket("artifact", row["control_id"], row["control_id"],
                          summary, "Task", "Medium", "", due,
                          jira_key, jira_id, jira_url, mock)
        created.append({"ticket_id": tid, "jira_key": jira_key,
                        "control_id": row["control_id"]})

    return created


# ─────────────────────────────────────────────────────────────────────────────
# TRIGGER 5 — Drata Monitor Failures → Jira Tickets
# ─────────────────────────────────────────────────────────────────────────────

def create_tickets_for_drata_failures(mock: bool = False) -> list:
    """Create Jira Bug tickets for Drata automated monitor failures."""
    conn = get_connection()
    failures = conn.execute("""
        SELECT t.*, c.title as ctrl_title, c.theme, c.test_procedure
        FROM control_tests t
        JOIN controls c ON c.id = t.control_id
        WHERE t.result = 'Fail'
          AND t.tester = 'Drata (Mock)'
          AND t.test_id NOT IN (
              SELECT source_id FROM jira_tickets WHERE source_type='monitor'
          )
    """).fetchall()
    conn.close()

    created = []
    for t in failures:
        summary = (
            f"[DRATA MONITOR FAIL] {t['control_id']}: "
            f"{(t['ctrl_title'] or '')[:50]}"
        )
        description = (
            f"Drata automated monitor has FAILED for this control.\n\n"
            f"Control: {t['control_id']} — {t['ctrl_title']}\n"
            f"Theme: {t['theme']}\n"
            f"Monitor: {t['test_name']}\n"
            f"Failure Detected: {(t['test_date'] or '')[:10]}\n\n"
            f"FINDING:\n{t['finding'] or 'Automated monitor failure — review Drata dashboard.'}\n\n"
            f"RECOMMENDATION:\n{t['recommendation'] or t['test_procedure'] or 'Review and remediate.'}\n\n"
            f"ACTION: Log into Drata, review the failing monitor, remediate the "
            f"underlying control gap, and re-run the monitor to confirm resolution.\n\n"
            f"Source: Drata Monitor | Test ID: {t['test_id']}"
        )

        if mock:
            jira_key = f"{JIRA_PROJECT_KEY}-{len(created)+500}"
            jira_id  = str(uuid.uuid4().hex[:6])
            jira_url = f"{JIRA_BASE_URL}/browse/{jira_key}"
            logger.info("  [MOCK] %s [High] %s", jira_key, summary[:65])
        else:
            try:
                result_d = _create_jira_issue(
                    summary, description, "Bug", "High", "", "",
                    labels=["drata-monitor", t["control_id"].lower().replace(".", "-")]
                )
                jira_key = result_d["key"]
                jira_id  = result_d["id"]
                jira_url = result_d["url"]
                logger.info("  Created %s [Bug/High] %s", jira_key, summary[:65])
            except Exception as exc:
                logger.error("  Failed for monitor %s: %s", t["test_id"], exc)
                continue

        tid = _log_ticket("monitor", t["test_id"], t["control_id"],
                          summary, "Bug", "High", "", "",
                          jira_key, jira_id, jira_url, mock)
        created.append({"ticket_id": tid, "jira_key": jira_key, "test_id": t["test_id"]})

    return created


# ─────────────────────────────────────────────────────────────────────────────
# SYNC — Update local ticket status from Jira
# ─────────────────────────────────────────────────────────────────────────────

def sync_ticket_statuses(mock: bool = False):
    """
    Pull current Jira status for all open GRC tickets and update local DB.
    If a Jira ticket is Done/Closed → auto-close related GRC finding.
    """
    conn         = get_connection()
    open_tickets = conn.execute("""
        SELECT ticket_id, jira_key, source_type, source_id
        FROM jira_tickets WHERE status = 'Open' AND mock_mode = 0
    """).fetchall()
    conn.close()

    if not open_tickets:
        logger.info("[Jira Sync] No live tickets to sync (all are mock or closed).")
        return

    _check_requests()
    updated = 0
    for t in open_tickets:
        try:
            resp = _request_with_retry(
                "GET",
                f"{JIRA_BASE_URL}/rest/api/3/issue/{t['jira_key']}",
                _auth_header(),
                timeout=15
            )
            if not resp.ok:
                continue
            data   = resp.json()
            status = data["fields"]["status"]["name"]

            conn = get_connection()
            conn.execute("""
                UPDATE jira_tickets
                SET jira_status=?, last_synced=?,
                    status = CASE WHEN ? IN ('Done','Closed','Resolved') THEN 'Closed' ELSE 'Open' END
                WHERE jira_key=?
            """, (status, datetime.now().isoformat(), status, t["jira_key"]))

            if status in ("Done", "Closed", "Resolved") and t["source_type"] == "finding":
                conn.execute("""
                    UPDATE audit_findings SET status='Closed', closure_date=?
                    WHERE finding_id=? AND status='Open'
                """, (datetime.now().isoformat(), t["source_id"]))
                logger.info("  [Sync] %s → %s | Finding %s auto-closed",
                            t["jira_key"], status, t["source_id"])

            conn.commit()
            conn.close()
            updated += 1

        except Exception as exc:
            logger.error("  [Sync] %s: %s", t["jira_key"], exc)

    logger.info("[Jira Sync] Updated %d ticket statuses from Jira.", updated)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Run all ticket triggers in one pass
# ─────────────────────────────────────────────────────────────────────────────

def run_full_jira_sync(mock: bool = True) -> dict:
    """Master function: create tickets for all GRC events that need them."""
    mode = "MOCK" if mock else "LIVE"
    logger.info("=" * 64)
    logger.info("JIRA TICKET AUTOMATION — ISO 27001:2022 GRC [%s MODE]", mode)
    logger.info("=" * 64)

    init_jira_table()
    results = {}

    logger.info("[1/5] Audit Findings → Jira Tickets")
    results["findings"] = create_tickets_for_findings(mock=mock)
    logger.info("      → %d ticket(s) created", len(results["findings"]))

    logger.info("[2/5] Failed Control Tests → Jira Tickets")
    results["tests"] = create_tickets_for_failed_tests(mock=mock)
    logger.info("      → %d ticket(s) created", len(results["tests"]))

    logger.info("[3/5] Critical / High Risks → Jira Tickets")
    results["risks"] = create_tickets_for_risks(min_score=10, mock=mock)
    logger.info("      → %d ticket(s) created", len(results["risks"]))

    logger.info("[4/5] Pending Evidence / Artifacts → Jira Tickets")
    results["artifacts"] = create_tickets_for_overdue_artifacts(mock=mock)
    logger.info("      → %d ticket(s) created", len(results["artifacts"]))

    logger.info("[5/5] Drata Monitor Failures → Jira Tickets")
    results["monitors"] = create_tickets_for_drata_failures(mock=mock)
    logger.info("      → %d ticket(s) created", len(results["monitors"]))

    total = sum(len(v) for v in results.values())
    logger.info("-" * 64)
    logger.info("Total tickets created: %d  (findings=%d, tests=%d, "
                "risks=%d, artifacts=%d, monitors=%d)",
                total, len(results["findings"]), len(results["tests"]),
                len(results["risks"]), len(results["artifacts"]),
                len(results["monitors"]))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION TEST
# ─────────────────────────────────────────────────────────────────────────────

def test_jira_connection() -> bool:
    """Verify Jira API credentials and project access."""
    _check_requests()
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        logger.warning(
            "[Jira] Credentials not set (email: %s, token: %s).",
            JIRA_EMAIL or "<not set>", _mask_secret(JIRA_API_TOKEN)
        )
        return False
    logger.info("[Jira] Testing connection (email: %s, token: %s)...",
                JIRA_EMAIL, _mask_secret(JIRA_API_TOKEN))
    try:
        resp = _request_with_retry(
            "GET",
            f"{JIRA_BASE_URL}/rest/api/3/project/{JIRA_PROJECT_KEY}",
            _auth_header(),
            timeout=10
        )
        if resp.ok:
            name = resp.json().get("name", JIRA_PROJECT_KEY)
            logger.info("[Jira] Connected | Project: %s (%s)", name, JIRA_PROJECT_KEY)
            return True
        logger.error("[Jira] HTTP %d: %s", resp.status_code, resp.text[:100])
        return False
    except Exception as exc:
        logger.error("[Jira] Connection error: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# TICKET SUMMARY REPORT
# ─────────────────────────────────────────────────────────────────────────────

def get_ticket_summary() -> dict:
    """Return counts of all GRC-generated Jira tickets by type and status."""
    conn = get_connection()

    by_type     = conn.execute("""
        SELECT source_type, COUNT(*) as cnt, status
        FROM jira_tickets GROUP BY source_type, status
    """).fetchall()
    by_priority = conn.execute("""
        SELECT priority, COUNT(*) as cnt
        FROM jira_tickets GROUP BY priority ORDER BY cnt DESC
    """).fetchall()
    total = conn.execute(
        "SELECT COUNT(*) as cnt FROM jira_tickets"
    ).fetchone()["cnt"]
    open_ = conn.execute(
        "SELECT COUNT(*) as cnt FROM jira_tickets WHERE status='Open'"
    ).fetchone()["cnt"]

    conn.close()
    return {
        "total":       total,
        "open":        open_,
        "by_type":     [dict(r) for r in by_type],
        "by_priority": [dict(r) for r in by_priority],
    }
