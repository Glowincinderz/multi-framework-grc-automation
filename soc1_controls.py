"""
SOC 1 (SSAE 18 / AT-C 320, ISAE 3402) — Control Objectives Library

A SOC 1 report covers a service organisation's controls that are relevant to its
user entities' internal control over financial reporting (ICFR). Unlike SOC 2, there
is no fixed criteria set: management defines control objectives and the controls
that achieve them. This library provides a typical baseline of IT general control
(ITGC) and business process control objectives that a service organisation would
adapt to its own system description, plus the entity-level, subservice organisation
and complementary user entity control (CUEC) areas every SOC 1 report addresses.

Themes:
  Control Environment          — entity-level controls supporting ICFR
  Logical Access               — ITGC: provisioning, reviews, privileged access, terminations
  Change Management            — ITGC: application and infrastructure changes
  Program Development          — ITGC: new systems and significant upgrades
  Computer Operations          — ITGC: job scheduling, backups, incident handling
  Transaction Processing       — business process: input, processing and output accuracy
  Interfaces & Reconciliation  — business process: data transfers and reconciliations
  Subservice & User Entities   — carve-out/inclusive subservice orgs and CUECs

Use with: python iso27001_grc_main.py --init --framework SOC1
"""

STANDARD_VERSION        = "SSAE 18 (AT-C 320) / ISAE 3402 — SOC 1 Type I & Type II"
STANDARD_PUBLISHED_DATE = "2017-05-01"   # SSAE 18 effective date
LIBRARY_LAST_REVIEWED   = "2026-11-21"
CONTROL_COUNT_EXPECTED  = 24

SOC1_CONTROLS = [
    # --- Control Environment ---
    {"id": "SOC1-CE.1", "theme": "Control Environment",
     "title": "Governance and Oversight of Service Delivery",
     "description": "Management and the board oversee the design and operation of controls relevant to user entities' financial reporting, including an annual risk assessment of the services in scope.",
     "artifacts": ["Board / audit committee minutes", "Risk assessment", "Organisation chart"],
     "test_procedure": "Inspect committee minutes and the annual risk assessment for review of in-scope services and control deficiencies."},

    {"id": "SOC1-CE.2", "theme": "Control Environment",
     "title": "Code of Conduct and Personnel Screening",
     "description": "Personnel acknowledge the code of conduct, and background checks are completed before access to in-scope systems is granted.",
     "artifacts": ["Code of conduct acknowledgements", "Background check records", "Onboarding checklist"],
     "test_procedure": "For a sample of new hires, inspect signed acknowledgements and completed background checks dated before system access."},

    {"id": "SOC1-CE.3", "theme": "Control Environment",
     "title": "Policies and Procedures for In-Scope Services",
     "description": "Documented policies and procedures govern the services in scope and are reviewed and approved at least annually.",
     "artifacts": ["Policy library", "Annual review approvals", "Procedure documents"],
     "test_procedure": "Inspect in-scope policies for documented annual review and management approval."},

    # --- Logical Access (ITGC) ---
    {"id": "SOC1-LA.1", "theme": "Logical Access",
     "title": "User Access Provisioning",
     "description": "Access to in-scope applications, databases and infrastructure is granted only on approved requests that are consistent with job responsibilities.",
     "artifacts": ["Access request tickets", "Approval evidence", "Role definitions"],
     "test_procedure": "For a sample of new or changed accounts, inspect approved access requests that match the access granted."},

    {"id": "SOC1-LA.2", "theme": "Logical Access",
     "title": "Timely Removal of Access on Termination",
     "description": "Access for terminated personnel is removed within the defined timeframe (for example, one business day).",
     "artifacts": ["HR termination listing", "Deprovisioning tickets", "System account listings"],
     "test_procedure": "Compare HR terminations to account removal dates for a sample; confirm removal within the defined timeframe."},

    {"id": "SOC1-LA.3", "theme": "Logical Access",
     "title": "Periodic User Access Reviews",
     "description": "Owners review user access to in-scope systems at least quarterly, and inappropriate access is removed.",
     "artifacts": ["Quarterly access review sign-offs", "Remediation tickets", "User listings used in review"],
     "test_procedure": "Inspect a sample of quarterly reviews for completeness of the population, reviewer sign-off and remediation of exceptions."},

    {"id": "SOC1-LA.4", "theme": "Logical Access",
     "title": "Privileged Access Restriction and Monitoring",
     "description": "Administrative and privileged access is restricted to authorised personnel and its use is logged and reviewed.",
     "artifacts": ["Privileged account listing", "PAM logs", "Log review evidence"],
     "test_procedure": "Inspect the privileged user listing for appropriateness and evidence of periodic log review."},

    {"id": "SOC1-LA.5", "theme": "Logical Access",
     "title": "Authentication and Password Requirements",
     "description": "In-scope systems enforce unique user IDs, MFA for remote and privileged access, and password parameters consistent with policy.",
     "artifacts": ["SSO / MFA configuration", "Password policy settings", "Authentication standard"],
     "test_procedure": "Inspect authentication configurations for in-scope systems against the authentication standard."},

    {"id": "SOC1-LA.6", "theme": "Logical Access",
     "title": "Segregation of Duties",
     "description": "Incompatible duties (for example, developing and deploying changes, or initiating and approving transactions) are segregated or compensated by review.",
     "artifacts": ["SoD matrix", "SoD conflict report", "Compensating control evidence"],
     "test_procedure": "Inspect the SoD conflict report; for conflicts, inspect evidence of compensating review."},

    # --- Change Management (ITGC) ---
    {"id": "SOC1-CM.1", "theme": "Change Management",
     "title": "Change Authorisation, Testing and Approval",
     "description": "Changes to in-scope applications and infrastructure are documented, tested and approved before implementation.",
     "artifacts": ["Change tickets", "Test evidence", "CAB / approver sign-off"],
     "test_procedure": "For a sample of changes from the system-generated population, inspect testing and approval before deployment."},

    {"id": "SOC1-CM.2", "theme": "Change Management",
     "title": "Restricted Access to Migrate Changes to Production",
     "description": "Only authorised personnel independent of development can migrate changes to production.",
     "artifacts": ["Deployment pipeline permissions", "Production access listing"],
     "test_procedure": "Inspect deployment permissions; confirm developers cannot deploy to production without independent approval."},

    {"id": "SOC1-CM.3", "theme": "Change Management",
     "title": "Emergency Change Handling",
     "description": "Emergency changes are documented and retrospectively reviewed and approved within a defined period.",
     "artifacts": ["Emergency change log", "Retrospective approvals"],
     "test_procedure": "For a sample of emergency changes, inspect retrospective review and approval within the defined period."},

    # --- Program Development (ITGC) ---
    {"id": "SOC1-PD.1", "theme": "Program Development",
     "title": "New System Development and Data Conversion",
     "description": "New in-scope systems and significant upgrades follow an approved SDLC, including user acceptance testing and validated data conversion.",
     "artifacts": ["Project approval", "UAT sign-off", "Data conversion reconciliation"],
     "test_procedure": "For in-scope implementations during the period, inspect UAT sign-off and data conversion validation."},

    # --- Computer Operations (ITGC) ---
    {"id": "SOC1-CO.1", "theme": "Computer Operations",
     "title": "Batch Job Scheduling and Monitoring",
     "description": "Scheduled jobs that process user entity data are authorised, monitored, and failures are investigated and resolved.",
     "artifacts": ["Job schedule", "Job failure alerts", "Resolution tickets"],
     "test_procedure": "Inspect job scheduler access and, for a sample of failures, evidence of investigation and resolution."},

    {"id": "SOC1-CO.2", "theme": "Computer Operations",
     "title": "Backup and Restoration",
     "description": "In-scope data is backed up according to schedule, backup failures are resolved, and restoration is tested at least annually.",
     "artifacts": ["Backup configuration", "Backup failure tickets", "Restore test results"],
     "test_procedure": "Inspect backup configuration and the annual restore test; for a sample of failures, inspect resolution."},

    {"id": "SOC1-CO.3", "theme": "Computer Operations",
     "title": "Incident and Problem Management",
     "description": "Incidents affecting in-scope processing are logged, prioritised, resolved and, where relevant, communicated to user entities.",
     "artifacts": ["Incident tickets", "Root cause analyses", "Customer notifications"],
     "test_procedure": "For a sample of incidents, inspect logging, resolution and customer communication where required."},

    # --- Transaction Processing (business process) ---
    {"id": "SOC1-TP.1", "theme": "Transaction Processing",
     "title": "Completeness and Accuracy of Input",
     "description": "Transactions received from user entities are validated for completeness and accuracy, and rejected items are tracked to resolution.",
     "artifacts": ["Input validation rules", "Exception reports", "Resolution evidence"],
     "test_procedure": "Inspect validation rule configuration and, for a sample of exceptions, resolution evidence."},

    {"id": "SOC1-TP.2", "theme": "Transaction Processing",
     "title": "Accurate and Timely Processing",
     "description": "Transactions are processed accurately, completely and in the correct period, according to user entity instructions.",
     "artifacts": ["System calculation configuration", "Processing reports", "Cut-off evidence"],
     "test_procedure": "Re-perform a sample of calculations and inspect cut-off procedures at period end."},

    {"id": "SOC1-TP.3", "theme": "Transaction Processing",
     "title": "Complete and Accurate Output and Reporting",
     "description": "Reports provided to user entities are complete, accurate and delivered only to authorised recipients.",
     "artifacts": ["Report specifications", "Report review evidence", "Distribution lists"],
     "test_procedure": "For a sample of user entity reports, agree data to source and inspect distribution to authorised recipients."},

    # --- Interfaces & Reconciliation (business process) ---
    {"id": "SOC1-IR.1", "theme": "Interfaces & Reconciliation",
     "title": "Interface and Data Transfer Controls",
     "description": "Automated interfaces and file transfers are monitored for completeness, and failed or partial transfers are investigated.",
     "artifacts": ["Interface monitoring dashboards", "Control totals", "Failure tickets"],
     "test_procedure": "Inspect interface control totals and, for a sample of failures, investigation and resolution."},

    {"id": "SOC1-IR.2", "theme": "Interfaces & Reconciliation",
     "title": "Periodic Reconciliations",
     "description": "Key balances and transaction populations are reconciled on a defined cadence, with differences investigated and approved by a reviewer.",
     "artifacts": ["Reconciliation workpapers", "Reviewer sign-off", "Variance investigations"],
     "test_procedure": "For a sample of periods, inspect reconciliations for timely preparation, independent review and resolution of differences."},

    # --- Subservice & User Entities ---
    {"id": "SOC1-SU.1", "theme": "Subservice & User Entities",
     "title": "Monitoring of Subservice Organisations",
     "description": "Management obtains and reviews SOC 1 reports (or equivalent) for subservice organisations, evaluates exceptions and bridge letters, and confirms its own complementary subservice organisation controls (CSOCs).",
     "artifacts": ["Subservice SOC 1 reports", "Report review checklist", "Bridge letters", "CSOC mapping"],
     "test_procedure": "Inspect evidence of annual review of each carve-out subservice organisation's report, including exceptions and CSOCs."},

    {"id": "SOC1-SU.2", "theme": "Subservice & User Entities",
     "title": "Complementary User Entity Controls (CUECs) Communicated",
     "description": "Controls that user entities must operate for the control objectives to be achieved are identified in the system description and communicated to customers.",
     "artifacts": ["System description CUEC section", "Customer communications", "Contract terms"],
     "test_procedure": "Inspect the system description for CUECs mapped to each relevant control objective and evidence they were communicated."},

    {"id": "SOC1-SU.3", "theme": "Subservice & User Entities",
     "title": "Bridge Letters Between Report Periods",
     "description": "Bridge (gap) letters are issued to user entities to cover the period between the end of the SOC 1 report period and their fiscal year end.",
     "artifacts": ["Bridge letter template", "Issued bridge letters"],
     "test_procedure": "Inspect issued bridge letters for coverage of the gap period and management representation of no material changes."},
]
