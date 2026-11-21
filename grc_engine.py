"""
GRC Core Engine — ISO 27001:2022
Handles: database setup, risk register, control testing, audit management,
         artifact tracking, management reviews, and database backup.

Remediation changes (SWOT 2026-04-07):
  - Replaced all print() calls with structured logging (logging module)
  - Added backup_database() for point-in-time SQLite backups
  - DB_PATH and BACKUP_DIR are now env-var configurable

Remediation changes (SWOT 2026-04-07 — Prompt 6 gap):
  - backup_database() now prunes old backups, keeping MAX_BACKUP_COUNT most recent

Remediation changes (SWOT 2026-04-07 — Prompt 9):
  - controls table gains a `framework` column (migration-safe ALTER TABLE)
  - load_controls_from_library(framework) routes to the correct control module
  - get_control_summary(framework) filters by framework when supplied
"""

import sqlite3
import json
import os
import shutil
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION (env-var overridable)
# ─────────────────────────────────────────────────────────────────────────────

DB_PATH          = os.environ.get("GRC_DB_PATH",
                                  os.path.join(os.path.dirname(__file__), "grc_database.db"))
BACKUP_DIR       = os.environ.get("GRC_BACKUP_DIR",
                                  os.path.join(os.path.dirname(__file__), "backups"))
MAX_BACKUP_COUNT = int(os.environ.get("GRC_MAX_BACKUPS", "7"))


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Create all GRC tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # Controls register
    c.execute("""
        CREATE TABLE IF NOT EXISTS controls (
            id              TEXT PRIMARY KEY,
            theme           TEXT NOT NULL,
            title           TEXT NOT NULL,
            description     TEXT,
            artifacts_json  TEXT,
            test_procedure  TEXT,
            status          TEXT DEFAULT 'Not Implemented',
            owner           TEXT,
            implementation_date TEXT,
            last_reviewed   TEXT,
            notes           TEXT,
            framework       TEXT DEFAULT 'ISO27001'
        )
    """)
    # Migration: add framework column to existing databases that pre-date Prompt 9
    try:
        c.execute("ALTER TABLE controls ADD COLUMN framework TEXT DEFAULT 'ISO27001'")
        logger.debug("Migrated controls table: added 'framework' column.")
    except Exception:
        pass  # column already exists

    # Risk register
    c.execute("""
        CREATE TABLE IF NOT EXISTS risks (
            risk_id         TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            description     TEXT,
            asset           TEXT,
            threat          TEXT,
            vulnerability   TEXT,
            likelihood      INTEGER,   -- 1-5
            impact          INTEGER,   -- 1-5
            inherent_risk   INTEGER,   -- likelihood * impact
            treatment       TEXT,      -- Accept / Mitigate / Transfer / Avoid
            treatment_notes TEXT,
            residual_risk   INTEGER,
            control_ids     TEXT,      -- JSON list
            owner           TEXT,
            review_date     TEXT,
            status          TEXT DEFAULT 'Open',
            created_at      TEXT
        )
    """)

    # Control tests
    c.execute("""
        CREATE TABLE IF NOT EXISTS control_tests (
            test_id         TEXT PRIMARY KEY,
            control_id      TEXT NOT NULL,
            test_name       TEXT,
            tester          TEXT,
            test_date       TEXT,
            test_type       TEXT,      -- Design / Operating Effectiveness
            procedure_used  TEXT,
            result          TEXT,      -- Pass / Fail / Partial / Not Tested
            finding         TEXT,
            recommendation  TEXT,
            evidence_refs   TEXT,      -- JSON list of artifact IDs
            next_test_date  TEXT,
            FOREIGN KEY (control_id) REFERENCES controls(id)
        )
    """)

    # Audit management
    c.execute("""
        CREATE TABLE IF NOT EXISTS audits (
            audit_id        TEXT PRIMARY KEY,
            audit_type      TEXT,      -- Internal / External / Surveillance / Certification
            audit_name      TEXT,
            auditor         TEXT,
            audit_start     TEXT,
            audit_end       TEXT,
            scope           TEXT,
            status          TEXT DEFAULT 'Planned',   -- Planned / In Progress / Complete
            lead_contact    TEXT,
            report_ref      TEXT,
            notes           TEXT
        )
    """)

    # Audit findings
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_findings (
            finding_id      TEXT PRIMARY KEY,
            audit_id        TEXT NOT NULL,
            control_id      TEXT,
            finding_type    TEXT,   -- NC / OFI / Observation
            severity        TEXT,   -- Major / Minor / Low
            title           TEXT,
            description     TEXT,
            root_cause      TEXT,
            corrective_action TEXT,
            ca_owner        TEXT,
            due_date        TEXT,
            status          TEXT DEFAULT 'Open',
            closure_date    TEXT,
            closure_evidence TEXT,
            FOREIGN KEY (audit_id) REFERENCES audits(audit_id),
            FOREIGN KEY (control_id) REFERENCES controls(id)
        )
    """)

    # Artifact / evidence collection
    c.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id     TEXT PRIMARY KEY,
            control_id      TEXT,
            artifact_name   TEXT NOT NULL,
            artifact_type   TEXT,      -- Policy / Procedure / Log / Report / Screenshot / Certificate
            description     TEXT,
            file_path       TEXT,
            collected_by    TEXT,
            collected_date  TEXT,
            expiry_date     TEXT,
            status          TEXT DEFAULT 'Pending',   -- Pending / Collected / Expired / N/A
            notes           TEXT,
            FOREIGN KEY (control_id) REFERENCES controls(id)
        )
    """)

    # Drata sync log
    c.execute("""
        CREATE TABLE IF NOT EXISTS drata_sync_log (
            sync_id         TEXT PRIMARY KEY,
            sync_type       TEXT,   -- controls / tests / monitors / evidence
            synced_at       TEXT,
            records_synced  INTEGER,
            status          TEXT,
            response_summary TEXT
        )
    """)

    # ISMS management review
    c.execute("""
        CREATE TABLE IF NOT EXISTS management_reviews (
            review_id       TEXT PRIMARY KEY,
            review_date     TEXT,
            chair           TEXT,
            attendees       TEXT,
            inputs          TEXT,
            decisions       TEXT,
            action_items    TEXT,   -- JSON list
            next_review     TEXT,
            notes           TEXT
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialised successfully at: %s", DB_PATH)


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE BACKUP  (SWOT: data loss / single-user bottleneck remediation)
# ─────────────────────────────────────────────────────────────────────────────

def backup_database(backup_dir: str = None) -> str:
    """
    Create a timestamped, consistent backup of the SQLite database using
    SQLite's native online backup API (safe while the DB is in use).

    Returns the path to the backup file.
    Raises FileNotFoundError if the source database does not exist yet.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Source database not found at {DB_PATH}. "
            "Run --init first to create the database."
        )
    target_dir = backup_dir or BACKUP_DIR
    os.makedirs(target_dir, exist_ok=True)

    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S_%f")  # microseconds prevent collision
    backup_path = os.path.join(target_dir, f"grc_database_{timestamp}.db")

    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
        logger.info("Database backed up to: %s", backup_path)
    finally:
        dst.close()
        src.close()

    # Prune old backups — keep only the MAX_BACKUP_COUNT most recent
    _prune_backups(target_dir)

    return backup_path


def _prune_backups(backup_dir: str, keep: int = None) -> int:
    """
    Delete old backup files beyond the retention window.

    Returns the number of files deleted.
    """
    limit  = keep if keep is not None else MAX_BACKUP_COUNT
    files  = get_backup_list(backup_dir)
    to_del = files[limit:]
    for f in to_del:
        try:
            os.remove(f)
            logger.info("Pruned old backup: %s", f)
        except OSError as exc:
            logger.warning("Could not remove backup %s: %s", f, exc)
    if to_del:
        logger.info("Backup retention: kept %d, pruned %d backup(s).", limit, len(to_del))
    return len(to_del)


def get_backup_list(backup_dir: str = None) -> list:
    """Return a list of all available backup files, newest first."""
    target_dir = backup_dir or BACKUP_DIR
    if not os.path.isdir(target_dir):
        return []
    files = [
        os.path.join(target_dir, f)
        for f in sorted(os.listdir(target_dir), reverse=True)
        if f.startswith("grc_database_") and f.endswith(".db")
    ]
    return files


# ─────────────────────────────────────────────────────────────────────────────
# CONTROL REGISTER
# ─────────────────────────────────────────────────────────────────────────────

_FRAMEWORK_MODULES = {
    "ISO27001": ("iso27001_controls", "ISO27001_CONTROLS"),
    "SOC1":     ("soc1_controls",     "SOC1_CONTROLS"),
    "SOC2":     ("soc2_controls",     "SOC2_CONTROLS"),
    "NISTCSF":  ("nist_csf_controls", "NISTCSF_CONTROLS"),
    "PCIDSS":   ("pci_dss_controls",  "PCIDSS_CONTROLS"),
    "ISO42001": ("iso42001_controls", "ISO42001_CONTROLS"),
}

SUPPORTED_FRAMEWORKS = list(_FRAMEWORK_MODULES.keys())


def load_controls_from_library(framework: str = "ISO27001"):
    """
    Seed the controls table from the specified framework's control library.

    Args:
        framework: One of 'ISO27001' (default), 'SOC1', 'SOC2', 'NISTCSF', 'PCIDSS', 'ISO42001'.
    """
    fw = framework.upper()
    if fw not in _FRAMEWORK_MODULES:
        raise ValueError(
            f"Unknown framework '{framework}'. "
            f"Supported: {SUPPORTED_FRAMEWORKS}"
        )
    module_name, attr_name = _FRAMEWORK_MODULES[fw]
    import importlib
    mod      = importlib.import_module(module_name)
    controls = getattr(mod, attr_name)

    conn = get_connection()
    c    = conn.cursor()
    loaded = 0
    for ctrl in controls:
        c.execute("SELECT id FROM controls WHERE id = ? AND framework = ?",
                  (ctrl["id"], fw))
        if not c.fetchone():
            c.execute("""
                INSERT INTO controls
                    (id, theme, title, description, artifacts_json, test_procedure, framework)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ctrl["id"], ctrl["theme"], ctrl["title"],
                ctrl["description"],
                json.dumps(ctrl.get("artifacts", [])),
                ctrl.get("test_procedure", ""),
                fw,
            ))
            loaded += 1
    conn.commit()
    conn.close()
    logger.info("Loaded %d new %s controls into register.", loaded, fw)


def update_control_status(control_id: str, status: str, owner: str = None,
                           implementation_date: str = None, notes: str = None):
    """Update control implementation status."""
    valid_statuses = ["Not Implemented", "In Progress", "Implemented", "Not Applicable"]
    if status not in valid_statuses:
        raise ValueError(f"Status must be one of {valid_statuses}")
    conn = get_connection()
    conn.execute("""
        UPDATE controls SET status=?, owner=?, implementation_date=?, notes=?,
        last_reviewed=? WHERE id=?
    """, (status, owner, implementation_date, notes,
          datetime.now().isoformat(), control_id))
    conn.commit()
    conn.close()
    logger.debug("Control %s updated → %s", control_id, status)


def get_control_summary(framework: str = None) -> dict:
    """Return summary statistics for the control register.

    Args:
        framework: Optional framework filter (e.g. 'ISO27001', 'SOC2').
                   When None, totals across all frameworks.
    """
    conn = get_connection()
    if framework:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM controls "
            "WHERE framework = ? GROUP BY status",
            (framework.upper(),)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM controls GROUP BY status"
        ).fetchall()
    conn.close()
    summary = {row["status"]: row["cnt"] for row in rows}
    total   = sum(summary.values())
    summary["Total"] = total
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# RISK REGISTER
# ─────────────────────────────────────────────────────────────────────────────

def add_risk(title: str, description: str, asset: str, threat: str,
             vulnerability: str, likelihood: int, impact: int,
             treatment: str, treatment_notes: str = "",
             owner: str = "", control_ids: list = None,
             review_date: str = None) -> str:
    """Add a risk to the register."""
    if not 1 <= likelihood <= 5 or not 1 <= impact <= 5:
        raise ValueError("Likelihood and Impact must be 1-5.")
    risk_id = f"RISK-{uuid.uuid4().hex[:8].upper()}"
    inherent_risk = likelihood * impact
    # Residual risk: simplified — treatment reduces by factor
    treatment_factor = {"Accept": 1.0, "Mitigate": 0.5, "Transfer": 0.6, "Avoid": 0.1}
    residual_risk = round(inherent_risk * treatment_factor.get(treatment, 0.8))
    conn = get_connection()
    conn.execute("""
        INSERT INTO risks (risk_id, title, description, asset, threat, vulnerability,
            likelihood, impact, inherent_risk, treatment, treatment_notes,
            residual_risk, control_ids, owner, review_date, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (risk_id, title, description, asset, threat, vulnerability,
          likelihood, impact, inherent_risk, treatment, treatment_notes,
          residual_risk, json.dumps(control_ids or []), owner,
          review_date or (date.today() + timedelta(days=90)).isoformat(),
          datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.info("Added risk %s: '%s' | Inherent=%d | Residual=%d",
                risk_id, title, inherent_risk, residual_risk)
    return risk_id


def get_risk_heatmap_data() -> list:
    """Return all risks with scores for heatmap rendering."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT risk_id, title, likelihood, impact, inherent_risk, "
        "residual_risk, treatment, status FROM risks"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# CONTROL TESTING
# ─────────────────────────────────────────────────────────────────────────────

def record_control_test(control_id: str, test_name: str, tester: str,
                         test_type: str, procedure_used: str,
                         result: str, finding: str = "",
                         recommendation: str = "",
                         evidence_artifact_ids: list = None,
                         next_test_months: int = 12) -> str:
    """Record a control test result."""
    valid_results = ["Pass", "Fail", "Partial", "Not Tested"]
    valid_types   = ["Design", "Operating Effectiveness"]
    if result not in valid_results:
        raise ValueError(f"Result must be one of {valid_results}")
    if test_type not in valid_types:
        raise ValueError(f"test_type must be one of {valid_types}")

    test_id   = f"TEST-{uuid.uuid4().hex[:8].upper()}"
    test_date = datetime.now().isoformat()
    next_date = (date.today() + timedelta(days=30 * next_test_months)).isoformat()

    conn = get_connection()
    conn.execute("""
        INSERT INTO control_tests (test_id, control_id, test_name, tester, test_date,
            test_type, procedure_used, result, finding, recommendation,
            evidence_refs, next_test_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (test_id, control_id, test_name, tester, test_date,
          test_type, procedure_used, result, finding, recommendation,
          json.dumps(evidence_artifact_ids or []), next_date))
    conn.commit()
    conn.close()

    # Auto-update control status based on test result
    status_map = {
        "Pass":       "Implemented",
        "Fail":       "In Progress",
        "Partial":    "In Progress",
        "Not Tested": "Not Implemented",
    }
    update_control_status(control_id, status_map[result])

    logger.info("Test %s → Control %s | %s | Result: %s",
                test_id, control_id, test_type, result)
    return test_id


def get_test_summary() -> dict:
    """Return aggregated test result summary."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT result, COUNT(*) as cnt FROM control_tests GROUP BY result"
    ).fetchall()
    conn.close()
    return {row["result"]: row["cnt"] for row in rows}


def get_overdue_tests() -> list:
    """Return controls whose next_test_date has passed."""
    today = date.today().isoformat()
    conn  = get_connection()
    rows  = conn.execute("""
        SELECT t.test_id, t.control_id, c.title, t.result, t.next_test_date
        FROM control_tests t
        JOIN controls c ON c.id = t.control_id
        WHERE t.next_test_date < ?
        ORDER BY t.next_test_date
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# AUDIT MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def create_audit(audit_type: str, audit_name: str, auditor: str,
                  start_date: str, end_date: str, scope: str,
                  lead_contact: str = "") -> str:
    """Create a new audit record."""
    audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
    conn = get_connection()
    conn.execute("""
        INSERT INTO audits (audit_id, audit_type, audit_name, auditor,
            audit_start, audit_end, scope, lead_contact)
        VALUES (?,?,?,?,?,?,?,?)
    """, (audit_id, audit_type, audit_name, auditor,
          start_date, end_date, scope, lead_contact))
    conn.commit()
    conn.close()
    logger.info("Created audit %s: '%s' (%s)", audit_id, audit_name, audit_type)
    return audit_id


def add_audit_finding(audit_id: str, control_id: str, finding_type: str,
                       severity: str, title: str, description: str,
                       root_cause: str = "", corrective_action: str = "",
                       ca_owner: str = "", due_days: int = 30) -> str:
    """Add a finding to an audit."""
    finding_id = f"FND-{uuid.uuid4().hex[:8].upper()}"
    due_date   = (date.today() + timedelta(days=due_days)).isoformat()
    conn = get_connection()
    conn.execute("""
        INSERT INTO audit_findings (finding_id, audit_id, control_id, finding_type,
            severity, title, description, root_cause, corrective_action,
            ca_owner, due_date)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (finding_id, audit_id, control_id, finding_type, severity, title,
          description, root_cause, corrective_action, ca_owner, due_date))
    conn.commit()
    conn.close()
    logger.info("Finding %s (%s %s) → Audit %s", finding_id, severity, finding_type, audit_id)
    return finding_id


def close_finding(finding_id: str, closure_evidence: str):
    """Mark an audit finding as closed."""
    conn = get_connection()
    conn.execute("""
        UPDATE audit_findings SET status='Closed', closure_date=?, closure_evidence=?
        WHERE finding_id=?
    """, (datetime.now().isoformat(), closure_evidence, finding_id))
    conn.commit()
    conn.close()
    logger.info("Finding %s → Closed", finding_id)


def get_open_findings() -> list:
    """Return all open audit findings."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.*, a.audit_name FROM audit_findings f
        JOIN audits a ON a.audit_id = f.audit_id
        WHERE f.status = 'Open'
        ORDER BY f.severity, f.due_date
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# ARTIFACT / EVIDENCE COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

def register_artifact(control_id: str, artifact_name: str, artifact_type: str,
                       description: str = "", file_path: str = "",
                       collected_by: str = "", expiry_days: int = 365) -> str:
    """Register an evidence artifact for a control."""
    artifact_id    = f"ART-{uuid.uuid4().hex[:8].upper()}"
    collected_date = datetime.now().isoformat()
    expiry_date    = (date.today() + timedelta(days=expiry_days)).isoformat()
    status         = "Collected" if file_path else "Pending"
    conn = get_connection()
    conn.execute("""
        INSERT INTO artifacts (artifact_id, control_id, artifact_name, artifact_type,
            description, file_path, collected_by, collected_date, expiry_date, status)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (artifact_id, control_id, artifact_name, artifact_type,
          description, file_path, collected_by, collected_date, expiry_date, status))
    conn.commit()
    conn.close()
    logger.info("Artifact %s: '%s' for %s → %s", artifact_id, artifact_name, control_id, status)
    return artifact_id


def seed_artifact_checklist(framework: str = "ISO27001"):
    """Pre-populate artifact requirements for every control in the given framework's library."""
    fw = framework.upper()
    if fw not in _FRAMEWORK_MODULES:
        raise ValueError(f"Unknown framework '{framework}'. Supported: {SUPPORTED_FRAMEWORKS}")
    import importlib
    module_name, attr_name = _FRAMEWORK_MODULES[fw]
    controls = getattr(importlib.import_module(module_name), attr_name)
    conn    = get_connection()
    seeded  = 0
    for ctrl in controls:
        for art_name in ctrl["artifacts"]:
            existing = conn.execute(
                "SELECT artifact_id FROM artifacts WHERE control_id=? AND artifact_name=?",
                (ctrl["id"], art_name)
            ).fetchone()
            if not existing:
                artifact_id = f"ART-{uuid.uuid4().hex[:8].upper()}"
                conn.execute("""
                    INSERT INTO artifacts (artifact_id, control_id, artifact_name,
                        artifact_type, status, collected_date)
                    VALUES (?,?,?,'Document','Pending',?)
                """, (artifact_id, ctrl["id"], art_name, datetime.now().isoformat()))
                seeded += 1
    conn.commit()
    conn.close()
    logger.info("Seeded %d %s artifact requirements.", seeded, fw)


def get_artifact_collection_status() -> dict:
    """Return artifact collection progress summary."""
    conn  = get_connection()
    rows  = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM artifacts GROUP BY status"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) as cnt FROM artifacts").fetchone()["cnt"]
    conn.close()
    result    = {row["status"]: row["cnt"] for row in rows}
    result["Total"] = total
    collected = result.get("Collected", 0)
    result["Collection %"] = round((collected / total * 100), 1) if total else 0
    return result


def get_expiring_artifacts(days_ahead: int = 30) -> list:
    """Return artifacts expiring within the given number of days."""
    cutoff = (date.today() + timedelta(days=days_ahead)).isoformat()
    conn   = get_connection()
    rows   = conn.execute("""
        SELECT a.*, c.title as control_title
        FROM artifacts a
        LEFT JOIN controls c ON c.id = a.control_id
        WHERE a.expiry_date <= ? AND a.status = 'Collected'
        ORDER BY a.expiry_date
    """, (cutoff,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT REVIEW
# ─────────────────────────────────────────────────────────────────────────────

def create_management_review(review_date: str, chair: str, attendees: list,
                              decisions: str, action_items: list,
                              next_review_months: int = 6) -> str:
    """Record an ISMS management review."""
    review_id = f"MR-{uuid.uuid4().hex[:8].upper()}"
    # Auto-gather inputs
    ctrl_summary    = get_control_summary()
    test_summary    = get_test_summary()
    open_findings   = len(get_open_findings())
    artifact_status = get_artifact_collection_status()

    inputs = (
        f"Control status: {ctrl_summary} | "
        f"Test results: {test_summary} | "
        f"Open findings: {open_findings} | "
        f"Artifact collection: {artifact_status['Collection %']}%"
    )
    next_review = (date.today() + timedelta(days=30 * next_review_months)).isoformat()

    conn = get_connection()
    conn.execute("""
        INSERT INTO management_reviews (review_id, review_date, chair, attendees,
            inputs, decisions, action_items, next_review)
        VALUES (?,?,?,?,?,?,?,?)
    """, (review_id, review_date, chair, json.dumps(attendees),
          inputs, decisions, json.dumps(action_items), next_review))
    conn.commit()
    conn.close()
    logger.info("Management review %s recorded for %s", review_id, review_date)
    return review_id
