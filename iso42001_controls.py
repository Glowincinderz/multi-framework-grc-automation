"""
ISO/IEC 42001:2023 — AI Management System (AIMS) Control Library
Published: December 2023  |  https://www.iso.org/standard/81230.html

ISO 42001 is the world's first international standard for Artificial Intelligence
Management Systems. It provides a framework for organisations to responsibly develop,
provide, or use AI-based products and services.

Structure mirrors ISO 27001's Annex A approach:
  Clause 4   — Context of the Organisation
  Clause 5   — Leadership
  Clause 6   — Planning
  Clause 7   — Support
  Clause 8   — Operation
  Clause 9   — Performance Evaluation
  Clause 10  — Improvement
  Annex A    — Organisational Controls for AI
  Annex B    — Controls for AI System Impact Assessment

Themes used in this library:
  Organisational  — Leadership, governance, and policy (Clauses 4–5, Annex A)
  Planning        — Risk, objectives, and impact assessment (Clause 6, Annex B)
  Support         — Resources, competence, awareness, and communication (Clause 7)
  Operation       — AI system lifecycle management (Clause 8)
  Evaluation      — Monitoring, audit, and management review (Clause 9)
  Improvement     — Nonconformity, corrective action, continual improvement (Clause 10)

Added: SWOT Remediation — Prompt 9 extension (2026-04-07).
"""

STANDARD_VERSION        = "ISO/IEC 42001:2023"
STANDARD_PUBLISHED_DATE = "2023-12-18"
LIBRARY_LAST_REVIEWED   = "2026-04-07"
CONTROL_COUNT_EXPECTED  = 38

ISO42001_CONTROLS = [
    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 4 — CONTEXT OF THE ORGANISATION
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.4.1", "theme": "Organisational",
     "title": "Understanding the Organisation and Its Context",
     "description": "The organisation shall determine external and internal issues relevant to its purpose that affect its ability to achieve the intended outcomes of its AIMS.",
     "artifacts": ["AIMS context document", "Stakeholder register", "AI use-case inventory"],
     "test_procedure": "Inspect context document; verify AI use-cases are mapped to organisational objectives."},

    {"id": "42001.4.2", "theme": "Organisational",
     "title": "Understanding Needs and Expectations of Interested Parties",
     "description": "The organisation shall determine the interested parties relevant to the AIMS and their relevant requirements.",
     "artifacts": ["Stakeholder analysis", "Regulatory requirements register", "Customer AI commitments"],
     "test_procedure": "Verify stakeholder register is maintained; review regulatory AI requirements mapping."},

    {"id": "42001.4.3", "theme": "Organisational",
     "title": "Determining the Scope of the AIMS",
     "description": "The organisation shall determine the boundaries and applicability of the AIMS.",
     "artifacts": ["AIMS scope statement", "AI system boundaries documentation", "Exclusion justifications"],
     "test_procedure": "Inspect scope statement; verify in-scope AI systems are listed and boundaries justified."},

    {"id": "42001.4.4", "theme": "Organisational",
     "title": "AI Management System",
     "description": "The organisation shall establish, implement, maintain, and continually improve an AIMS.",
     "artifacts": ["AIMS framework documentation", "AIMS implementation plan", "Continual improvement log"],
     "test_procedure": "Verify AIMS is formally established; inspect implementation evidence and improvement records."},

    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 5 — LEADERSHIP
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.5.1", "theme": "Organisational",
     "title": "Leadership and Commitment",
     "description": "Top management shall demonstrate leadership and commitment to the AIMS.",
     "artifacts": ["AI policy signed by leadership", "Board AI oversight minutes", "AI governance charter"],
     "test_procedure": "Verify AI policy is signed by top management; inspect board-level AI oversight records."},

    {"id": "42001.5.2", "theme": "Organisational",
     "title": "AI Policy",
     "description": "Top management shall establish an AI policy appropriate to the organisation's purpose.",
     "artifacts": ["AI Policy document", "Policy approval record", "Policy communication evidence"],
     "test_procedure": "Inspect AI policy; verify it covers responsible AI principles and is communicated to all staff."},

    {"id": "42001.5.3", "theme": "Organisational",
     "title": "Organisational Roles, Responsibilities, and Authorities",
     "description": "Top management shall assign and communicate roles, responsibilities, and authorities for the AIMS.",
     "artifacts": ["RACI chart for AI governance", "AI governance committee terms of reference", "Role descriptions"],
     "test_procedure": "Verify AI governance roles are assigned; inspect RACI and committee charter."},

    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 6 — PLANNING
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.6.1", "theme": "Planning",
     "title": "Actions to Address Risks and Opportunities",
     "description": "The organisation shall determine risks and opportunities that need to be addressed for the AIMS.",
     "artifacts": ["AI risk register", "Risk treatment plan", "Opportunity log"],
     "test_procedure": "Inspect AI risk register; verify risks are rated and treatment plans are implemented."},

    {"id": "42001.6.1.2", "theme": "Planning",
     "title": "AI Risk Assessment",
     "description": "The organisation shall define and apply an AI risk assessment process.",
     "artifacts": ["AI risk assessment methodology", "Risk assessment reports per AI system", "Residual risk acceptances"],
     "test_procedure": "Verify risk assessments are conducted for each in-scope AI system; inspect methodology."},

    {"id": "42001.6.1.3", "theme": "Planning",
     "title": "AI Risk Treatment",
     "description": "The organisation shall define and apply an AI risk treatment process.",
     "artifacts": ["Risk treatment options documentation", "Statement of Applicability (SoA)", "Treatment implementation evidence"],
     "test_procedure": "Inspect AI SoA; verify selected controls are implemented and residual risk accepted."},

    {"id": "42001.6.2", "theme": "Planning",
     "title": "AI Objectives and Planning",
     "description": "The organisation shall establish AI objectives at relevant functions and levels.",
     "artifacts": ["AI objectives register", "KPI/KRI for AI", "Objectives review records"],
     "test_procedure": "Verify AI objectives are documented, measurable, and reviewed periodically."},

    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 7 — SUPPORT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.7.1", "theme": "Support",
     "title": "Resources",
     "description": "The organisation shall determine and provide resources needed for the AIMS.",
     "artifacts": ["AIMS resource plan", "Budget allocation for AI governance", "Tool and infrastructure inventory"],
     "test_procedure": "Verify resource plan is approved; inspect budget allocation and tooling."},

    {"id": "42001.7.2", "theme": "Support",
     "title": "Competence",
     "description": "The organisation shall determine the necessary competence for AI roles and take action to ensure competence.",
     "artifacts": ["AI competency framework", "Training completion records", "Skills gap analysis"],
     "test_procedure": "Inspect competency framework; verify AI practitioners have completed required training."},

    {"id": "42001.7.3", "theme": "Support",
     "title": "Awareness",
     "description": "All personnel shall be aware of the AI policy, their contribution to the AIMS, and implications of not conforming.",
     "artifacts": ["AI awareness training records", "Communications log", "Induction materials"],
     "test_procedure": "Verify all staff complete AI awareness training; inspect communication records."},

    {"id": "42001.7.4", "theme": "Support",
     "title": "Communication",
     "description": "The organisation shall determine what, when, with whom, and how to communicate regarding the AIMS.",
     "artifacts": ["AI communication plan", "Internal/external communication records", "Disclosure register"],
     "test_procedure": "Inspect communication plan; verify stakeholder communications are documented."},

    {"id": "42001.7.5", "theme": "Support",
     "title": "Documented Information",
     "description": "The AIMS shall include documented information required by this standard and deemed necessary by the organisation.",
     "artifacts": ["AIMS document register", "Document control procedure", "Records retention schedule"],
     "test_procedure": "Verify AIMS documentation is controlled; inspect version history and review records."},

    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 8 — OPERATION
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.8.1", "theme": "Operation",
     "title": "Operational Planning and Control",
     "description": "The organisation shall plan, implement, control, and maintain processes for the AIMS.",
     "artifacts": ["AI operational procedures", "Process controls documentation", "Change management records"],
     "test_procedure": "Inspect operational procedures; verify process controls are documented and followed."},

    {"id": "42001.8.2", "theme": "Operation",
     "title": "AI Risk Assessment — Operational",
     "description": "The organisation shall perform AI risk assessments at planned intervals or when significant changes occur.",
     "artifacts": ["Periodic AI risk assessment records", "Trigger log for reassessments", "Change-triggered assessment evidence"],
     "test_procedure": "Verify risk assessments are performed at least annually and after significant AI changes."},

    {"id": "42001.8.3", "theme": "Operation",
     "title": "AI Risk Treatment — Operational",
     "description": "The organisation shall implement the AI risk treatment plan.",
     "artifacts": ["Risk treatment implementation evidence", "Control effectiveness records", "Residual risk register"],
     "test_procedure": "Inspect risk treatment evidence; verify controls are operating effectively."},

    {"id": "42001.8.4", "theme": "Operation",
     "title": "AI System Impact Assessment",
     "description": "The organisation shall conduct an impact assessment for AI systems addressing potential harms.",
     "artifacts": ["AI Impact Assessment reports", "Bias and fairness evaluation", "Harm mitigation plans"],
     "test_procedure": "Verify AI impact assessments exist for all in-scope systems; inspect harm mitigation plans."},

    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 9 — PERFORMANCE EVALUATION
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.9.1", "theme": "Evaluation",
     "title": "Monitoring, Measurement, Analysis, and Evaluation",
     "description": "The organisation shall evaluate the AI performance and effectiveness of the AIMS.",
     "artifacts": ["AI KPI dashboard", "Monitoring reports", "Model performance metrics"],
     "test_procedure": "Inspect AI monitoring dashboards; verify performance metrics are tracked against targets."},

    {"id": "42001.9.2", "theme": "Evaluation",
     "title": "Internal Audit",
     "description": "The organisation shall conduct internal audits at planned intervals to confirm AIMS conformance.",
     "artifacts": ["Internal audit programme", "Audit reports", "Audit findings and corrective actions"],
     "test_procedure": "Verify internal audit schedule; inspect most recent AIMS audit report and findings."},

    {"id": "42001.9.3", "theme": "Evaluation",
     "title": "Management Review",
     "description": "Top management shall review the AIMS at planned intervals.",
     "artifacts": ["Management review agenda and minutes", "AIMS performance summary", "Improvement decisions log"],
     "test_procedure": "Inspect management review records; verify AI KPIs and improvement actions were discussed."},

    # ─────────────────────────────────────────────────────────────────────────
    # CLAUSE 10 — IMPROVEMENT
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.10.1", "theme": "Improvement",
     "title": "Continual Improvement",
     "description": "The organisation shall continually improve the suitability, adequacy, and effectiveness of the AIMS.",
     "artifacts": ["Continual improvement register", "Improvement initiative records", "Lessons-learned log"],
     "test_procedure": "Inspect improvement register; verify improvements are tracked, prioritised, and implemented."},

    {"id": "42001.10.2", "theme": "Improvement",
     "title": "Nonconformity and Corrective Action",
     "description": "When nonconformities occur, the organisation shall react, determine root cause, and implement corrective actions.",
     "artifacts": ["Nonconformity register", "Root cause analysis records", "Corrective action closure evidence"],
     "test_procedure": "Sample nonconformity records; verify root cause analysis and corrective actions are documented."},

    # ─────────────────────────────────────────────────────────────────────────
    # ANNEX A — ORGANISATIONAL CONTROLS FOR AI SYSTEMS
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.A.2.2", "theme": "Organisational",
     "title": "AI Roles and Responsibilities",
     "description": "Define and document roles and responsibilities related to AI development, deployment, and use.",
     "artifacts": ["AI governance RACI", "Role-specific AI accountability documentation"],
     "test_procedure": "Verify AI roles are defined; inspect accountability documentation for each AI system."},

    {"id": "42001.A.2.3", "theme": "Organisational",
     "title": "Responsible AI Resources",
     "description": "The organisation shall ensure resources are available to support responsible AI practices.",
     "artifacts": ["Responsible AI team documentation", "Ethics board charter", "External expertise engagement records"],
     "test_procedure": "Verify responsible AI function exists; inspect resources allocated to ethics and fairness."},

    {"id": "42001.A.2.4", "theme": "Organisational",
     "title": "AI System Lifecycle",
     "description": "Policies shall define responsibilities for each phase of the AI system lifecycle.",
     "artifacts": ["AI lifecycle policy", "Lifecycle stage gate documentation", "Decommission procedures"],
     "test_procedure": "Inspect AI lifecycle policy; verify stage gate approvals exist for in-scope systems."},

    {"id": "42001.A.2.5", "theme": "Organisational",
     "title": "AI Supplier Relationships",
     "description": "The organisation shall manage AI-specific risks from suppliers and third-party AI systems.",
     "artifacts": ["AI supplier register", "Third-party AI risk assessments", "Vendor AI contractual clauses"],
     "test_procedure": "Sample AI supplier assessments; verify AI-specific contractual requirements are in place."},

    {"id": "42001.A.2.6", "theme": "Organisational",
     "title": "AI System Impact Assessment — Annex A",
     "description": "Before deploying an AI system, assess potential impacts on individuals and society.",
     "artifacts": ["Pre-deployment impact assessment", "Fairness and bias testing results", "Deployment approval records"],
     "test_procedure": "Verify pre-deployment impact assessments are completed; inspect fairness testing evidence."},

    {"id": "42001.A.3.2", "theme": "Organisational",
     "title": "Data Governance for AI",
     "description": "The organisation shall establish governance over data used in AI systems.",
     "artifacts": ["AI data governance policy", "Training data inventory", "Data lineage documentation"],
     "test_procedure": "Inspect AI data governance policy; verify training data is inventoried and documented."},

    {"id": "42001.A.3.3", "theme": "Organisational",
     "title": "Data Acquisition and Preparation",
     "description": "Processes for data acquisition and preparation shall ensure data quality, representativeness, and compliance.",
     "artifacts": ["Data acquisition procedures", "Data quality reports", "Bias assessment of training data"],
     "test_procedure": "Review data quality reports; verify training data is tested for representativeness and bias."},

    {"id": "42001.A.4.2", "theme": "Organisational",
     "title": "AI System Documentation",
     "description": "The organisation shall document AI systems to support transparency, auditability, and oversight.",
     "artifacts": ["AI system cards / model cards", "Algorithm documentation", "Training and validation reports"],
     "test_procedure": "Verify model cards exist for all in-scope AI systems; inspect algorithm documentation."},

    {"id": "42001.A.5.2", "theme": "Organisational",
     "title": "AI System Access Controls",
     "description": "Access to AI systems, training data, and model artefacts shall be appropriately controlled.",
     "artifacts": ["AI system access control policy", "Access review records", "Model repository access logs"],
     "test_procedure": "Verify least-privilege access to AI systems; inspect model repository access controls."},

    {"id": "42001.A.6.1", "theme": "Organisational",
     "title": "Addressing AI-Specific Security",
     "description": "The organisation shall address AI-specific security threats including adversarial attacks and model poisoning.",
     "artifacts": ["AI security threat assessment", "Adversarial robustness testing results", "Model integrity controls"],
     "test_procedure": "Verify AI-specific threat model exists; inspect adversarial robustness testing evidence."},

    # ─────────────────────────────────────────────────────────────────────────
    # ANNEX B — AI SYSTEM IMPACT ASSESSMENT CONTROLS
    # ─────────────────────────────────────────────────────────────────────────
    {"id": "42001.B.1", "theme": "Planning",
     "title": "AI Impact Assessment — Scope and Objectives",
     "description": "Define the scope, objectives, and methodology for the AI impact assessment.",
     "artifacts": ["Impact assessment scope document", "Assessment methodology", "Stakeholder list for assessment"],
     "test_procedure": "Verify impact assessment scope is defined; inspect methodology documentation."},

    {"id": "42001.B.2", "theme": "Planning",
     "title": "AI Impact Assessment — Identification of Impacts",
     "description": "Identify potential positive and negative impacts of the AI system on individuals, groups, and society.",
     "artifacts": ["Impact catalogue", "Affected party analysis", "Societal impact review"],
     "test_procedure": "Inspect impact catalogue; verify all affected parties are identified and impacts assessed."},

    {"id": "42001.B.3", "theme": "Planning",
     "title": "AI Impact Assessment — Evaluation and Mitigation",
     "description": "Evaluate identified impacts and implement mitigating controls.",
     "artifacts": ["Impact risk ratings", "Mitigation measures documentation", "Residual impact acceptance"],
     "test_procedure": "Verify impacts are rated and mitigations are implemented; inspect residual impact acceptance."},

    {"id": "42001.B.4", "theme": "Planning",
     "title": "AI Impact Assessment — Monitoring and Review",
     "description": "Monitor AI system impacts in operation and review the impact assessment at defined intervals.",
     "artifacts": ["Operational impact monitoring records", "Periodic assessment review", "Incident-triggered reassessment evidence"],
     "test_procedure": "Verify operational impact monitoring is in place; inspect periodic reassessment records."},
]
