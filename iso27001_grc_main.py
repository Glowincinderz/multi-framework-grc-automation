#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         ISO 27001:2022 GRC AUTOMATION FRAMEWORK                 ║
║   Controls · Testing · Audits · Artifacts · Jira · Drata        ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
    python iso27001_grc_main.py                  # Interactive menu
    python iso27001_grc_main.py --init            # Initialise DB + seed controls
    python iso27001_grc_main.py --demo            # Run full demo workflow
    python iso27001_grc_main.py --report          # Generate Excel report
    python iso27001_grc_main.py --drata-sync      # Sync from Drata (live)
    python iso27001_grc_main.py --drata-mock      # Simulate Drata sync (offline)
    python iso27001_grc_main.py --jira            # Create Jira tickets (live)
    python iso27001_grc_main.py --jira-mock       # Simulate Jira ticket creation
    python iso27001_grc_main.py --status          # Print GRC status summary
    python iso27001_grc_main.py --backup          # Backup the SQLite database
    python iso27001_grc_main.py --alert-test      # Send a test notification to webhooks
    python iso27001_grc_main.py --alert-check     # Run all GRC alert condition checks
    python iso27001_grc_main.py --init --framework SOC1      # Initialise with SOC 1 control objectives
    python iso27001_grc_main.py --init --framework SOC2      # Initialise with SOC 2 controls
    python iso27001_grc_main.py --status --framework NISTCSF # Status summary for NIST CSF

Prerequisites:
    pip install -r requirements.txt
    cp .env.example .env  # then fill in your real API keys

    # Or set env vars directly:
    export DRATA_API_KEY=<your_api_key>
    export DRATA_REGION=us                        # or "eu"
    export JIRA_BASE_URL=https://yourco.atlassian.net
    export JIRA_EMAIL=you@company.com
    export JIRA_API_TOKEN=<your_jira_token>
    export JIRA_PROJECT_KEY=GRC

Remediation changes (SWOT 2026-04-07):
  - Replaced all print() calls with structured logging
  - Logging is configured once here (level / file from env vars)
  - Added --backup CLI flag for on-demand DB backups
  - Fixed OUTPUT_DIR: report now saves to the same directory as this script
  - Added python-dotenv support to load .env automatically

Remediation changes (SWOT 2026-04-07 — Prompt 8):
  - Added --alert-test flag: sends a test notification to all configured webhooks
  - Added --alert-check flag: runs GRC alert condition checks and fires notifications

Remediation changes (SWOT 2026-04-07 — Prompt 9):
  - Added --framework flag: selects control library (ISO27001 / SOC2 / NISTCSF / PCIDSS)
  - --init respects --framework to seed the correct control set
  - --status respects --framework to filter the status summary
"""

import argparse
import logging
import logging.handlers
import os
import sys
from datetime import date, datetime

# ── Load .env if present (python-dotenv) ──────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"),
                override=False)
except ImportError:
    pass  # python-dotenv not installed; env vars must be set externally

# ── Logging setup ─────────────────────────────────────────────────────────────
# Configure before importing local modules so their loggers inherit this config.

def _configure_logging():
    """
    Set up root logger from environment variables:
      GRC_LOG_LEVEL : DEBUG | INFO | WARNING | ERROR | CRITICAL  (default: INFO)
      GRC_LOG_FILE  : path to log file (optional; stdout used if not set)
    """
    level_name = os.environ.get("GRC_LOG_LEVEL", "INFO").upper()
    level      = getattr(logging, level_name, logging.INFO)

    handlers: list[logging.Handler] = []

    # Console handler — always present
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    handlers.append(console)

    # Optional rotating file handler
    log_file = os.environ.get("GRC_LOG_FILE", "")
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)


_configure_logging()
logger = logging.getLogger(__name__)

# ── Local modules ─────────────────────────────────────────────────────────────
from alerting import send_test_alert, run_alert_checks
from grc_engine import (
    init_database, load_controls_from_library, seed_artifact_checklist,
    update_control_status, get_control_summary, add_risk, get_risk_heatmap_data,
    record_control_test, get_test_summary, get_overdue_tests,
    create_audit, add_audit_finding, close_finding, get_open_findings,
    register_artifact, get_artifact_collection_status, get_expiring_artifacts,
    create_management_review, backup_database
)
from drata_integration import (
    test_drata_connection, full_drata_sync, simulate_drata_sync,
    get_drata_compliance_score
)
from jira_integration import (
    init_jira_table, run_full_jira_sync, test_jira_connection,
    sync_ticket_statuses, get_ticket_summary
)
from grc_report_generator import generate_report

# ── Output path ───────────────────────────────────────────────────────────────
# Reports are saved in the same directory as this script.
OUTPUT_DIR  = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(
    OUTPUT_DIR,
    f"ISO27001_GRC_Report_{date.today().strftime('%Y%m%d')}.xlsx"
)


# ─────────────────────────────────────────────────────────────────────────────
# INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(framework: str = "ISO27001"):
    """Initialise database and seed controls for the requested framework."""
    fw = framework.upper()
    logger.info("=" * 64)
    logger.info("GRC INITIALISATION — Framework: %s", fw)
    logger.info("=" * 64)
    init_database()
    load_controls_from_library(fw)
    seed_artifact_checklist(fw)
    logger.info(
        "GRC system initialised. %s controls and their artifact requirements "
        "are now loaded in the local database.", fw
    )


# ─────────────────────────────────────────────────────────────────────────────
# ALERTING
# ─────────────────────────────────────────────────────────────────────────────

def cmd_alert_test():
    """Send a test notification to all configured webhooks."""
    logger.info("=" * 64)
    logger.info("GRC ALERT — TEST NOTIFICATION")
    logger.info("=" * 64)
    results = send_test_alert()
    configured = [ch for ch, ok in results.items() if ok is not None]
    sent       = [ch for ch, ok in results.items() if ok is True]
    if not configured:
        print("\n  ℹ  No webhooks configured. "
              "Set SLACK_WEBHOOK_URL or TEAMS_WEBHOOK_URL to enable alerts.")
    else:
        for ch, ok in results.items():
            status = "✅ sent" if ok else ("❌ failed" if ok is False else "—  not configured")
            print(f"  {ch.capitalize():<10} {status}")
        if sent:
            print(f"\n  ✅ Test alert sent to: {', '.join(sent)}")


def cmd_alert_check():
    """Run GRC alert condition checks and fire notifications for any breaches."""
    logger.info("=" * 64)
    logger.info("GRC ALERT — CONDITION CHECKS")
    logger.info("=" * 64)
    summary = run_alert_checks()
    fired   = summary.get("checks_fired", [])
    if not fired:
        print("\n  ✅ All alert checks passed — no conditions breached.")
    else:
        print(f"\n  ⚠  {len(fired)} alert condition(s) fired: {', '.join(fired)}")


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE BACKUP
# ─────────────────────────────────────────────────────────────────────────────

def cmd_backup():
    """Create a timestamped backup of the GRC database."""
    logger.info("=" * 64)
    logger.info("GRC DATABASE BACKUP")
    logger.info("=" * 64)
    try:
        path = backup_database()
        logger.info("Backup complete → %s", path)
        print(f"\n  ✅  Database backed up to: {path}")
    except FileNotFoundError as exc:
        logger.error("Backup failed: %s", exc)
        print(f"\n  ✗  Backup failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# STATUS SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def cmd_status(framework: str = "ISO27001"):
    """Print a concise GRC status summary to the terminal."""
    fw = framework.upper()
    print("\n" + "=" * 64)
    print(f"  GRC STATUS SUMMARY — {fw}")
    print(f"  As of {date.today().strftime('%d %b %Y')}")
    print("=" * 64)

    ctrl  = get_control_summary(fw)
    total = ctrl.get("Total", 0)
    impl  = ctrl.get("Implemented", 0)
    pct   = round(impl / total * 100, 1) if total else 0

    print(f"\n▸ CONTROL REGISTER ({total} total)")
    print(f"  {'Implemented':<22} {impl:>5}  ({pct}%)")
    print(f"  {'In Progress':<22} {ctrl.get('In Progress', 0):>5}")
    print(f"  {'Not Implemented':<22} {ctrl.get('Not Implemented', 0):>5}")
    print(f"  {'Not Applicable':<22} {ctrl.get('Not Applicable', 0):>5}")

    tests       = get_test_summary()
    total_tests = sum(tests.values())
    print(f"\n▸ CONTROL TESTING ({total_tests} tests recorded)")
    for result, cnt in tests.items():
        print(f"  {result:<22} {cnt:>5}")

    findings = get_open_findings()
    major    = sum(1 for f in findings if f["severity"] == "Major")
    print(f"\n▸ AUDIT FINDINGS")
    print(f"  {'Open Findings':<22} {len(findings):>5}")
    print(f"  {'Major Non-Conformities':<22} {major:>5}")

    arts = get_artifact_collection_status()
    print(f"\n▸ ARTIFACT COLLECTION")
    print(f"  {'Total Required':<22} {arts.get('Total', 0):>5}")
    print(f"  {'Collected':<22} {arts.get('Collected', 0):>5}")
    print(f"  {'Pending':<22} {arts.get('Pending', 0):>5}")
    print(f"  {'Collection %':<22} {arts.get('Collection %', 0):>4}%")

    overdue = get_overdue_tests()
    if overdue:
        print(f"\n⚠  OVERDUE TESTS: {len(overdue)} control(s) need re-testing")
        for o in overdue[:5]:
            print(f"   • {o['control_id']}: {o['title'][:45]} (due {o['next_test_date'][:10]})")
        if len(overdue) > 5:
            print(f"   ... and {len(overdue) - 5} more")

    expiring = get_expiring_artifacts(days_ahead=30)
    if expiring:
        print(f"\n⚠  EXPIRING ARTIFACTS: {len(expiring)} expiring within 30 days")
        for e in expiring[:3]:
            print(f"   • {e['artifact_name'][:45]} (expires {e['expiry_date']})")

    print("\n" + "-" * 64)


# ─────────────────────────────────────────────────────────────────────────────
# DEMO WORKFLOW
# ─────────────────────────────────────────────────────────────────────────────

def cmd_demo():
    """Run a complete end-to-end demo of the GRC automation."""
    logger.info("=" * 64)
    logger.info("ISO 27001:2022 GRC — FULL DEMO WORKFLOW")
    logger.info("=" * 64)

    logger.info("[Step 1/9] Initialising database...")
    cmd_init()

    logger.info("[Step 2/9] Simulating Drata sync...")
    simulate_drata_sync()

    logger.info("[Step 3/9] Populating risk register...")
    _demo_risks()

    logger.info("[Step 4/9] Recording control tests...")
    _demo_control_tests()

    logger.info("[Step 5/9] Creating audit and findings...")
    _demo_audits()

    logger.info("[Step 6/9] Registering evidence artifacts...")
    _demo_artifacts()

    logger.info("[Step 7/9] Creating management review...")
    create_management_review(
        review_date=date.today().isoformat(),
        chair="CISO",
        attendees=["CISO", "DPO", "Head of IT", "Risk Manager", "Internal Auditor"],
        decisions=(
            "1. Accelerate remediation of 5 critical Drata monitor failures. "
            "2. Prioritise A.8.8 vulnerability management patching SLA. "
            "3. Extend DLP to cloud storage by Q3. "
            "4. Schedule Stage 1 certification audit for Q4."
        ),
        action_items=[
            {"action": "Remediate critical Drata monitor failures",      "owner": "Head of IT",   "due": "2026-05-01"},
            {"action": "Implement DLP on cloud storage",                 "owner": "Security Team","due": "2026-07-30"},
            {"action": "Book Stage 1 certification audit",               "owner": "CISO",         "due": "2026-05-15"},
            {"action": "Complete security awareness training rollout",   "owner": "HR",           "due": "2026-04-30"},
        ],
        next_review_months=6
    )

    logger.info("[Step 8/9] Creating Jira tickets (mock mode)...")
    init_jira_table()
    run_full_jira_sync(mock=True)

    logger.info("[Step 9/9] Generating Excel GRC report...")
    generate_report(REPORT_PATH)

    logger.info("=" * 64)
    logger.info("DEMO COMPLETE — Report: %s", REPORT_PATH)
    logger.info("=" * 64)
    cmd_status()


def _demo_risks():
    risks = [
        ("Ransomware Attack", "Ransomware encrypts critical business systems",
         "All IT systems", "Malicious actors", "Unpatched systems / no EDR",
         4, 5, "Mitigate", "Deploy EDR, patch management, offline backups", "IT Security",
         ["A.8.7", "A.8.8", "A.8.13"]),
        ("Insider Data Theft", "Privileged user exfiltrates confidential data",
         "HR & Finance systems", "Malicious insider", "Excessive access rights / no DLP",
         3, 5, "Mitigate", "Implement DLP, PAM, user behaviour analytics", "CISO",
         ["A.5.3", "A.8.2", "A.8.12"]),
        ("Phishing / Business Email Compromise", "CEO fraud / credential phishing",
         "Email platform", "External threat actor", "Lack of MFA / email filtering",
         4, 4, "Mitigate", "Enforce MFA, deploy email security gateway", "IT Security",
         ["A.8.5", "A.6.3"]),
        ("Cloud Misconfiguration", "Public S3 bucket exposes sensitive data",
         "AWS / Cloud storage", "Human error", "No IaC policy gates / CSPM",
         3, 4, "Mitigate", "Deploy CSPM tool, enforce IaC security scanning", "Cloud Team",
         ["A.5.23", "A.8.9"]),
        ("Third-party Breach", "Key supplier suffers breach affecting shared data",
         "Supplier systems", "External threat actor", "Inadequate supplier vetting",
         3, 4, "Transfer", "Require SOC 2 / ISO 27001 certs, cyber insurance", "Procurement",
         ["A.5.19", "A.5.20", "A.5.22"]),
        ("Physical Intrusion", "Unauthorised person gains access to server room",
         "Data centre", "Opportunistic intruder", "Tailgating / visitor management gaps",
         2, 5, "Mitigate", "Enforce anti-tailgating, mantrap, CCTV monitoring", "Facilities",
         ["A.7.1", "A.7.2", "A.7.4"]),
        ("Regulatory Non-Compliance (GDPR)", "Personal data processed without lawful basis",
         "Customer data", "Process failure", "Unclear ROPA / DPIA process",
         2, 4, "Mitigate", "Complete ROPA, conduct DPIAs, appoint DPO", "DPO",
         ["A.5.34", "A.5.31"]),
        ("DDoS Attack on Production", "Volumetric DDoS causes service outage",
         "Public-facing applications", "Hacktivist / competitor", "No DDoS mitigation service",
         3, 3, "Transfer", "Engage DDoS protection provider, update cyber insurance", "IT Ops",
         ["A.8.14", "A.5.29"]),
    ]
    for r in risks:
        add_risk(
            title=r[0], description=r[1], asset=r[2], threat=r[3],
            vulnerability=r[4], likelihood=r[5], impact=r[6],
            treatment=r[7], treatment_notes=r[8], owner=r[9], control_ids=r[10]
        )


def _demo_control_tests():
    tests = [
        ("A.5.1",  "IS Policy Annual Review Check",              "Internal Auditor",      "Design",                 "Pass",    "", ""),
        ("A.5.17", "MFA Enforcement Verification",               "Security Analyst",      "Operating Effectiveness","Pass",    "", ""),
        ("A.6.3",  "Security Awareness Training Completion Check","HR / Security",         "Operating Effectiveness","Partial",
         "Training completion rate is 72% — below 90% target.",
         "Mandate completion for all staff; escalate non-completions to managers."),
        ("A.8.5",  "Secure Authentication Review",               "Security Analyst",      "Operating Effectiveness","Pass",    "", ""),
        ("A.8.7",  "Malware Protection Coverage Scan",           "Security Analyst",      "Operating Effectiveness","Pass",    "", ""),
        ("A.8.8",  "Vulnerability Patching SLA Review",          "Vulnerability Manager", "Operating Effectiveness","Fail",
         "3 critical CVEs open for >30 days, exceeding 14-day SLA.",
         "Implement automated patching for OS and middleware. Review exception process."),
        ("A.8.12", "DLP Policy Coverage Check",                  "Security Analyst",      "Design",                 "Partial",
         "DLP not deployed on cloud storage endpoints.",
         "Extend DLP solution to cover SharePoint Online and OneDrive."),
        ("A.8.13", "Backup and Restoration Test",                "IT Operations",         "Operating Effectiveness","Pass",    "", ""),
        ("A.8.15", "SIEM Log Coverage Audit",                    "SOC Lead",              "Operating Effectiveness","Pass",    "", ""),
        ("A.5.19", "Supplier Security Assessment Review",        "Procurement / Security","Operating Effectiveness","Fail",
         "2 critical suppliers have not completed annual security assessments.",
         "Issue formal requests to suppliers; set 30-day deadline or trigger exit clause."),
        ("A.7.2",  "Physical Access Control Audit",              "Facilities / Security", "Operating Effectiveness","Pass",    "", ""),
        ("A.5.24", "Incident Response Plan Tabletop Exercise",   "CISO",                  "Operating Effectiveness","Pass",    "", ""),
        ("A.5.35", "Independent IS Review Verification",         "External Auditor",      "Design",                 "Pass",    "", ""),
        ("A.8.25", "Secure SDLC Gate Verification",              "Dev Security Lead",     "Operating Effectiveness","Partial",
         "SAST is integrated but DAST is not run in CI/CD pipeline.",
         "Integrate OWASP ZAP or equivalent DAST into CI/CD; block high-severity findings."),
    ]
    for ctrl_id, name, tester, t_type, result, finding, rec in tests:
        record_control_test(
            control_id=ctrl_id, test_name=name, tester=tester,
            test_type=t_type, procedure_used=f"ISO 27001 control test procedure for {ctrl_id}",
            result=result, finding=finding, recommendation=rec
        )


def _demo_audits():
    aud1 = create_audit(
        audit_type="Internal",
        audit_name="Q1 2026 Internal ISMS Audit",
        auditor="Internal Audit Team",
        start_date="2026-03-10",
        end_date="2026-03-21",
        scope="All ISO 27001:2022 Annex A controls — full ISMS scope",
        lead_contact="CISO"
    )
    add_audit_finding(aud1, "A.8.8", "NC", "Major",
        "Critical CVEs Unpatched Beyond SLA",
        "3 critical CVEs exceed the 14-day patching SLA with no documented exception.",
        "Insufficient automated patching; manual process delays.",
        "Deploy automated patch management; review and close critical CVEs within 14 days.",
        "Head of IT", 30)
    add_audit_finding(aud1, "A.6.3", "NC", "Minor",
        "Security Awareness Training Below Target",
        "Annual security awareness training completion at 72%, below 90% KPI.",
        "No automated reminder escalation for non-completers.",
        "Configure LMS auto-reminders and management escalation at 80% deadline.",
        "HR Manager", 45)
    add_audit_finding(aud1, "A.5.19", "NC", "Minor",
        "2 Critical Suppliers Without Current Security Assessment",
        "Annual supplier security assessments overdue for 2 Tier-1 suppliers.",
        "No automated due-date tracking in procurement system.",
        "Add supplier assessment due-dates to GRC tracker with automated reminders.",
        "Procurement Manager", 30)
    add_audit_finding(aud1, "A.8.25", "OFI", "Low",
        "DAST Not Integrated in CI/CD",
        "Dynamic application security testing not automated in deployment pipeline.",
        "DAST tool procurement delayed.",
        "Evaluate and procure DAST tool; integrate in CI/CD by Q3.",
        "Dev Security Lead", 90)

    create_audit("Certification", "ISO 27001:2022 Stage 1 — Documentation Review",
                 "BSI / Certification Body", "2026-10-06", "2026-10-07",
                 "ISMS documentation, scope statement, risk assessment, SoA review", "CISO")
    create_audit("Certification", "ISO 27001:2022 Stage 2 — On-site Certification Audit",
                 "BSI / Certification Body", "2026-11-10", "2026-11-14",
                 "Full ISMS implementation — all controls, processes and evidence review", "CISO")


def _demo_artifacts():
    artifacts = [
        ("A.5.1",  "Information Security Policy v2.1",        "Policy",      "APPROVED POLICY DOCUMENT",                                       "/docs/IS_Policy_v2.1.pdf"),
        ("A.5.1",  "Board Approval Minutes — IS Policy",      "Document",    "Board sign-off on IS policy",                                    "/docs/Board_Minutes_IS_Policy.pdf"),
        ("A.5.9",  "Asset Register — Q1 2026",                "Spreadsheet", "Full asset inventory with owners and classification",            "/docs/Asset_Register_Q1.xlsx"),
        ("A.5.17", "MFA Enforcement Screenshot — Azure AD",   "Screenshot",  "Azure AD MFA policy enforced for all users",                     "/evidence/mfa_enforcement_azure.png"),
        ("A.6.3",  "Security Awareness Training Report",      "Report",      "LMS completion report — 72% completion rate",                    "/evidence/awareness_training_report.pdf"),
        ("A.8.7",  "EDR Deployment Report — CrowdStrike",    "Report",      "100% endpoint coverage confirmed",                               "/evidence/edr_coverage_report.pdf"),
        ("A.8.8",  "Vulnerability Scan Report — Tenable",    "Report",      "Monthly Nessus scan results",                                    "/evidence/vuln_scan_march2026.pdf"),
        ("A.8.13", "Backup Restoration Test Report",          "Report",      "Quarterly backup restore test — PASS",                          "/evidence/backup_test_q1.pdf"),
        ("A.8.15", "SIEM Configuration Screenshot",          "Screenshot",  "Splunk SIEM log source coverage",                               "/evidence/siem_config.png"),
        ("A.7.2",  "Access Control Log — Server Room",        "Log",         "Badge access log — last 90 days",                               "/evidence/badge_log_q1.csv"),
        ("A.5.24", "Incident Response Plan v3.0",             "Policy",      "Current IRP including playbooks",                               "/docs/IRP_v3.pdf"),
        ("A.5.19", "Supplier Security Assessment — Vendor A", "Report",      "Annual security questionnaire — PASS",                          "/evidence/supplier_A_assessment.pdf"),
    ]
    for ctrl_id, name, art_type, desc, path in artifacts:
        register_artifact(
            control_id=ctrl_id, artifact_name=name,
            artifact_type=art_type, description=desc,
            file_path=path, collected_by="GRC Team", expiry_days=365
        )


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE MENU
# ─────────────────────────────────────────────────────────────────────────────

def interactive_menu():
    menu = """
╔══════════════════════════════════════════════════════════════╗
║     ISO 27001:2022 GRC AUTOMATION — MAIN MENU               ║
╠══════════════════════════════════════════════════════════════╣
║  1.  Initialise / Reset GRC database                        ║
║  2.  Print GRC status summary                               ║
║  3.  Run full demo workflow                                 ║
║  4.  Generate Excel report                                  ║
║  5.  Drata: Test connection                                 ║
║  6.  Drata: Full live sync (requires API key)               ║
║  7.  Drata: Simulate sync (offline/demo)                    ║
║  8.  Drata: Get compliance score                            ║
║  9.  Add a risk manually                                    ║
║  10. Record a control test                                  ║
║  11. Jira: Test connection                                  ║
║  12. Jira: Create tickets — LIVE (requires API key)         ║
║  13. Jira: Create tickets — MOCK (simulate)                 ║
║  14. Jira: Sync ticket statuses from Jira                   ║
║  15. Jira: Show ticket summary                              ║
║  16. Backup database                                        ║
║  0.  Exit                                                   ║
╚══════════════════════════════════════════════════════════════╝
"""
    while True:
        print(menu)
        choice = input("  Enter choice: ").strip()

        if   choice == "1":  cmd_init()
        elif choice == "2":  cmd_status()
        elif choice == "3":  cmd_demo()
        elif choice == "4":
            path = input(f"  Output path [{REPORT_PATH}]: ").strip() or REPORT_PATH
            generate_report(path)
            logger.info("Report saved to: %s", path)
            print(f"\n  ✅ Report saved to: {path}")
        elif choice == "5":  test_drata_connection()
        elif choice == "6":  full_drata_sync()
        elif choice == "7":  simulate_drata_sync()
        elif choice == "8":  get_drata_compliance_score()
        elif choice == "9":  _interactive_add_risk()
        elif choice == "10": _interactive_add_test()
        elif choice == "11": test_jira_connection()
        elif choice == "12":
            init_jira_table()
            run_full_jira_sync(mock=False)
        elif choice == "13":
            init_jira_table()
            run_full_jira_sync(mock=True)
        elif choice == "14": sync_ticket_statuses()
        elif choice == "15": _print_jira_summary()
        elif choice == "16": cmd_backup()
        elif choice == "0":
            logger.info("GRC session ended.")
            print("  Goodbye.")
            break
        else:
            print("  Invalid choice. Try again.")


def _print_jira_summary():
    try:
        summary = get_ticket_summary()
        print(f"\n  ── JIRA TICKET SUMMARY ──")
        print(f"  Total Tickets : {summary['total']}")
        print(f"  Open          : {summary['open']}")
        print(f"  Closed        : {summary['total'] - summary['open']}")
        print(f"\n  By Type:")
        for t in summary["by_type"]:
            print(f"    {t['source_type']:<12} {t['status']:<8} {t['cnt']}")
        print(f"\n  By Priority:")
        for p in summary["by_priority"]:
            print(f"    {p['priority']:<12} {p['cnt']}")
    except Exception as exc:
        logger.warning("[Jira] No ticket data yet: %s", exc)
        print(f"  [Jira] No ticket data yet: {exc}")


def _interactive_add_risk():
    print("\n  — ADD RISK —")
    title    = input("  Title: ").strip()
    desc     = input("  Description: ").strip()
    asset    = input("  Asset: ").strip()
    threat   = input("  Threat: ").strip()
    vuln     = input("  Vulnerability: ").strip()
    likeli   = int(input("  Likelihood (1-5): ").strip())
    impact   = int(input("  Impact (1-5): ").strip())
    treatment = input("  Treatment (Accept/Mitigate/Transfer/Avoid): ").strip()
    notes    = input("  Treatment notes: ").strip()
    owner    = input("  Owner: ").strip()
    ctrl_ids = input("  Related control IDs (comma-separated, e.g. A.8.8,A.5.19): ").strip()
    ctrl_list = [c.strip() for c in ctrl_ids.split(",") if c.strip()]
    risk_id = add_risk(title, desc, asset, threat, vuln, likeli, impact,
                       treatment, notes, owner, ctrl_list)
    print(f"\n  ✅ Risk {risk_id} added.")


def _interactive_add_test():
    print("\n  — RECORD CONTROL TEST —")
    ctrl_id = input("  Control ID (e.g. A.8.8): ").strip()
    name    = input("  Test name: ").strip()
    tester  = input("  Tester name: ").strip()
    t_type  = input("  Type (Design / Operating Effectiveness): ").strip()
    proc    = input("  Procedure used: ").strip()
    result  = input("  Result (Pass / Fail / Partial / Not Tested): ").strip()
    finding = input("  Finding (leave blank if Pass): ").strip()
    rec     = input("  Recommendation: ").strip()
    test_id = record_control_test(ctrl_id, name, tester, t_type, proc,
                                   result, finding, rec)
    print(f"\n  ✅ Test {test_id} recorded.")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ISO 27001:2022 GRC Automation Framework"
    )
    parser.add_argument("--init",         action="store_true", help="Initialise DB + seed controls")
    parser.add_argument("--demo",         action="store_true", help="Run full demo workflow")
    parser.add_argument("--report",       action="store_true", help="Generate Excel GRC report")
    parser.add_argument("--status",       action="store_true", help="Print GRC status summary")
    parser.add_argument("--drata-sync",   action="store_true", help="Full live Drata sync")
    parser.add_argument("--drata-mock",   action="store_true", help="Simulate Drata sync (offline)")
    parser.add_argument("--jira",         action="store_true", help="Create Jira tickets (live)")
    parser.add_argument("--jira-mock",    action="store_true", help="Simulate Jira ticket creation")
    parser.add_argument("--backup",       action="store_true", help="Backup the GRC database")
    parser.add_argument("--alert-test",   action="store_true", help="Send a test webhook notification")
    parser.add_argument("--alert-check",  action="store_true", help="Run GRC alert condition checks")
    parser.add_argument("--framework",    type=str, default="ISO27001",
                        metavar="FRAMEWORK",
                        help="Control framework: ISO27001 (default), SOC1, SOC2, NISTCSF, PCIDSS, ISO42001")
    parser.add_argument("--out",          type=str,            help="Report output path")

    args = parser.parse_args()
    fw   = args.framework.upper()

    if   args.init:         cmd_init(fw)
    elif args.demo:         cmd_demo()
    elif args.report:
        path = args.out or REPORT_PATH
        generate_report(path)
        print(f"\n  ✅ Report saved to: {path}")
    elif args.status:       cmd_status(fw)
    elif args.drata_sync:   full_drata_sync()
    elif args.drata_mock:   simulate_drata_sync()
    elif args.jira:
        init_jira_table()
        run_full_jira_sync(mock=False)
    elif args.jira_mock:
        init_jira_table()
        run_full_jira_sync(mock=True)
    elif args.backup:       cmd_backup()
    elif args.alert_test:   cmd_alert_test()
    elif args.alert_check:  cmd_alert_check()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
