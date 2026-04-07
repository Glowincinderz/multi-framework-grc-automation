"""
Drata GRC Platform Integration Module
Syncs ISO 27001 controls, monitors, evidence and test results between
the local GRC database and Drata via its REST API.

API Docs: https://docs.drata.com/api
Authentication: Bearer token (API key from Drata workspace settings)

Remediation changes (SWOT 2026-04-07):
  - Replaced all print() calls with structured logging
  - DRATA_REGION is now env-var configurable (fixes hard-coded EU/US region)
  - Added _request_with_retry() for rate-limit and transient error handling
  - Added _mask_secret() to prevent API key exposure in logs/errors
  - Added _validate_list_response() for API schema validation
"""

import os
import json
import uuid
import time
import logging
import sqlite3
from datetime import datetime
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
# CONFIGURATION  (env-var overridable — fixes hard-coded region weakness)
# ─────────────────────────────────────────────────────────────────────────────

DRATA_REGION   = os.environ.get("DRATA_REGION", "us").lower()   # "us" or "eu"
DRATA_BASE_URL = f"https://public-api.{DRATA_REGION}.drata.com/api"
DRATA_API_KEY  = os.environ.get("DRATA_API_KEY", "")

# Retry / back-off settings
_MAX_RETRIES      = 3
_RETRY_BACKOFF_S  = 2.0   # initial wait; doubled each attempt
_RATE_LIMIT_CODES = {429, 503}


# ─────────────────────────────────────────────────────────────────────────────
# CREDENTIAL MASKING  (SWOT threat: credential exposure in logs)
# ─────────────────────────────────────────────────────────────────────────────

def _mask_secret(secret: str, visible: int = 4) -> str:
    """Return a masked representation of a secret for safe logging."""
    if not secret:
        return "<not set>"
    return secret[:visible] + "****"


# ─────────────────────────────────────────────────────────────────────────────
# RETRY / BACK-OFF  (SWOT threat: no rate-limit or retry handling)
# ─────────────────────────────────────────────────────────────────────────────

def _request_with_retry(method: str, url: str, headers: dict,
                        params: dict = None, json_body: dict = None,
                        timeout: int = 30) -> "requests.Response":
    """
    Execute an HTTP request with exponential back-off retry on transient
    errors (5xx, 429, connection errors).  Raises on final failure.
    """
    _check_requests()
    delay = _RETRY_BACKOFF_S
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
                    "[Drata] Rate limited (HTTP %d). Waiting %.1fs before retry %d/%d.",
                    resp.status_code, retry_after, attempt, _MAX_RETRIES
                )
                time.sleep(retry_after)
                delay *= 2
                continue

            if resp.status_code >= 500:
                logger.warning(
                    "[Drata] Server error HTTP %d on attempt %d/%d. Retrying in %.1fs.",
                    resp.status_code, attempt, _MAX_RETRIES, delay
                )
                time.sleep(delay)
                delay *= 2
                continue

            return resp  # success or a 4xx client error (don't retry)

        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            logger.warning(
                "[Drata] Connection error on attempt %d/%d: %s. Retrying in %.1fs.",
                attempt, _MAX_RETRIES, exc, delay
            )
            time.sleep(delay)
            delay *= 2

    raise requests.exceptions.RetryError(
        f"[Drata] All {_MAX_RETRIES} attempts failed for {url}. "
        f"Last error: {last_exc}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# API SCHEMA VALIDATION  (SWOT threat: third-party API drift)
# ─────────────────────────────────────────────────────────────────────────────

def _validate_list_response(data: dict, endpoint: str) -> list:
    """
    Extract the item list from a Drata paginated response.
    Validates that the response is a dict and raises a descriptive error
    if the shape is unexpected, making API drift immediately detectable.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"[Drata] Unexpected response shape from {endpoint}: "
            f"expected dict, got {type(data).__name__}. "
            "The API contract may have changed — check Drata API changelog."
        )
    # Drata uses 'content' or 'data' as the list key
    for key in ("content", "data", "items", "results"):
        if key in data and isinstance(data[key], list):
            return data[key]
    # Fallback: if it's just a bare list-like response
    logger.warning(
        "[Drata] Could not find standard list key in %s response. "
        "Keys present: %s. API schema may have changed.",
        endpoint, list(data.keys())
    )
    return []


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _headers() -> dict:
    if not DRATA_API_KEY:
        raise EnvironmentError(
            "DRATA_API_KEY environment variable is not set.\n"
            "Set it with: export DRATA_API_KEY=<your_api_key>"
        )
    return {
        "Authorization": f"Bearer {DRATA_API_KEY}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }


def _check_requests():
    if not REQUESTS_AVAILABLE:
        raise ImportError("The 'requests' library is required: pip install requests")


# ─────────────────────────────────────────────────────────────────────────────
# SYNC LOG
# ─────────────────────────────────────────────────────────────────────────────

def _log_sync(sync_type: str, records: int, status: str, summary: str = ""):
    """Record a Drata sync event in the local DB."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO drata_sync_log
            (sync_id, sync_type, synced_at, records_synced, status, response_summary)
        VALUES (?,?,?,?,?,?)
    """, (f"SYNC-{uuid.uuid4().hex[:8].upper()}", sync_type,
          datetime.now().isoformat(), records, status, summary))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# 1. PULL DRATA CONTROLS / REQUIREMENTS
# ─────────────────────────────────────────────────────────────────────────────

def pull_drata_controls(framework: str = "ISO 27001") -> list:
    """
    Pull controls/requirements from Drata for the specified framework.
    Maps them to local control IDs where possible.
    """
    logger.info("[Drata] Pulling controls for framework: %s (region: %s)...",
                framework, DRATA_REGION)
    try:
        resp = _request_with_retry(
            "GET", f"{DRATA_BASE_URL}/controls", _headers(),
            params={"frameworkSlugs": "iso-27001", "limit": 200}
        )
        resp.raise_for_status()
        data     = resp.json()
        controls = _validate_list_response(data, "/controls")

        conn    = get_connection()
        updated = 0
        for dc in controls:
            code         = dc.get("code") or dc.get("requirementCode", "")
            drata_status = dc.get("status", "").lower()

            status_map = {
                "passing":       "Implemented",
                "failing":       "In Progress",
                "in_progress":   "In Progress",
                "not_applicable":"Not Applicable",
                "no_policy":     "Not Implemented",
            }
            local_status = status_map.get(drata_status, "In Progress")

            row = conn.execute("SELECT id FROM controls WHERE id = ?", (code,)).fetchone()
            if row:
                conn.execute("""
                    UPDATE controls SET status=?, last_reviewed=?, notes=? WHERE id=?
                """, (local_status, datetime.now().isoformat(),
                      f"[Drata sync] {dc.get('name','')} | Drata status: {drata_status}",
                      code))
                updated += 1

        conn.commit()
        conn.close()

        _log_sync("controls", len(controls), "Success",
                  f"Pulled {len(controls)} controls, updated {updated} local records")
        logger.info("[Drata] Pulled %d controls, updated %d local records.", len(controls), updated)
        return controls

    except Exception as exc:
        _log_sync("controls", 0, "Error", str(exc))
        logger.error("[Drata] Error pulling controls: %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 2. PULL DRATA MONITORS (automated control tests)
# ─────────────────────────────────────────────────────────────────────────────

def pull_drata_monitors() -> list:
    """
    Pull automated monitor results from Drata.
    Each failing monitor becomes a test record in the local DB.
    """
    logger.info("[Drata] Pulling monitor results...")
    try:
        resp = _request_with_retry(
            "GET", f"{DRATA_BASE_URL}/monitors", _headers(),
            params={"limit": 200}
        )
        resp.raise_for_status()
        data     = resp.json()
        monitors = _validate_list_response(data, "/monitors")

        conn     = get_connection()
        imported = 0
        for m in monitors:
            status       = m.get("status", "").lower()
            result       = ("Pass" if status == "passing"
                            else "Fail" if status == "failing"
                            else "Not Tested")
            control_code = (m.get("controlCode") or "").upper()

            ctrl_row   = conn.execute(
                "SELECT id FROM controls WHERE id=?", (control_code,)
            ).fetchone()
            control_id = ctrl_row["id"] if ctrl_row else None

            if control_id and result in ("Fail", "Pass"):
                test_id  = f"DRATA-{m.get('id', uuid.uuid4().hex[:8])}"
                existing = conn.execute(
                    "SELECT test_id FROM control_tests WHERE test_id=?", (test_id,)
                ).fetchone()
                if not existing:
                    conn.execute("""
                        INSERT INTO control_tests
                            (test_id, control_id, test_name, tester, test_date,
                             test_type, procedure_used, result, finding, recommendation)
                        VALUES (?,?,?,?,?,?,?,?,?,?)
                    """, (test_id, control_id,
                          m.get("name", "Drata Automated Monitor"),
                          "Drata (Automated)",
                          datetime.now().isoformat(),
                          "Operating Effectiveness",
                          m.get("description", "Automated Drata monitor"),
                          result,
                          m.get("failureReason", "")  if result == "Fail" else "",
                          m.get("remediationSteps", "") if result == "Fail" else ""))
                    imported += 1

        conn.commit()
        conn.close()
        _log_sync("monitors", len(monitors), "Success",
                  f"Pulled {len(monitors)} monitors, imported {imported} test results")
        logger.info("[Drata] Pulled %d monitors, imported %d test results.", len(monitors), imported)
        return monitors

    except Exception as exc:
        _log_sync("monitors", 0, "Error", str(exc))
        logger.error("[Drata] Error pulling monitors: %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 3. PULL DRATA EVIDENCE
# ─────────────────────────────────────────────────────────────────────────────

def pull_drata_evidence() -> list:
    """
    Pull uploaded evidence from Drata and register in local artifact store.
    """
    logger.info("[Drata] Pulling evidence items...")
    try:
        resp = _request_with_retry(
            "GET", f"{DRATA_BASE_URL}/evidence", _headers(),
            params={"limit": 200}
        )
        resp.raise_for_status()
        data           = resp.json()
        evidence_items = _validate_list_response(data, "/evidence")

        conn     = get_connection()
        imported = 0
        for ev in evidence_items:
            control_code = (ev.get("controlCode") or "").upper()
            artifact_id  = f"DRATA-EV-{ev.get('id', uuid.uuid4().hex[:8])}"
            existing     = conn.execute(
                "SELECT artifact_id FROM artifacts WHERE artifact_id=?", (artifact_id,)
            ).fetchone()
            if not existing:
                conn.execute("""
                    INSERT INTO artifacts
                        (artifact_id, control_id, artifact_name, artifact_type,
                         description, file_path, collected_by, collected_date, status)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (artifact_id,
                      control_code if control_code else None,
                      ev.get("name", "Drata Evidence"),
                      ev.get("type", "Document"),
                      ev.get("description", "Imported from Drata"),
                      ev.get("url", ""),
                      "Drata (Automated)",
                      ev.get("createdAt", datetime.now().isoformat()),
                      "Collected"))
                imported += 1

        conn.commit()
        conn.close()
        _log_sync("evidence", len(evidence_items), "Success",
                  f"Pulled {len(evidence_items)} items, imported {imported} artifacts")
        logger.info("[Drata] Pulled %d evidence items, imported %d.", len(evidence_items), imported)
        return evidence_items

    except Exception as exc:
        _log_sync("evidence", 0, "Error", str(exc))
        logger.error("[Drata] Error pulling evidence: %s", exc)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 4. PUSH FINDINGS TO DRATA
# ─────────────────────────────────────────────────────────────────────────────

def push_finding_to_drata(finding_id: str) -> bool:
    """Push a local audit finding to Drata as a risk/exception record."""
    conn    = get_connection()
    finding = conn.execute(
        "SELECT * FROM audit_findings WHERE finding_id=?", (finding_id,)
    ).fetchone()
    conn.close()

    if not finding:
        logger.warning("[Drata] Finding %s not found.", finding_id)
        return False

    payload = {
        "name":             finding["title"],
        "description":      finding["description"],
        "severity":         finding["severity"].lower(),
        "status":           "open" if finding["status"] == "Open" else "resolved",
        "controlCode":      finding["control_id"] or "",
        "remediationSteps": finding["corrective_action"] or "",
        "dueDate":          finding["due_date"],
        "source":           "ISO27001-GRC-Automation",
    }

    try:
        resp = _request_with_retry(
            "POST", f"{DRATA_BASE_URL}/risks", _headers(), json_body=payload
        )
        resp.raise_for_status()
        logger.info("[Drata] Finding %s pushed to Drata as risk.", finding_id)
        _log_sync("push_finding", 1, "Success", f"Finding {finding_id} → Drata")
        return True

    except Exception as exc:
        _log_sync("push_finding", 0, "Error", str(exc))
        logger.error("[Drata] Error pushing finding %s: %s", finding_id, exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 5. FULL SYNC
# ─────────────────────────────────────────────────────────────────────────────

def full_drata_sync():
    """Run a complete sync cycle: controls → monitors → evidence."""
    logger.info("=" * 60)
    logger.info("DRATA FULL SYNC — ISO 27001 (region: %s)", DRATA_REGION)
    logger.info("=" * 60)
    pull_drata_controls()
    pull_drata_monitors()
    pull_drata_evidence()
    logger.info("[Drata] Full sync complete.")


# ─────────────────────────────────────────────────────────────────────────────
# 6. CONNECTION TEST
# ─────────────────────────────────────────────────────────────────────────────

def test_drata_connection() -> bool:
    """Verify the Drata API key and connection are working."""
    _check_requests()
    if not DRATA_API_KEY:
        logger.warning("[Drata] DRATA_API_KEY not set (key: %s). Cannot connect.",
                       _mask_secret(DRATA_API_KEY))
        return False
    logger.info("[Drata] Testing connection (region: %s, key: %s)...",
                DRATA_REGION, _mask_secret(DRATA_API_KEY))
    try:
        resp = _request_with_retry(
            "GET", f"{DRATA_BASE_URL}/company", _headers(), timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            name = data.get("name", data.get("companyName", "Unknown"))
            logger.info("[Drata] Connected to workspace: %s", name)
            return True
        logger.error("[Drata] Connection failed: HTTP %d", resp.status_code)
        return False
    except Exception as exc:
        logger.error("[Drata] Connection error: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 7. GET COMPLIANCE SCORE
# ─────────────────────────────────────────────────────────────────────────────

def get_drata_compliance_score() -> Optional[dict]:
    """Fetch overall compliance score from Drata dashboard."""
    _check_requests()
    try:
        resp = _request_with_retry(
            "GET", f"{DRATA_BASE_URL}/compliance/summary", _headers(), timeout=15
        )
        resp.raise_for_status()
        data    = resp.json()
        score   = data.get("overallScore") or data.get("score")
        passing = data.get("passingControls") or data.get("passing")
        failing = data.get("failingControls") or data.get("failing")
        logger.info("[Drata] Compliance Score: %s%% | Passing: %s | Failing: %s",
                    score, passing, failing)
        return {"score": score, "passing": passing, "failing": failing}
    except Exception as exc:
        logger.error("[Drata] Could not fetch compliance score: %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# MOCK / OFFLINE MODE
# ─────────────────────────────────────────────────────────────────────────────

def simulate_drata_sync():
    """
    Simulate a Drata sync with realistic mock data.
    Used for testing / demo without a live API connection.
    """
    import random
    from iso27001_controls import ISO27001_CONTROLS

    logger.info("[Drata MOCK] Running simulated Drata sync...")

    statuses = ["Implemented", "In Progress", "Not Implemented"]
    weights  = [0.55, 0.30, 0.15]

    conn = get_connection()
    for ctrl in ISO27001_CONTROLS:
        status = random.choices(statuses, weights=weights)[0]
        conn.execute("""
            UPDATE controls SET status=?, last_reviewed=?,
            notes='[Drata Mock] Simulated sync result'
            WHERE id=?
        """, (status, datetime.now().isoformat(), ctrl["id"]))

    mock_failures  = random.sample(ISO27001_CONTROLS, k=8)
    test_inserted  = 0
    for ctrl in mock_failures:
        result  = random.choice(["Fail", "Partial"])
        test_id = f"MOCK-{uuid.uuid4().hex[:8].upper()}"
        conn.execute("""
            INSERT OR IGNORE INTO control_tests
            (test_id, control_id, test_name, tester, test_date, test_type,
             procedure_used, result, finding, recommendation)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (test_id, ctrl["id"],
              f"Drata Monitor: {ctrl['title'][:40]}",
              "Drata (Mock)", datetime.now().isoformat(),
              "Operating Effectiveness",
              ctrl["test_procedure"][:200],
              result,
              f"Simulated finding for {ctrl['id']}",
              "Review and remediate control implementation."))
        test_inserted += 1

    conn.commit()
    conn.close()
    _log_sync("mock_sync", len(ISO27001_CONTROLS), "Success (Mock)",
              f"Simulated {len(ISO27001_CONTROLS)} controls, {test_inserted} failures")
    logger.info(
        "[Drata MOCK] Synced %d controls, %d mock failures.",
        len(ISO27001_CONTROLS), test_inserted
    )
