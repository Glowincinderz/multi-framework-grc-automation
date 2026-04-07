# GRC Automation Framework

[![CI](https://github.com/your-org/grc-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/grc-automation/actions/workflows/ci.yml)

A Python-based, end-to-end **Governance, Risk & Compliance (GRC) automation platform** that walks an organisation through every phase of a compliance programme — from initialising a control register and running risk assessments, through control testing and audit management, to evidence collection, Excel reporting, and real-time push alerts. All data is stored locally in SQLite with automated backup. Two-way integrations with **Drata** (compliance automation) and **Jira** (ticket management) are included out of the box.

The platform supports five internationally recognised frameworks in a single installation:

| Key | Standard | Scope |
|---|---|---|
| `ISO27001` | ISO/IEC 27001:2022 | Information Security Management System — 93 Annex A controls |
| `SOC2` | AICPA Trust Services Criteria 2017 | Trust Services Criteria for service organisations |
| `NISTCSF` | NIST Cybersecurity Framework 2.0 | US federal and industry cyber risk framework |
| `PCIDSS` | PCI DSS v4.0 | Payment card industry data security standard |
| `ISO42001` | ISO/IEC 42001:2023 | AI Management System — responsible AI governance |

---

## Table of Contents

1. [What Problem This Solves](#1-what-problem-this-solves)
2. [Architecture Overview](#2-architecture-overview)
3. [GRC Process Phases](#3-grc-process-phases)
   - [Phase 1 — Control Register](#phase-1--control-register)
   - [Phase 2 — Risk Assessment](#phase-2--risk-assessment)
   - [Phase 3 — Control Testing](#phase-3--control-testing)
   - [Phase 4 — Audit Management](#phase-4--audit-management)
   - [Phase 5 — Artifact & Evidence Collection](#phase-5--artifact--evidence-collection)
   - [Phase 6 — Reporting](#phase-6--reporting)
   - [Phase 7 — Drata Integration](#phase-7--drata-integration)
   - [Phase 8 — Jira Integration](#phase-8--jira-integration)
   - [Phase 9 — Alerting & Notifications](#phase-9--alerting--notifications)
   - [Phase 10 — Database Backup](#phase-10--database-backup)
4. [Supported Frameworks](#4-supported-frameworks)
5. [Project Structure](#5-project-structure)
6. [Prerequisites & Installation](#6-prerequisites--installation)
7. [Environment Variables](#7-environment-variables)
8. [Quick Start](#8-quick-start)
9. [CLI Reference](#9-cli-reference)
10. [Running Tests](#10-running-tests)
11. [CI/CD Pipeline](#11-cicd-pipeline)
12. [Security Notes](#12-security-notes)

---

## 1. What Problem This Solves

Achieving and maintaining compliance with frameworks like ISO 27001 or SOC 2 is a manual, time-consuming process. Teams typically manage compliance in spreadsheets, track audit findings in email, and chase evidence artefacts by hand — with no visibility into real-time status and no early warning when something slips.

This platform automates the entire lifecycle:

- **Eliminates spreadsheet sprawl** — all controls, risks, tests, findings, and artefacts live in a single local database.
- **Surfaces issues before auditors do** — overdue tests, expiring evidence, and open Major Non-Conformities trigger push alerts the moment they breach thresholds.
- **Closes the loop with your existing tools** — Drata keeps your control statuses in sync automatically; Jira tickets are created for every finding, failed test, and overdue artefact.
- **Supports multiple frameworks simultaneously** — run ISO 27001 and SOC 2 from the same database with a single `--framework` flag.
- **Produces audit-ready outputs** — a fully formatted Excel workbook covering every domain is generated on demand.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        iso27001_grc_main.py                         │
│            CLI entry point · Interactive menu · Orchestration        │
└───────┬─────────────┬──────────────┬──────────────┬────────────────-┘
        │             │              │              │
        ▼             ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────────────┐
│  grc_engine  │ │  drata_  │ │    jira_     │ │  grc_report_       │
│  .py         │ │  integr. │ │  integr.     │ │  generator.py      │
│              │ │  .py     │ │  .py         │ │                    │
│ Controls     │ │          │ │              │ │ Excel (.xlsx)      │
│ Risks        │ │ Controls │ │ Findings →   │ │ report with all    │
│ Tests        │ │ Monitors │ │   tickets    │ │ GRC domains        │
│ Audits       │ │ Evidence │ │ Tests →      │ │                    │
│ Artifacts    │ │          │ │   tickets    │ └────────────────────┘
│ Reviews      │ └──────────┘ │ Risks →      │
│ Backup       │              │   tickets    │ ┌────────────────────┐
└──────┬───────┘              └──────────────┘ │  alerting.py       │
       │                                        │                    │
       ▼                                        │ Slack / Teams      │
┌──────────────┐                               │ webhook alerts     │
│ SQLite DB    │  ◄── grc_database.db           └────────────────────┘
└──────────────┘
       │
       ▼
┌──────────────┐
│  backups/    │  ◄── timestamped .db files (auto-pruned to 7)
└──────────────┘
```

All state is persisted in a local **SQLite database**. Each module is independently testable — no network access is required for the core GRC engine.

---

## 3. GRC Process Phases

The platform implements a complete compliance lifecycle. The phases below map directly to the modules, database tables, and CLI flags in this project.

---

### Phase 1 — Control Register

**What it does:** Loads the full control library for your chosen framework into the database, giving every control a unique ID, owner, implementation status, and linked artefact requirements.

**Why it matters:** The control register is the foundation of the entire programme. Every subsequent phase — risk assessment, testing, audit, evidence — references control IDs. Without a complete, accurate register, nothing else is meaningful.

**How it works in this project:**

Each framework has its own control module (`iso27001_controls.py`, `soc2_controls.py`, etc.). When you run `--init`, the engine calls `load_controls_from_library(framework)`, which iterates through the control definitions and inserts them into the `controls` table. The insert is idempotent — running `--init` a second time will not create duplicates.

Controls start with a status of `Not Implemented`. Status progresses through `In Progress` → `Implemented` → `Not Applicable` as the programme matures.

```bash
# Initialise ISO 27001 (default)
python iso27001_grc_main.py --init

# Initialise a different framework
python iso27001_grc_main.py --init --framework SOC2
```

**Key database table:** `controls`

| Column | Purpose |
|---|---|
| `id` | Framework control ID (e.g. `A.8.8`, `CC6.1`, `PCI.1.2`) |
| `framework` | Which standard owns this control (`ISO27001`, `SOC2`, etc.) |
| `status` | Implementation status |
| `owner` | Person or team accountable |
| `implementation_date` | Date control was implemented |
| `last_reviewed` | Date of last review |

---

### Phase 2 — Risk Assessment

**What it does:** Builds a risk register where each entry captures the asset at risk, the threat and vulnerability, likelihood and impact scores (1–5), treatment decision, and residual risk after controls are applied.

**Why it matters:** ISO 27001 Clause 6.1 and most other frameworks require a documented risk assessment as the basis for selecting controls. A risk register that is not linked to controls is a compliance gap.

**How it works in this project:**

The `add_risk()` function in `grc_engine.py` calculates `inherent_risk = likelihood × impact` and applies a treatment factor to derive `residual_risk`. Treatment options are `Accept`, `Mitigate`, `Transfer`, and `Avoid`. Risks can be linked to one or more control IDs, creating a traceable risk-to-control mapping.

The interactive menu (Option → Add Risk) guides entry of all required fields.

**Key database table:** `risks`

| Column | Purpose |
|---|---|
| `risk_id` | Auto-generated unique ID (e.g. `RISK-4A2B1C3D`) |
| `likelihood` | 1 (rare) to 5 (almost certain) |
| `impact` | 1 (negligible) to 5 (catastrophic) |
| `inherent_risk` | `likelihood × impact` (1–25) |
| `residual_risk` | Post-treatment risk score |
| `treatment` | Accept / Mitigate / Transfer / Avoid |
| `control_ids` | JSON list of linked control IDs |

---

### Phase 3 — Control Testing

**What it does:** Records the results of control effectiveness tests — both design effectiveness (is the control designed correctly?) and operating effectiveness (is it working as intended?) — and automatically updates the linked control's status based on the result.

**Why it matters:** For ISO 27001 Stage 2 and SOC 2 Type II audits, demonstrating that controls are not only implemented but operating effectively is mandatory. Untested controls are treated by auditors as unevidenced controls.

**How it works in this project:**

`record_control_test()` in `grc_engine.py` captures the test name, tester, test type, procedure used, result (Pass / Fail / Partial / Not Tested), finding, and recommendation. It automatically updates the linked control status: a `Pass` sets it to `Implemented`; `Fail` or `Partial` sets it to `In Progress`.

The next test date is calculated from the test date plus a configurable interval (default 12 months). Controls whose `next_test_date` has passed are surfaced by `get_overdue_tests()` and trigger alerts.

**Key database table:** `control_tests`

| Column | Purpose |
|---|---|
| `test_id` | Auto-generated unique ID (e.g. `TEST-9F1A2C3E`) |
| `control_id` | The control being tested |
| `test_type` | `Design` or `Operating Effectiveness` |
| `result` | Pass / Fail / Partial / Not Tested |
| `next_test_date` | Auto-calculated due date for re-test |

---

### Phase 4 — Audit Management

**What it does:** Creates audit records (internal audits, external audits, certification audits), logs findings against specific controls, classifies findings by severity, and tracks corrective actions through to closure.

**Why it matters:** ISO 27001 Clause 9.2 mandates a formal internal audit programme. Every finding must be tracked to closure with documented root cause and corrective action. Open Major Non-Conformities (NCs) at the time of a certification audit will result in a failed certification.

**How it works in this project:**

`create_audit()` creates an audit record. `add_audit_finding()` logs a finding against a control, assigning a severity (`Minor`, `Major`, `Observation`), due date, and corrective action owner. `close_finding()` marks a finding as resolved with a closure note. `get_open_findings()` returns all unresolved findings — used by the alerting module to fire critical notifications for open Major NCs.

**Key database tables:** `audits`, `audit_findings`

| Severity | Description | Alert Level |
|---|---|---|
| `Observation` | Improvement opportunity; not a nonconformity | None |
| `Minor` | Isolated nonconformity; does not affect the system's intent | Warning |
| `Major` | Absence of or complete failure of a required control | Critical |

---

### Phase 5 — Artifact & Evidence Collection

**What it does:** Maintains a checklist of all evidence artefacts required by the framework — policies, procedures, reports, training records, test results — tracks which have been collected, and flags artefacts approaching their expiry date.

**Why it matters:** Evidence collection is the most time-consuming part of any audit. Having a complete, up-to-date artefact register means you always know your collection percentage and never discover gaps the week before an audit.

**How it works in this project:**

`seed_artifact_checklist()` populates the `artifacts` table with all required artefacts for ISO 27001 (279 requirements across all 93 controls). `register_artifact()` marks an artefact as collected and stores its file path and expiry date. `get_expiring_artifacts(days_ahead=30)` returns artefacts whose expiry date falls within the specified window, which drives the alerting module.

**Key database table:** `artifacts`

| Column | Purpose |
|---|---|
| `artifact_name` | Name of the required evidence document |
| `control_id` | The control this artefact evidences |
| `status` | `Pending` or `Collected` |
| `file_path` | Local or network path to the evidence file |
| `expiry_date` | Date the evidence expires and must be re-collected |

---

### Phase 6 — Reporting

**What it does:** Generates a fully formatted, multi-sheet Excel workbook covering every domain of the GRC programme — control register, risk heatmap, test results, audit findings, artefact tracker, and management review log — in a format suitable for presenting to auditors, the board, or leadership.

**Why it matters:** Auditors and leadership need a snapshot view of the programme. A structured, consistently formatted report reduces audit friction and demonstrates organisational maturity.

**How it works in this project:**

`grc_report_generator.py` uses `openpyxl` to build the workbook. Each sheet is styled with headers, conditional formatting (green/amber/red by status), and summary statistics. The report is saved with a date-stamped filename and the output path is configurable via `--out`.

```bash
# Generate report to default location
python iso27001_grc_main.py --report

# Generate to a custom path
python iso27001_grc_main.py --report --out /shared/audit/GRC_Report_Q2.xlsx
```

**Report sheets:**

| Sheet | Contents |
|---|---|
| Summary Dashboard | Overall compliance % and key metrics at a glance |
| Control Register | All controls with status, owner, and implementation date |
| Risk Register | Risk heatmap data with likelihood, impact, and treatment |
| Control Tests | All test records with results and next due dates |
| Audit Findings | All findings with severity, owner, and closure status |
| Artifact Tracker | Evidence checklist with collection status and expiry |
| Management Reviews | Review minutes, decisions, and action items |
| Drata Sync Log | History of synchronisation events with Drata |

---

### Phase 7 — Drata Integration

**What it does:** Synchronises control statuses, monitor results, and evidence from your Drata workspace into the local GRC database — eliminating the need to manually update control statuses that Drata already tracks automatically.

**Why it matters:** Drata continuously monitors cloud controls (MFA enforcement, encryption at rest, logging configuration, etc.). Without integration, that real-time data sits isolated in Drata while your GRC database shows stale statuses. The sync bridges the gap.

**How it works in this project:**

`drata_integration.py` calls three Drata REST API endpoints: `/controls`, `/monitors`, and `/evidence`. All requests use `_request_with_retry()`, which implements exponential back-off, `Retry-After` header handling for rate limits, and schema validation on responses. The API key is never written to logs — only the first four characters are shown via `_mask_secret()`.

Both US and EU regions are supported via the `DRATA_REGION` environment variable.

```bash
# Live sync (requires DRATA_API_KEY)
python iso27001_grc_main.py --drata-sync

# Offline simulation (no API key needed — for testing/demo)
python iso27001_grc_main.py --drata-mock
```

---

### Phase 8 — Jira Integration

**What it does:** Creates Jira tickets automatically for audit findings, failed control tests, overdue artefacts, and at-risk risk register items — ensuring every compliance gap has an owner and a due date in the team's task tracker.

**Why it matters:** GRC findings that are not in the team's workflow system get ignored. Creating Jira tickets automatically closes the loop between the compliance programme and the engineering or operations teams responsible for remediation.

**How it works in this project:**

`jira_integration.py` uses the Jira REST API to create issues in a configurable project. Each ticket is labelled by type (finding, test failure, artefact, risk) and linked back to the control ID. `sync_ticket_statuses()` reads ticket states back from Jira and updates the GRC database — so closing a Jira ticket marks the finding as resolved.

Like the Drata integration, all API calls use `_request_with_retry()` and API tokens are masked in logs.

```bash
# Create live Jira tickets (requires JIRA_* env vars)
python iso27001_grc_main.py --jira

# Simulate ticket creation (offline/demo)
python iso27001_grc_main.py --jira-mock
```

---

### Phase 9 — Alerting & Notifications

**What it does:** Monitors the GRC database for breach conditions and fires push notifications to Slack and/or Microsoft Teams the moment a threshold is crossed — without waiting for someone to run a report.

**Why it matters:** Compliance programmes fail silently. Evidence expires without anyone noticing; tests go overdue; Major NCs stay open past their due date. Real-time alerts turn passive monitoring into active governance.

**Conditions monitored:**

| Condition | Severity | Trigger |
|---|---|---|
| Evidence artefact has passed its expiry date | 🔴 Critical | Immediately on `--alert-check` |
| Evidence artefact expiring within 30 days | ⚠️ Warning | `days_ahead` window (configurable) |
| Control test is past its next test date | ⚠️ Warning | Overdue by any amount |
| Open Major Non-Conformity finding | 🔴 Critical | Count exceeds threshold (default: 0) |

**How it works in this project:**

`alerting.py` reads `SLACK_WEBHOOK_URL` and `TEAMS_WEBHOOK_URL` from environment variables. If neither is set, the application runs normally — alerting is entirely optional. `send_webhook_alert()` formats the payload to the correct schema for each platform (Slack attachment format; Teams MessageCard format).

```bash
# Verify your webhook is working
python iso27001_grc_main.py --alert-test

# Run all alert condition checks
python iso27001_grc_main.py --alert-check
```

To run alert checks on a schedule, add a cron entry:

```cron
# Daily GRC alert check at 08:00
0 8 * * * cd /path/to/grc && python iso27001_grc_main.py --alert-check
```

---

### Phase 10 — Database Backup

**What it does:** Creates timestamped, point-in-time backups of the SQLite database using SQLite's native online backup API — which is safe to run while the database is actively in use. Old backups are automatically pruned to keep the most recent 7.

**Why it matters:** The GRC database is the single source of truth for the entire compliance programme. A single file corruption event without a backup would mean total loss of all control statuses, risk assessments, audit findings, test records, and artefact evidence.

**How it works in this project:**

`backup_database()` in `grc_engine.py` uses `sqlite3.Connection.backup()` to create a consistent copy. After each backup, `_prune_backups()` sorts all backup files by timestamp and deletes any beyond the `GRC_MAX_BACKUPS` limit (default 7). The backup directory and retention count are both configurable via environment variables.

```bash
# Manual backup
python iso27001_grc_main.py --backup

# Custom backup directory
GRC_BACKUP_DIR=/mnt/nas/grc-backups python iso27001_grc_main.py --backup

# Keep 14 backups instead of 7
GRC_MAX_BACKUPS=14 python iso27001_grc_main.py --backup
```

---

## 4. Supported Frameworks

### ISO/IEC 27001:2022 — Information Security Management

The flagship framework. All 93 Annex A controls are implemented across four themes: Organisational (A.5, 37 controls), People (A.6, 8 controls), Physical (A.7, 14 controls), and Technological (A.8, 34 controls). The artifact checklist covers 279 evidence requirements across all controls. The control library is versioned with `STANDARD_VERSION`, `STANDARD_PUBLISHED_DATE`, and `LIBRARY_LAST_REVIEWED` constants, and CI tests assert the control count matches `CONTROL_COUNT_EXPECTED`.

### AICPA SOC 2 — Trust Services Criteria (2017)

32 criteria covering the five Trust Services Categories: Common Criteria (CC), Availability (A), Confidentiality (C), Processing Integrity (PI), and Privacy (P). Designed for service organisations undergoing SOC 2 Type I or Type II examinations.

### NIST Cybersecurity Framework 2.0

31 controls mapped to all six CSF 2.0 Functions: **Govern** (new in 2.0), **Identify**, **Protect**, **Detect**, **Respond**, and **Recover**. Widely used by US federal agencies and critical infrastructure operators, and increasingly adopted globally as a risk-based cyber framework.

### PCI DSS v4.0

27 controls spanning all 12 PCI DSS Requirements — from network security and configuration hardening through access control, logging, cryptography, vulnerability management, and incident response. Applicable to any organisation that stores, processes, or transmits cardholder data.

### ISO/IEC 42001:2023 — AI Management System

39 controls covering the complete AIMS lifecycle: Clauses 4–10 (context, leadership, planning, support, operation, evaluation, improvement) plus Annex A (organisational AI controls) and Annex B (AI impact assessment). The world's first international standard for responsible AI governance, applicable to any organisation developing, deploying, or procuring AI systems.

---

## 5. Project Structure

```
GRC Preparation/
│
│  ── Entry point ────────────────────────────────────────────────────
├── iso27001_grc_main.py       CLI, interactive menu, command dispatch
│
│  ── Core engine ────────────────────────────────────────────────────
├── grc_engine.py              DB schema, controls, risks, tests, audits,
│                              artifacts, management reviews, backup & pruning
│
│  ── Integrations ───────────────────────────────────────────────────
├── drata_integration.py       Drata REST API sync (controls, monitors, evidence)
├── jira_integration.py        Jira ticket creation and status sync
├── alerting.py                Slack / Teams webhook push notifications
│
│  ── Reporting ──────────────────────────────────────────────────────
├── grc_report_generator.py    Excel (.xlsx) GRC report generator
│
│  ── Control libraries ──────────────────────────────────────────────
├── iso27001_controls.py       ISO 27001:2022 — 93 Annex A controls
├── soc2_controls.py           SOC 2 TSC 2017 — 32 Trust Services Criteria
├── nist_csf_controls.py       NIST CSF 2.0 — 31 controls across 6 functions
├── pci_dss_controls.py        PCI DSS v4.0 — 27 controls across 12 requirements
├── iso42001_controls.py       ISO 42001:2023 — 39 AI Management System controls
│
│  ── Supporting files ───────────────────────────────────────────────
├── process_diagrams.mermaid   GRC process flow diagrams (Mermaid syntax)
├── requirements.txt           Python dependencies
├── pyproject.toml             Package metadata and tool configuration
├── .env.example               Environment variable template
│
│  ── Generated at runtime ──────────────────────────────────────────
├── grc_database.db            SQLite database (created on --init)
├── backups/                   Timestamped DB backups (auto-pruned to 7)
├── *.xlsx                     GRC Excel reports
│
│  ── CI/CD ──────────────────────────────────────────────────────────
├── .github/
│   └── workflows/
│       └── ci.yml             GitHub Actions: unit tests + offline smoke tests
│
│  ── Tests ───────────────────────────────────────────────────────────
└── tests/
    ├── __init__.py
    ├── test_grc_engine.py     DB, controls, risks, tests, audits,
    │                          artifacts, backup, standard version tracking
    └── test_api_hardening.py  Retry logic, credential masking,
                               schema validation, region config
```

---

## 6. Prerequisites & Installation

**Requires Python 3.9 or higher.**

```bash
# 1. Clone the repository
git clone https://github.com/your-org/grc-automation.git
cd grc-automation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and fill in your API keys
```

---

## 7. Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DRATA_API_KEY` | For live sync | — | Drata workspace API key |
| `DRATA_REGION` | No | `us` | Drata region: `us` or `eu` |
| `JIRA_BASE_URL` | For Jira | — | Atlassian Cloud base URL |
| `JIRA_EMAIL` | For Jira | — | Atlassian account email |
| `JIRA_API_TOKEN` | For Jira | — | Jira REST API token |
| `JIRA_PROJECT_KEY` | For Jira | — | Jira project key (e.g. `GRC`) |
| `SLACK_WEBHOOK_URL` | No | — | Slack Incoming Webhook URL |
| `TEAMS_WEBHOOK_URL` | No | — | MS Teams Incoming Webhook URL |
| `GRC_LOG_LEVEL` | No | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `GRC_LOG_FILE` | No | — | Path for rotating log file (stdout if unset) |
| `GRC_DB_PATH` | No | `./grc_database.db` | Override SQLite database path |
| `GRC_BACKUP_DIR` | No | `./backups` | Override backup directory |
| `GRC_MAX_BACKUPS` | No | `7` | Maximum backup files to retain |

All variables can be set in a `.env` file at the project root (loaded automatically via `python-dotenv`) or exported as shell environment variables.

---

## 8. Quick Start

```bash
# ── Phase 1: Initialise the control register ─────────────────────────
python iso27001_grc_main.py --init                        # ISO 27001 (default)
python iso27001_grc_main.py --init --framework SOC2       # SOC 2
python iso27001_grc_main.py --init --framework NISTCSF    # NIST CSF 2.0
python iso27001_grc_main.py --init --framework PCIDSS     # PCI DSS v4.0
python iso27001_grc_main.py --init --framework ISO42001   # ISO 42001

# ── Run the full offline demo (no API keys needed) ────────────────────
python iso27001_grc_main.py --demo

# ── Check programme status ────────────────────────────────────────────
python iso27001_grc_main.py --status
python iso27001_grc_main.py --status --framework ISO42001

# ── Sync with Drata ───────────────────────────────────────────────────
python iso27001_grc_main.py --drata-mock    # offline simulation
python iso27001_grc_main.py --drata-sync    # live (requires DRATA_API_KEY)

# ── Sync with Jira ────────────────────────────────────────────────────
python iso27001_grc_main.py --jira-mock     # offline simulation
python iso27001_grc_main.py --jira          # live (requires JIRA_* vars)

# ── Generate the Excel GRC report ────────────────────────────────────
python iso27001_grc_main.py --report
python iso27001_grc_main.py --report --out /path/to/output.xlsx

# ── Backup the database ───────────────────────────────────────────────
python iso27001_grc_main.py --backup

# ── Alerting ──────────────────────────────────────────────────────────
python iso27001_grc_main.py --alert-test    # send a test notification
python iso27001_grc_main.py --alert-check   # run all alert condition checks
```

---

## 9. CLI Reference

```
python iso27001_grc_main.py [OPTIONS]

Flags:
  (none)              Launch the interactive menu
  --init              Initialise DB and seed control library
  --demo              Run a complete end-to-end demo workflow
  --status            Print GRC status summary to the terminal
  --report            Generate the Excel GRC report
  --drata-sync        Full live sync from Drata (requires DRATA_API_KEY)
  --drata-mock        Simulate Drata sync — offline, no API key needed
  --jira              Create/sync Jira tickets (requires JIRA_* variables)
  --jira-mock         Simulate Jira ticket creation — offline
  --backup            Create a timestamped database backup
  --alert-test        Send a test notification to all configured webhooks
  --alert-check       Run all GRC alert condition checks

Options:
  --framework FW      Control framework to use with --init and --status.
                      Values: ISO27001 (default) | SOC2 | NISTCSF | PCIDSS | ISO42001
  --out PATH          Custom output path for --report
```

---

## 10. Running Tests

The test suite requires no live API keys or network access. All external calls are mocked.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing

# Run a specific test file
pytest tests/test_grc_engine.py -v
pytest tests/test_api_hardening.py -v
```

**Test coverage includes:**

- Database initialisation and idempotency
- Control loading for ISO 27001 (count and required field validation)
- Risk register CRUD and score calculation
- Control test recording and status propagation
- Audit creation, finding management, and closure
- Artefact registration and collection status
- Database backup creation and validity
- Standard version constant verification
- Drata and Jira credential masking
- Retry logic (503 retries, 429 rate limiting, 4xx no-retry)
- API response schema validation
- Region configuration via environment variable

---

## 11. CI/CD Pipeline

The GitHub Actions workflow at `.github/workflows/ci.yml` runs automatically on every push and pull request.

**Jobs:**

| Job | Trigger | What it does |
|---|---|---|
| `Unit Tests` | Every push / PR | Runs `pytest tests/ --cov` |
| `Offline Smoke Test` | After unit tests pass | Runs all CLI commands with mock data for all 5 frameworks |
| `Live Integration` | Push to `main` only (opt-in) | Runs live Drata and Jira syncs using repository secrets |

To enable live integration tests, set the repository variable `RUN_LIVE_INTEGRATION` to `true` and add the following secrets under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `DRATA_API_KEY` | Drata workspace API key |
| `DRATA_REGION` | `us` or `eu` |
| `JIRA_BASE_URL` | Your Atlassian Cloud base URL |
| `JIRA_EMAIL` | Email associated with the Jira token |
| `JIRA_API_TOKEN` | Jira REST API token |
| `JIRA_PROJECT_KEY` | Jira project key (e.g. `GRC`) |
| `SLACK_WEBHOOK_URL` | Optional — for alert notification tests |
| `TEAMS_WEBHOOK_URL` | Optional — for alert notification tests |

---

## 12. Security Notes

- **Never commit `.env`** — it is git-ignored. Commit only `.env.example` with placeholder values.
- **API keys are masked in all log output** — only the first four characters are visible. The full key value will never appear in log files or console output.
- **SQLite database permissions** — the `grc_database.db` file contains sensitive compliance data. Restrict permissions: `chmod 600 grc_database.db`.
- **Backup files** contain the same sensitive data as the primary database. Store them in a location with equivalent access controls.
- **For multi-user or production deployments**, consider migrating the SQLite backend to PostgreSQL. The schema is standard SQL and requires minimal changes.
- **Drata and Jira tokens** should be scoped to the minimum required permissions (read-only for Drata sync; create-issue for Jira).

---

*GRC Automation Framework · Maintained by the GRC Team · Last updated: 2026-04-07*
