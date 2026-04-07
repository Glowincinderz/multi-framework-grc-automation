"""
NIST Cybersecurity Framework (CSF) 2.0 — Control Library
Published: February 2024  |  https://doi.org/10.6028/NIST.CSWP.29

Functions (Themes):
  GV  - Govern   (new in CSF 2.0)
  ID  - Identify
  PR  - Protect
  DE  - Detect
  RS  - Respond
  RC  - Recover

Each control maps to a Category (e.g., GV.OC) from the NIST CSF 2.0 Core.

SWOT Remediation — Prompt 9 (2026-04-07): added to support multi-framework.
"""

NISTCSF_CONTROLS = [
    # ─────────────────────────────────────────────────────────────────────────
    # GV — GOVERN
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "GV.OC-01", "theme": "Govern",
     "title": "Organisational Context",
     "description": "The organisational mission is understood and informs cybersecurity risk management.",
     "artifacts": ["Mission statement", "Strategic plan", "Cybersecurity strategy alignment docs"],
     "test_procedure": "Verify cybersecurity strategy aligns with organisational mission; inspect documentation."},

    {"id": "GV.RM-01", "theme": "Govern",
     "title": "Risk Management Strategy",
     "description": "Risk management objectives are established and agreed to by organisational stakeholders.",
     "artifacts": ["Risk appetite statement", "Risk management policy", "Board-approved risk framework"],
     "test_procedure": "Inspect risk management policy; verify stakeholder approval of risk objectives."},

    {"id": "GV.RM-02", "theme": "Govern",
     "title": "Risk Tolerance",
     "description": "Risk tolerance statements are established, communicated, and maintained.",
     "artifacts": ["Risk tolerance documentation", "Communication records", "Risk acceptance log"],
     "test_procedure": "Review risk tolerance statements; verify they have been communicated to stakeholders."},

    {"id": "GV.RR-01", "theme": "Govern",
     "title": "Roles and Responsibilities",
     "description": "Organisational leadership is responsible and accountable for cybersecurity risk.",
     "artifacts": ["RACI chart", "CISO appointment documentation", "Board accountability records"],
     "test_procedure": "Verify CISO role is defined; inspect board accountability for cybersecurity risk."},

    {"id": "GV.PO-01", "theme": "Govern",
     "title": "Cybersecurity Policy",
     "description": "Cybersecurity policy is established, communicated, and enforced.",
     "artifacts": ["Information Security Policy", "Policy approval records", "Communication evidence"],
     "test_procedure": "Inspect IS policy; verify approval date and distribution to all staff."},

    {"id": "GV.OV-01", "theme": "Govern",
     "title": "Cybersecurity Performance Oversight",
     "description": "Cybersecurity risk management performance is reviewed by organisational leaders.",
     "artifacts": ["Management review records", "KPI / KRI dashboards", "Risk committee minutes"],
     "test_procedure": "Sample management review records; verify cybersecurity KPIs are tracked."},

    {"id": "GV.SC-01", "theme": "Govern",
     "title": "Supply Chain Risk Management",
     "description": "A cybersecurity supply chain risk management program is established.",
     "artifacts": ["Supply chain risk policy", "Vendor risk register", "Third-party assessments"],
     "test_procedure": "Review supply chain risk policy; sample vendor risk assessments."},

    # ─────────────────────────────────────────────────────────────────────────
    # ID — IDENTIFY
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "ID.AM-01", "theme": "Identify",
     "title": "Asset Inventory — Hardware",
     "description": "Inventories of hardware managed by the organisation are maintained.",
     "artifacts": ["Hardware asset inventory", "CMDB extract", "Asset scan reports"],
     "test_procedure": "Verify CMDB is current; reconcile asset scan results against inventory."},

    {"id": "ID.AM-02", "theme": "Identify",
     "title": "Asset Inventory — Software",
     "description": "Inventories of software, services, and systems managed by the organisation are maintained.",
     "artifacts": ["Software asset inventory", "SBOM", "Shadow IT scan results"],
     "test_procedure": "Inspect software inventory; verify licensing compliance and shadow IT scans."},

    {"id": "ID.AM-05", "theme": "Identify",
     "title": "Assets are Prioritised by Criticality",
     "description": "Assets are prioritised based on classification, criticality, resources, and impact.",
     "artifacts": ["Asset classification policy", "Criticality ratings", "Business impact analysis"],
     "test_procedure": "Verify assets have criticality ratings; inspect BIA for coverage."},

    {"id": "ID.RA-01", "theme": "Identify",
     "title": "Vulnerabilities are Identified and Documented",
     "description": "Vulnerabilities in assets are identified, validated, and recorded.",
     "artifacts": ["Vulnerability scan reports", "CVE tracking register", "Pen test reports"],
     "test_procedure": "Review vulnerability scan reports; verify CVEs are tracked and remediated."},

    {"id": "ID.RA-02", "theme": "Identify",
     "title": "Cyber Threat Intelligence",
     "description": "Cyber threat intelligence is received from information sharing forums and sources.",
     "artifacts": ["Threat intel subscriptions", "ISACs membership", "Threat reports"],
     "test_procedure": "Verify threat intelligence feeds are active; inspect threat reports consumed."},

    {"id": "ID.RA-05", "theme": "Identify",
     "title": "Risk Register",
     "description": "Threats, vulnerabilities, likelihoods, and impacts are used to determine and prioritise risk.",
     "artifacts": ["Risk register", "Risk scoring methodology", "Risk treatment plans"],
     "test_procedure": "Inspect risk register completeness; verify risk scoring methodology is applied."},

    {"id": "ID.IM-01", "theme": "Identify",
     "title": "Improvements are Identified",
     "description": "Improvements are identified from cybersecurity evaluations.",
     "artifacts": ["Audit findings log", "Continuous improvement register", "Lessons-learned records"],
     "test_procedure": "Inspect audit findings log; verify improvements are tracked and implemented."},

    # ─────────────────────────────────────────────────────────────────────────
    # PR — PROTECT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PR.AA-01", "theme": "Protect",
     "title": "Identity Management and Authentication",
     "description": "Identities and credentials for authorised users, services, and hardware are managed.",
     "artifacts": ["IAM policy", "MFA evidence", "Password policy", "Service account inventory"],
     "test_procedure": "Verify MFA enforcement; inspect service account review records."},

    {"id": "PR.AA-05", "theme": "Protect",
     "title": "Access Permissions",
     "description": "Access permissions, entitlements, and authorisations are managed.",
     "artifacts": ["Access control matrix", "Privileged access review", "Least-privilege evidence"],
     "test_procedure": "Sample access reviews; verify least-privilege principle is applied."},

    {"id": "PR.AT-01", "theme": "Protect",
     "title": "Awareness and Training",
     "description": "Personnel are provided with awareness and training so they can perform cybersecurity tasks.",
     "artifacts": ["Training completion records", "Phishing simulation results", "Training programme"],
     "test_procedure": "Verify training completion rates; inspect phishing simulation results."},

    {"id": "PR.DS-01", "theme": "Protect",
     "title": "Data-at-Rest Protection",
     "description": "The confidentiality, integrity, and availability of data-at-rest are protected.",
     "artifacts": ["Encryption policy", "Disk encryption evidence", "Database encryption config"],
     "test_procedure": "Verify encryption-at-rest is enabled on storage systems and databases."},

    {"id": "PR.DS-02", "theme": "Protect",
     "title": "Data-in-Transit Protection",
     "description": "The confidentiality, integrity, and availability of data-in-transit are protected.",
     "artifacts": ["TLS configuration evidence", "Network encryption policy", "Certificate inventory"],
     "test_procedure": "Verify TLS 1.2/1.3 is enforced; inspect certificate validity and rotation."},

    {"id": "PR.PS-01", "theme": "Protect",
     "title": "Configuration Management",
     "description": "Configuration management practices are established and applied.",
     "artifacts": ["Configuration management policy", "Baseline configurations", "CIS benchmark results"],
     "test_procedure": "Verify hardening baselines are applied; inspect CIS benchmark compliance results."},

    {"id": "PR.IR-01", "theme": "Protect",
     "title": "Network Segmentation",
     "description": "Networks and environments are protected from unauthorised logical access and usage.",
     "artifacts": ["Network segmentation diagram", "Firewall rules", "VLAN configuration"],
     "test_procedure": "Inspect network architecture; verify segmentation between production and non-production."},

    # ─────────────────────────────────────────────────────────────────────────
    # DE — DETECT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "DE.CM-01", "theme": "Detect",
     "title": "Continuous Monitoring — Networks",
     "description": "Networks and network services are monitored to find potentially adverse events.",
     "artifacts": ["IDS/IPS configuration", "Network flow logs", "SIEM alert rules"],
     "test_procedure": "Verify IDS/IPS is active; inspect SIEM rules coverage for network threats."},

    {"id": "DE.CM-03", "theme": "Detect",
     "title": "Continuous Monitoring — Personnel",
     "description": "Personnel activity and technology usage are monitored to find potentially adverse events.",
     "artifacts": ["User activity monitoring policy", "UEBA configuration", "Audit log reviews"],
     "test_procedure": "Verify user activity monitoring is enabled; inspect audit log review records."},

    {"id": "DE.CM-06", "theme": "Detect",
     "title": "External Service Provider Activities Monitoring",
     "description": "External service provider activities and services are monitored.",
     "artifacts": ["Third-party monitoring procedures", "Service provider reports", "SLA monitoring data"],
     "test_procedure": "Verify third-party monitoring procedures; inspect service provider reports."},

    {"id": "DE.AE-02", "theme": "Detect",
     "title": "Potentially Adverse Events are Analysed",
     "description": "Potentially adverse events are analysed to better understand associated activities.",
     "artifacts": ["Security event analysis records", "Threat hunting logs", "Correlation rules"],
     "test_procedure": "Sample security events; verify analysis and correlation procedures are followed."},

    # ─────────────────────────────────────────────────────────────────────────
    # RS — RESPOND
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "RS.MA-01", "theme": "Respond",
     "title": "Incident Response Plan",
     "description": "The incident response plan is executed in coordination with relevant third parties.",
     "artifacts": ["Incident Response Plan", "Contact list", "RACI for incidents"],
     "test_procedure": "Inspect IRP; verify contact lists are current; review tabletop exercise."},

    {"id": "RS.AN-03", "theme": "Respond",
     "title": "Root Cause Analysis",
     "description": "Root cause analysis is performed during incident analysis.",
     "artifacts": ["Post-incident review reports", "Root cause analysis records", "5-Why documentation"],
     "test_procedure": "Sample post-incident reports; verify root cause analysis is documented."},

    {"id": "RS.CO-02", "theme": "Respond",
     "title": "Internal and External Reporting",
     "description": "Internal and external stakeholders are notified of incidents.",
     "artifacts": ["Breach notification records", "Regulatory reporting evidence", "Communication logs"],
     "test_procedure": "Verify notification procedures; inspect any regulatory reporting records."},

    {"id": "RS.MI-01", "theme": "Respond",
     "title": "Containment",
     "description": "Incidents are contained.",
     "artifacts": ["Containment procedures", "Incident containment records", "IR playbooks"],
     "test_procedure": "Review containment procedures; sample incident records for containment evidence."},

    # ─────────────────────────────────────────────────────────────────────────
    # RC — RECOVER
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "RC.RP-01", "theme": "Recover",
     "title": "Recovery Plan Execution",
     "description": "The recovery portion of the incident response plan is executed once initiated.",
     "artifacts": ["Recovery Plan", "BCP", "DR test results", "RTO/RPO targets"],
     "test_procedure": "Review recovery plan; verify DR tests demonstrate RTO/RPO achievement."},

    {"id": "RC.CO-03", "theme": "Recover",
     "title": "Recovery Communication",
     "description": "Recovery activities are communicated to internal and external stakeholders.",
     "artifacts": ["Recovery communication plan", "Stakeholder notification records"],
     "test_procedure": "Inspect recovery communication plan; verify stakeholder notifications are logged."},
]
