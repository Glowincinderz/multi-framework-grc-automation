"""
SOC 2 Trust Services Criteria (2017) — Control Library
Based on AICPA TSC 2017 (updated for SOC 2 Type I & II engagements).

Themes align with the Trust Services Categories:
  CC  - Common Criteria (Security)
  A   - Availability
  C   - Confidentiality
  PI  - Processing Integrity
  P   - Privacy

SWOT Remediation — Prompt 9 (2026-04-07): added to support multi-framework.
"""

SOC2_CONTROLS = [
    # ─────────────────────────────────────────────────────────────────────────
    # CC1 — CONTROL ENVIRONMENT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC1.1", "theme": "Common Criteria",
     "title": "COSO Principle 1 — Demonstrates Commitment to Integrity and Ethical Values",
     "description": "The entity demonstrates a commitment to integrity and ethical values.",
     "artifacts": ["Code of Conduct", "Ethics policy", "Employee acknowledgements"],
     "test_procedure": "Inspect Code of Conduct; verify signed employee acknowledgements."},

    {"id": "CC1.2", "theme": "Common Criteria",
     "title": "COSO Principle 2 — Board Independence and Oversight",
     "description": "The board of directors demonstrates independence from management and exercises oversight.",
     "artifacts": ["Board charter", "Meeting minutes", "Committee charters"],
     "test_procedure": "Review board charter and meeting minutes for evidence of oversight activities."},

    {"id": "CC1.3", "theme": "Common Criteria",
     "title": "COSO Principle 3 — Organisational Structure and Reporting Lines",
     "description": "Management establishes structures, reporting lines, and appropriate authorities.",
     "artifacts": ["Org chart", "RACI matrix", "Job descriptions"],
     "test_procedure": "Verify org chart reflects current structure; inspect reporting line assignments."},

    {"id": "CC1.4", "theme": "Common Criteria",
     "title": "COSO Principle 4 — Commitment to Competence",
     "description": "The entity demonstrates a commitment to attract, develop, and retain competent individuals.",
     "artifacts": ["Training records", "Competency frameworks", "Performance reviews"],
     "test_procedure": "Sample employee training records; verify role-based training completions."},

    {"id": "CC1.5", "theme": "Common Criteria",
     "title": "COSO Principle 5 — Accountability for Internal Control",
     "description": "The entity holds individuals accountable for their internal control responsibilities.",
     "artifacts": ["Control owner assignments", "Performance metrics", "Disciplinary procedures"],
     "test_procedure": "Verify control owners are assigned; inspect accountability mechanisms."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC2 — COMMUNICATION AND INFORMATION
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC2.1", "theme": "Common Criteria",
     "title": "COSO Principle 13 — Uses Relevant Quality Information",
     "description": "The entity obtains or generates and uses relevant, quality information to support internal control.",
     "artifacts": ["Information quality standards", "Data governance policy"],
     "test_procedure": "Review data governance policy; inspect data quality controls."},

    {"id": "CC2.2", "theme": "Common Criteria",
     "title": "COSO Principle 14 — Internally Communicates Information",
     "description": "The entity internally communicates information, including objectives and responsibilities.",
     "artifacts": ["Internal communications records", "Policy distribution evidence"],
     "test_procedure": "Verify policy distribution to staff; inspect internal communication logs."},

    {"id": "CC2.3", "theme": "Common Criteria",
     "title": "COSO Principle 15 — Externally Communicates",
     "description": "The entity communicates with external parties regarding matters affecting internal control.",
     "artifacts": ["Privacy notices", "Vendor communications", "SLA agreements"],
     "test_procedure": "Review customer-facing privacy notices; inspect vendor communication records."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC3 — RISK ASSESSMENT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC3.1", "theme": "Common Criteria",
     "title": "COSO Principle 6 — Specifies Suitable Objectives",
     "description": "The entity specifies objectives with sufficient clarity to identify and assess risks.",
     "artifacts": ["Risk register", "Service objectives documentation"],
     "test_procedure": "Inspect risk register; verify objectives are documented and approved."},

    {"id": "CC3.2", "theme": "Common Criteria",
     "title": "COSO Principle 7 — Identifies and Analyses Risk",
     "description": "The entity identifies risks to achieving objectives and analyses them.",
     "artifacts": ["Risk assessment", "Risk treatment plans", "Risk acceptance records"],
     "test_procedure": "Review risk assessment methodology; verify risks are rated and treated."},

    {"id": "CC3.3", "theme": "Common Criteria",
     "title": "COSO Principle 8 — Assesses Fraud Risk",
     "description": "The entity considers the potential for fraud in assessing risks to achievement of objectives.",
     "artifacts": ["Fraud risk assessment", "Anti-fraud controls documentation"],
     "test_procedure": "Inspect fraud risk assessment; verify anti-fraud controls are in place."},

    {"id": "CC3.4", "theme": "Common Criteria",
     "title": "COSO Principle 9 — Identifies and Analyses Significant Change",
     "description": "The entity identifies and assesses changes that could significantly impact internal control.",
     "artifacts": ["Change management records", "Risk reassessment evidence"],
     "test_procedure": "Sample change records; verify risk reassessments were triggered."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC5 — CONTROL ACTIVITIES
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC5.1", "theme": "Common Criteria",
     "title": "COSO Principle 10 — Selects and Develops Control Activities",
     "description": "The entity selects and develops control activities that mitigate risks to acceptable levels.",
     "artifacts": ["Control inventory", "Risk-to-control mapping"],
     "test_procedure": "Verify controls are mapped to risks; inspect control design documentation."},

    {"id": "CC5.2", "theme": "Common Criteria",
     "title": "COSO Principle 11 — Selects General Technology Controls",
     "description": "The entity also selects and develops general control activities over technology.",
     "artifacts": ["IT general controls documentation", "Technology risk assessment"],
     "test_procedure": "Review IT general controls; verify technology risks are addressed."},

    {"id": "CC5.3", "theme": "Common Criteria",
     "title": "COSO Principle 12 — Deploys Through Policies and Procedures",
     "description": "The entity deploys control activities through policies, procedures, and technology.",
     "artifacts": ["Policy library", "Standard Operating Procedures", "Policy review log"],
     "test_procedure": "Sample policies; verify current versions are approved and communicated."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC6 — LOGICAL AND PHYSICAL ACCESS CONTROLS
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC6.1", "theme": "Common Criteria",
     "title": "Logical Access Security",
     "description": "The entity implements logical access security software, infrastructure, and architectures.",
     "artifacts": ["Access control policy", "MFA enforcement evidence", "IAM configuration"],
     "test_procedure": "Verify MFA is enforced for privileged access; inspect IAM role assignments."},

    {"id": "CC6.2", "theme": "Common Criteria",
     "title": "Access Provisioning and De-provisioning",
     "description": "Prior to issuing credentials, the entity registers and authorises new internal and external users.",
     "artifacts": ["Access request records", "Joiner/mover/leaver process documentation"],
     "test_procedure": "Sample new-hire access provisioning; verify terminated users are de-provisioned."},

    {"id": "CC6.3", "theme": "Common Criteria",
     "title": "Role-Based Access and Least Privilege",
     "description": "The entity authorises, modifies, or removes access based on roles and least privilege.",
     "artifacts": ["Role definition matrix", "Access review results", "Privileged access log"],
     "test_procedure": "Verify role definitions; inspect quarterly access review results."},

    {"id": "CC6.6", "theme": "Common Criteria",
     "title": "Logical Access From External Sources",
     "description": "Logical access security measures restrict access to assets from persons acting from outside boundaries.",
     "artifacts": ["VPN / Zero Trust config", "Remote access policy", "Firewall rules"],
     "test_procedure": "Inspect firewall rules and VPN configuration; verify remote access policy."},

    {"id": "CC6.7", "theme": "Common Criteria",
     "title": "Transmission and Disclosure of Information",
     "description": "The entity restricts the transmission, movement, and removal of information to authorised parties.",
     "artifacts": ["Data classification policy", "DLP configuration", "Encryption standards"],
     "test_procedure": "Verify encryption in transit; inspect DLP policy and configuration."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC7 — SYSTEM OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC7.1", "theme": "Common Criteria",
     "title": "Vulnerability Management",
     "description": "To meet objectives, the entity uses detection and monitoring procedures.",
     "artifacts": ["Vulnerability scan reports", "Patch management records", "CVE tracking log"],
     "test_procedure": "Review vulnerability scan results; verify critical patches are applied timely."},

    {"id": "CC7.2", "theme": "Common Criteria",
     "title": "Security Event Monitoring",
     "description": "The entity monitors system components and the operation of those components for anomalies.",
     "artifacts": ["SIEM alert configuration", "Incident log", "Monitoring dashboard"],
     "test_procedure": "Inspect SIEM configuration; sample alerts and verify investigation records."},

    {"id": "CC7.3", "theme": "Common Criteria",
     "title": "Evaluation of Security Events",
     "description": "The entity evaluates security events to determine whether they could or have resulted in failure.",
     "artifacts": ["Incident response log", "Triage records", "Post-incident reviews"],
     "test_procedure": "Sample security events; verify triage and escalation procedures were followed."},

    {"id": "CC7.4", "theme": "Common Criteria",
     "title": "Incident Response",
     "description": "The entity responds to identified security incidents by executing a defined incident response program.",
     "artifacts": ["Incident Response Plan", "IR exercise records", "Post-incident reports"],
     "test_procedure": "Review IRP; inspect tabletop exercise reports; verify IR roles are assigned."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC8 — CHANGE MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC8.1", "theme": "Common Criteria",
     "title": "Change Management Process",
     "description": "The entity authorises, designs, develops, acquires, implements, and maintains infrastructure.",
     "artifacts": ["Change management policy", "Change approval records", "Rollback plans"],
     "test_procedure": "Sample change requests; verify approval, testing, and rollback documentation."},

    # ─────────────────────────────────────────────────────────────────────────
    # CC9 — RISK MITIGATION
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "CC9.1", "theme": "Common Criteria",
     "title": "Risk Mitigation Activities",
     "description": "The entity identifies, selects, and develops risk mitigation activities for risks.",
     "artifacts": ["Risk treatment plan", "Control implementation evidence"],
     "test_procedure": "Review risk treatment decisions; verify mitigation controls are implemented."},

    {"id": "CC9.2", "theme": "Common Criteria",
     "title": "Vendor and Business Partner Management",
     "description": "The entity assesses and manages risks associated with vendors and business partners.",
     "artifacts": ["Vendor risk assessments", "Third-party contracts with security clauses", "Vendor register"],
     "test_procedure": "Sample vendor risk assessments; verify security requirements in contracts."},

    # ─────────────────────────────────────────────────────────────────────────
    # A — AVAILABILITY
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "A1.1", "theme": "Availability",
     "title": "Availability Commitments and System Requirements",
     "description": "The entity maintains, monitors, and evaluates current processing capacity and use.",
     "artifacts": ["SLA documentation", "Capacity monitoring reports", "Uptime reports"],
     "test_procedure": "Review SLA commitments; inspect uptime and capacity monitoring reports."},

    {"id": "A1.2", "theme": "Availability",
     "title": "Environmental Protections and Backup",
     "description": "The entity authorises, designs, develops, acquires, implements, operates, approves, maintains environmental protections.",
     "artifacts": ["Backup policy", "Backup test results", "DR plan", "BCP"],
     "test_procedure": "Verify backup schedules; inspect backup restoration test results."},

    {"id": "A1.3", "theme": "Availability",
     "title": "Recovery Plan Testing",
     "description": "The entity tests recovery plan procedures to support availability commitments.",
     "artifacts": ["DR test records", "BCP exercise reports", "RTO/RPO documentation"],
     "test_procedure": "Review DR test results; verify RTO/RPO targets were met."},

    # ─────────────────────────────────────────────────────────────────────────
    # C — CONFIDENTIALITY
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "C1.1", "theme": "Confidentiality",
     "title": "Identification and Designation of Confidential Information",
     "description": "The entity identifies and designates confidential information to meet its commitments.",
     "artifacts": ["Data classification policy", "Data inventory", "Classification labels"],
     "test_procedure": "Verify data classification policy; inspect data inventory for classification labels."},

    {"id": "C1.2", "theme": "Confidentiality",
     "title": "Disposal of Confidential Information",
     "description": "The entity disposes of confidential information to meet its confidentiality commitments.",
     "artifacts": ["Data retention policy", "Media disposal records", "Secure deletion evidence"],
     "test_procedure": "Inspect media disposal records; verify secure deletion procedures are followed."},
]
