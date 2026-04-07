"""
PCI DSS v4.0 — Control Library
Published: March 2022  |  https://www.pcisecuritystandards.org/

Themes map to the 12 PCI DSS Requirements (principal domains).
Each control maps to a top-level or second-level Requirement.

SWOT Remediation — Prompt 9 (2026-04-07): added to support multi-framework.
"""

PCIDSS_CONTROLS = [
    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 1 — Install and Maintain Network Security Controls
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.1.1", "theme": "Network Security",
     "title": "Processes for Managing Network Security Controls",
     "description": "Processes and mechanisms for installing and maintaining network security controls are defined and understood.",
     "artifacts": ["Firewall policy", "Network security standard", "NSC management procedures"],
     "test_procedure": "Inspect firewall policy; verify management procedures are documented and reviewed."},

    {"id": "PCI.1.2", "theme": "Network Security",
     "title": "Network Security Controls Configured and Maintained",
     "description": "Network security controls (NSCs) are configured and maintained.",
     "artifacts": ["Firewall configuration", "Rule review records", "Network diagram"],
     "test_procedure": "Review firewall rules; verify rule review is performed at least every 6 months."},

    {"id": "PCI.1.3", "theme": "Network Security",
     "title": "Network Access to and from the Cardholder Data Environment",
     "description": "Network access to and from the cardholder data environment (CDE) is restricted.",
     "artifacts": ["CDE network diagram", "Inbound/outbound rule documentation", "Penetration test report"],
     "test_procedure": "Verify CDE is segmented; inspect firewall rules restricting access to CDE."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 2 — Apply Secure Configurations to All System Components
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.2.1", "theme": "Secure Configuration",
     "title": "Processes for Managing Secure Configurations",
     "description": "Processes and mechanisms for applying secure configurations are defined and understood.",
     "artifacts": ["Hardening standards", "Configuration management policy", "Baseline security config"],
     "test_procedure": "Verify hardening baselines exist; inspect baseline deviation tracking."},

    {"id": "PCI.2.2", "theme": "Secure Configuration",
     "title": "System Components are Configured and Managed Securely",
     "description": "System components are configured and managed securely.",
     "artifacts": ["CIS benchmark results", "Vulnerability scan reports", "Config audit reports"],
     "test_procedure": "Sample system configurations; verify alignment to hardening baselines."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 3 — Protect Stored Account Data
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.3.2", "theme": "Data Protection",
     "title": "Storage of Account Data is Kept to a Minimum",
     "description": "Storage of account data is kept to a minimum.",
     "artifacts": ["Data retention policy", "Data flow diagram", "Data discovery scan results"],
     "test_procedure": "Verify retention policy limits CHD storage; inspect data discovery scans."},

    {"id": "PCI.3.3", "theme": "Data Protection",
     "title": "Sensitive Authentication Data Not Retained After Authorisation",
     "description": "Sensitive authentication data (SAD) is not retained after authorisation.",
     "artifacts": ["SAD handling procedures", "Application security review", "Tokenisation evidence"],
     "test_procedure": "Verify SAD is not stored post-authorisation; inspect application data storage."},

    {"id": "PCI.3.5", "theme": "Data Protection",
     "title": "Primary Account Number (PAN) is Secured",
     "description": "The primary account number (PAN) is secured wherever it is stored.",
     "artifacts": ["PAN encryption evidence", "Tokenisation records", "Masking configuration"],
     "test_procedure": "Verify PAN is masked/tokenised; inspect encryption key management."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 4 — Protect Cardholder Data with Strong Cryptography in Transit
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.4.1", "theme": "Cryptography",
     "title": "Processes for Protecting Cardholder Data with Cryptography",
     "description": "Processes and mechanisms for protecting cardholder data with cryptography during transmission are defined.",
     "artifacts": ["Cryptography policy", "TLS configuration", "Certificate inventory"],
     "test_procedure": "Verify TLS 1.2+ is enforced; inspect certificate management procedures."},

    {"id": "PCI.4.2", "theme": "Cryptography",
     "title": "PAN is Protected During Transmission",
     "description": "PAN is protected with strong cryptography during transmission over open, public networks.",
     "artifacts": ["TLS scan results", "End-to-end encryption evidence", "Network traffic analysis"],
     "test_procedure": "Perform TLS scan; verify no unencrypted PAN transmission over public networks."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 5 — Protect All Systems and Networks from Malicious Software
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.5.2", "theme": "Malware Protection",
     "title": "Malware is Addressed",
     "description": "Malware attacks are prevented, or their impacts are detected and addressed.",
     "artifacts": ["Anti-malware deployment evidence", "EDR coverage report", "Scan frequency records"],
     "test_procedure": "Verify anti-malware is deployed on all in-scope systems; inspect scan logs."},

    {"id": "PCI.5.3", "theme": "Malware Protection",
     "title": "Anti-Malware Mechanisms and Processes are Active",
     "description": "Anti-malware mechanisms and processes are active, maintained, and monitored.",
     "artifacts": ["Anti-malware update logs", "Alert response records", "Definition currency evidence"],
     "test_procedure": "Verify malware definitions are current; inspect alert response procedures."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 6 — Develop and Maintain Secure Systems and Software
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.6.2", "theme": "Secure Development",
     "title": "Bespoke and Custom Software are Developed Securely",
     "description": "Bespoke and custom software are developed securely.",
     "artifacts": ["Secure SDLC policy", "Code review records", "SAST/DAST results"],
     "test_procedure": "Inspect secure SDLC policy; sample code review and SAST/DAST records."},

    {"id": "PCI.6.3", "theme": "Secure Development",
     "title": "Security Vulnerabilities are Identified and Addressed",
     "description": "Security vulnerabilities in bespoke and custom software are identified and remediated.",
     "artifacts": ["Vulnerability tracking log", "Patch records", "Pen test findings and remediation"],
     "test_procedure": "Review vulnerability tracking; verify critical vulnerabilities are remediated within SLA."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 7 — Restrict Access to System Components and Cardholder Data
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.7.2", "theme": "Access Control",
     "title": "Access to System Components and Data is Appropriately Defined and Assigned",
     "description": "Access to system components and data is appropriately defined and assigned.",
     "artifacts": ["Access control policy", "Role definitions", "Access provisioning records"],
     "test_procedure": "Verify access control policy; sample access provisioning records for approval."},

    {"id": "PCI.7.3", "theme": "Access Control",
     "title": "All User IDs and Related Access Privileges are Managed",
     "description": "All user accounts and related access privileges, including third-party/vendor accounts, are reviewed.",
     "artifacts": ["Periodic access review results", "Third-party account list", "Privileged account log"],
     "test_procedure": "Inspect access review results; verify third-party accounts are reviewed quarterly."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 8 — Identify Users and Authenticate Access to System Components
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.8.2", "theme": "Authentication",
     "title": "All Users are Assigned a Unique ID",
     "description": "All users are assigned and use a unique ID before allowing them to access system components.",
     "artifacts": ["Account provisioning records", "Shared account exception log", "ID policy"],
     "test_procedure": "Verify no shared accounts exist in CDE; inspect unique ID policy compliance."},

    {"id": "PCI.8.3", "theme": "Authentication",
     "title": "User Authentication is Managed via an Authentication Policy",
     "description": "User authentication for users and administrators is established and managed via an authentication policy.",
     "artifacts": ["Authentication policy", "MFA configuration", "Password complexity evidence"],
     "test_procedure": "Verify MFA is required for CDE access; inspect authentication policy enforcement."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 9 — Restrict Physical Access to Cardholder Data
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.9.1", "theme": "Physical Security",
     "title": "Physical Security Controls for the CDE",
     "description": "Processes and mechanisms for restricting physical access to cardholder data are defined.",
     "artifacts": ["Physical access policy", "Access control log", "CCTV records"],
     "test_procedure": "Inspect physical access controls to CDE; review badge access logs."},

    {"id": "PCI.9.4", "theme": "Physical Security",
     "title": "Media with Cardholder Data is Secured",
     "description": "Media with cardholder data is secured.",
     "artifacts": ["Media handling policy", "Media inventory", "Media destruction records"],
     "test_procedure": "Verify media is physically secured; inspect destruction certificates."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 10 — Log and Monitor All Access to System Components and CHD
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.10.2", "theme": "Logging and Monitoring",
     "title": "Audit Logs Capture All Individual Access to Cardholder Data",
     "description": "Audit logs capture all individual user access to cardholder data.",
     "artifacts": ["Audit log configuration", "Log retention policy", "Sample audit logs"],
     "test_procedure": "Verify audit logs are enabled for CDE systems; inspect log retention (12 months)."},

    {"id": "PCI.10.4", "theme": "Logging and Monitoring",
     "title": "Audit Logs are Reviewed to Identify Anomalies",
     "description": "Audit logs are reviewed to identify anomalies or suspicious activity.",
     "artifacts": ["Log review records", "SIEM alert tuning", "Anomaly investigation log"],
     "test_procedure": "Inspect log review records; verify daily reviews are performed for critical systems."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 11 — Test Security of Systems and Networks Regularly
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.11.3", "theme": "Security Testing",
     "title": "External and Internal Vulnerabilities are Regularly Tested",
     "description": "External and internal vulnerabilities are regularly identified, prioritised, and addressed.",
     "artifacts": ["Quarterly vulnerability scan reports", "Remediation tracking", "ASV scan results"],
     "test_procedure": "Verify ASV scans are performed quarterly; inspect remediation of high-risk findings."},

    {"id": "PCI.11.4", "theme": "Security Testing",
     "title": "External and Internal Penetration Testing is Regularly Performed",
     "description": "External and internal penetration testing is regularly performed.",
     "artifacts": ["Annual pen test reports", "Penetration test methodology", "Remediation evidence"],
     "test_procedure": "Verify annual pen test is conducted; inspect remediation of critical findings."},

    # ─────────────────────────────────────────────────────────────────────────
    # REQUIREMENT 12 — Support Information Security with Organisational Policies
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "PCI.12.1", "theme": "Information Security Policy",
     "title": "Comprehensive Information Security Policy",
     "description": "A comprehensive information security policy is known and current.",
     "artifacts": ["IS Policy (annual review evidence)", "Policy distribution records", "Staff acknowledgements"],
     "test_procedure": "Verify IS policy is reviewed annually; inspect distribution and acknowledgement records."},

    {"id": "PCI.12.6", "theme": "Information Security Policy",
     "title": "Security Awareness Education",
     "description": "Security awareness education is an ongoing activity.",
     "artifacts": ["Security awareness training completion", "Phishing simulation records", "Training programme"],
     "test_procedure": "Verify all staff complete annual security awareness training; inspect completion rates."},

    {"id": "PCI.12.10", "theme": "Information Security Policy",
     "title": "Suspected and Confirmed Security Incidents are Responded to Immediately",
     "description": "Suspected and confirmed security incidents that could impact the CDE are responded to immediately.",
     "artifacts": ["Incident Response Plan", "IR contact list", "Incident log"],
     "test_procedure": "Inspect IRP for CDE scope; verify incident response contacts are current."},
]
