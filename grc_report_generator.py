"""
GRC Excel Report Generator — ISO 27001:2022
Generates a multi-sheet Excel workbook with:
  1. Executive Dashboard
  2. Control Register (all 93 controls)
  3. Risk Register & Heatmap
  4. Control Test Results
  5. Audit Tracker
  6. Audit Findings & CAR Log
  7. Artifact Collection Status
  8. Drata Sync Log
"""

import os
import json
from datetime import datetime, date

try:
    import openpyxl
    from openpyxl.styles import (PatternFill, Font, Alignment, Border, Side,
                                  GradientFill)
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, PieChart, Reference
    from openpyxl.chart.series import DataPoint
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

from grc_engine import get_connection

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────

DARK_BLUE   = "1B3A6B"
MID_BLUE    = "2E6DA4"
LIGHT_BLUE  = "D6E4F0"
WHITE       = "FFFFFF"
BLACK       = "000000"
GREEN       = "27AE60"
AMBER       = "F39C12"
RED         = "E74C3C"
LIGHT_GREY  = "F2F2F2"
MID_GREY    = "BDBDBD"
DARK_GREY   = "555555"
PURPLE      = "6C3483"
TEAL        = "117A65"

STATUS_COLORS = {
    "Implemented":      GREEN,
    "In Progress":      AMBER,
    "Not Implemented":  RED,
    "Not Applicable":   MID_GREY,
    "Pass":             GREEN,
    "Fail":             RED,
    "Partial":          AMBER,
    "Not Tested":       MID_GREY,
    "Open":             RED,
    "Closed":           GREEN,
    "Planned":          MID_BLUE,
    "In Progress":      AMBER,
    "Complete":         GREEN,
    "Pending":          AMBER,
    "Collected":        GREEN,
    "Expired":          RED,
    "N/A":              MID_GREY,
    "Major":            RED,
    "Minor":            AMBER,
    "Low":              GREEN,
}

def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)

def _font(bold=False, color=BLACK, size=11, italic=False) -> Font:
    return Font(bold=bold, color=color, size=size, italic=italic)

def _center() -> Alignment:
    return Alignment(horizontal="center", vertical="center", wrap_text=True)

def _left() -> Alignment:
    return Alignment(horizontal="left", vertical="center", wrap_text=True)

def _border() -> Border:
    thin = Side(style="thin", color=MID_GREY)
    return Border(left=thin, right=thin, top=thin, bottom=thin)

def _header_row(ws, headers: list, row: int = 1, bg=DARK_BLUE, fg=WHITE,
                bold=True, size=11):
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=header)
        cell.fill = _fill(bg)
        cell.font = _font(bold=bold, color=fg, size=size)
        cell.alignment = _center()
        cell.border = _border()

def _data_cell(ws, row, col, value, bg=WHITE, fg=BLACK, bold=False,
               align="left", size=10):
    cell = ws.cell(row=row, column=col, value=value)
    cell.fill = _fill(bg)
    cell.font = _font(bold=bold, color=fg, size=size)
    cell.alignment = _left() if align == "left" else _center()
    cell.border = _border()
    return cell

def _status_cell(ws, row, col, value):
    color = STATUS_COLORS.get(value, WHITE)
    cell = _data_cell(ws, row, col, value, bg=color, fg=WHITE,
                      bold=True, align="center")
    return cell

def _set_col_widths(ws, widths: dict):
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

def _freeze(ws, cell="A2"):
    ws.freeze_panes = cell

def _section_header(ws, row, ncols, title, bg=MID_BLUE):
    ws.merge_cells(start_row=row, start_column=1,
                   end_row=row, end_column=ncols)
    cell = ws.cell(row=row, column=1, value=title)
    cell.fill = _fill(bg)
    cell.font = _font(bold=True, color=WHITE, size=12)
    cell.alignment = _center()
    cell.border = _border()


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 1 — EXECUTIVE DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

def _build_dashboard(wb, conn):
    ws = wb.create_sheet("📊 Dashboard", 0)
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 3
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 18
    ws.row_dimensions[1].height = 8

    # Title banner
    ws.merge_cells("B2:F3")
    title = ws["B2"]
    title.value = "ISO 27001:2022 — GRC Program Dashboard"
    title.fill = _fill(DARK_BLUE)
    title.font = Font(bold=True, color=WHITE, size=18)
    title.alignment = _center()

    ws.merge_cells("B4:F4")
    sub = ws["B4"]
    sub.value = f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}  |  Framework: ISO/IEC 27001:2022  |  Drata-integrated"
    sub.fill = _fill(MID_BLUE)
    sub.font = _font(color=WHITE, size=10)
    sub.alignment = _center()

    # ── Control Status KPIs ──────────────────────────────────────────────────
    ctrl_rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM controls GROUP BY status"
    ).fetchall()
    ctrl_data = {r["status"]: r["cnt"] for r in ctrl_rows}
    total_ctrl = sum(ctrl_data.values())
    implemented = ctrl_data.get("Implemented", 0)
    pct_complete = round((implemented / total_ctrl * 100), 1) if total_ctrl else 0

    kpis = [
        ("Total Controls",       total_ctrl,                         DARK_BLUE),
        ("Implemented",          implemented,                        GREEN),
        ("In Progress",          ctrl_data.get("In Progress", 0),    AMBER),
        ("Not Implemented",      ctrl_data.get("Not Implemented", 0), RED),
        ("Completion Rate",      f"{pct_complete}%",                 TEAL),
    ]

    ws.merge_cells("B6:F6")
    sec = ws["B6"]
    sec.value = "▸ Control Implementation Status"
    sec.fill = _fill(MID_BLUE)
    sec.font = _font(bold=True, color=WHITE, size=11)
    sec.alignment = _left()

    kpi_cols = ["B", "C", "D", "E", "F"]
    for idx, (label, value, color) in enumerate(kpis):
        col = kpi_cols[idx]
        ws[f"{col}7"].value = label
        ws[f"{col}7"].fill = _fill(color)
        ws[f"{col}7"].font = _font(bold=True, color=WHITE, size=10)
        ws[f"{col}7"].alignment = _center()
        ws[f"{col}7"].border = _border()

        ws[f"{col}8"].value = value
        ws[f"{col}8"].fill = _fill(LIGHT_GREY)
        ws[f"{col}8"].font = _font(bold=True, size=16)
        ws[f"{col}8"].alignment = _center()
        ws[f"{col}8"].border = _border()
        ws.row_dimensions[8].height = 36

    # ── Risk Summary ─────────────────────────────────────────────────────────
    risk_rows = conn.execute("""
        SELECT
            SUM(CASE WHEN inherent_risk >= 15 THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN inherent_risk BETWEEN 10 AND 14 THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN inherent_risk BETWEEN 6 AND 9 THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN inherent_risk < 6 THEN 1 ELSE 0 END) as low,
            COUNT(*) as total
        FROM risks
    """).fetchone()

    ws.merge_cells("B10:F10")
    ws["B10"].value = "▸ Risk Register Summary"
    ws["B10"].fill = _fill(MID_BLUE)
    ws["B10"].font = _font(bold=True, color=WHITE, size=11)
    ws["B10"].alignment = _left()

    risk_kpis = [
        ("Total Risks",   risk_rows["total"] or 0,    DARK_BLUE),
        ("Critical (≥15)", risk_rows["critical"] or 0, RED),
        ("High (10-14)",  risk_rows["high"] or 0,     AMBER),
        ("Medium (6-9)",  risk_rows["medium"] or 0,   MID_BLUE),
        ("Low (<6)",      risk_rows["low"] or 0,      GREEN),
    ]
    for idx, (label, value, color) in enumerate(risk_kpis):
        col = kpi_cols[idx]
        ws[f"{col}11"].value = label
        ws[f"{col}11"].fill = _fill(color)
        ws[f"{col}11"].font = _font(bold=True, color=WHITE, size=10)
        ws[f"{col}11"].alignment = _center()
        ws[f"{col}11"].border = _border()
        ws[f"{col}12"].value = value
        ws[f"{col}12"].fill = _fill(LIGHT_GREY)
        ws[f"{col}12"].font = _font(bold=True, size=16)
        ws[f"{col}12"].alignment = _center()
        ws[f"{col}12"].border = _border()
        ws.row_dimensions[12].height = 36

    # ── Test & Audit KPIs ────────────────────────────────────────────────────
    test_rows = conn.execute(
        "SELECT result, COUNT(*) as cnt FROM control_tests GROUP BY result"
    ).fetchall()
    test_data = {r["result"]: r["cnt"] for r in test_rows}

    findings_open = conn.execute(
        "SELECT COUNT(*) as cnt FROM audit_findings WHERE status='Open'"
    ).fetchone()["cnt"]
    findings_major = conn.execute(
        "SELECT COUNT(*) as cnt FROM audit_findings WHERE severity='Major' AND status='Open'"
    ).fetchone()["cnt"]

    artifact_total = conn.execute("SELECT COUNT(*) as cnt FROM artifacts").fetchone()["cnt"]
    artifact_collected = conn.execute(
        "SELECT COUNT(*) as cnt FROM artifacts WHERE status='Collected'"
    ).fetchone()["cnt"]
    artifact_pct = round((artifact_collected / artifact_total * 100), 1) if artifact_total else 0

    ws.merge_cells("B14:F14")
    ws["B14"].value = "▸ Testing & Audit Status"
    ws["B14"].fill = _fill(MID_BLUE)
    ws["B14"].font = _font(bold=True, color=WHITE, size=11)
    ws["B14"].alignment = _left()

    test_kpis = [
        ("Tests Pass",    test_data.get("Pass", 0),    GREEN),
        ("Tests Fail",    test_data.get("Fail", 0),    RED),
        ("Tests Partial", test_data.get("Partial", 0), AMBER),
        ("Open Findings", findings_open,               RED if findings_open > 0 else GREEN),
        ("Major NCs",     findings_major,              RED if findings_major > 0 else GREEN),
    ]
    for idx, (label, value, color) in enumerate(test_kpis):
        col = kpi_cols[idx]
        ws[f"{col}15"].value = label
        ws[f"{col}15"].fill = _fill(color)
        ws[f"{col}15"].font = _font(bold=True, color=WHITE, size=10)
        ws[f"{col}15"].alignment = _center()
        ws[f"{col}15"].border = _border()
        ws[f"{col}16"].value = value
        ws[f"{col}16"].fill = _fill(LIGHT_GREY)
        ws[f"{col}16"].font = _font(bold=True, size=16)
        ws[f"{col}16"].alignment = _center()
        ws[f"{col}16"].border = _border()
        ws.row_dimensions[16].height = 36

    # ── Artifact collection ──────────────────────────────────────────────────
    ws.merge_cells("B18:F18")
    ws["B18"].value = "▸ Evidence & Artifact Collection"
    ws["B18"].fill = _fill(MID_BLUE)
    ws["B18"].font = _font(bold=True, color=WHITE, size=11)
    ws["B18"].alignment = _left()

    art_kpis = [
        ("Total Required",  artifact_total,     DARK_BLUE),
        ("Collected",       artifact_collected, GREEN),
        ("Pending",         artifact_total - artifact_collected, AMBER),
        ("Collection %",    f"{artifact_pct}%", TEAL),
        ("Drata-imported",  conn.execute("SELECT COUNT(*) as cnt FROM artifacts WHERE collected_by='Drata (Automated)'").fetchone()["cnt"], MID_BLUE),
    ]
    for idx, (label, value, color) in enumerate(art_kpis):
        col = kpi_cols[idx]
        ws[f"{col}19"].value = label
        ws[f"{col}19"].fill = _fill(color)
        ws[f"{col}19"].font = _font(bold=True, color=WHITE, size=10)
        ws[f"{col}19"].alignment = _center()
        ws[f"{col}19"].border = _border()
        ws[f"{col}20"].value = value
        ws[f"{col}20"].fill = _fill(LIGHT_GREY)
        ws[f"{col}20"].font = _font(bold=True, size=16)
        ws[f"{col}20"].alignment = _center()
        ws[f"{col}20"].border = _border()
        ws.row_dimensions[20].height = 36

    # Footer
    ws.merge_cells("B22:F22")
    footer = ws["B22"]
    footer.value = "Auto-generated by ISO 27001 GRC Automation | Integrated with Drata"
    footer.fill = _fill(DARK_GREY)
    footer.font = _font(color=WHITE, size=9, italic=True)
    footer.alignment = _center()


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 2 — CONTROL REGISTER
# ─────────────────────────────────────────────────────────────────────────────

def _build_control_register(wb, conn):
    ws = wb.create_sheet("🛡 Control Register")
    ws.sheet_view.showGridLines = False

    headers = ["Control ID", "Theme", "Title", "Description", "Status",
               "Owner", "Implementation Date", "Last Reviewed",
               "Artifacts Required", "Test Procedure", "Notes"]
    _header_row(ws, headers)
    _freeze(ws)

    rows = conn.execute(
        "SELECT * FROM controls ORDER BY id"
    ).fetchall()

    theme_colors = {
        "Organizational": "EBF5FB",
        "People":         "EAFAF1",
        "Physical":       "FEF9E7",
        "Technological":  "F4ECF7",
    }

    for r_idx, row in enumerate(rows, 2):
        bg = theme_colors.get(row["theme"], WHITE)
        artifacts = json.loads(row["artifacts_json"] or "[]")
        cols = [
            (row["id"],                   "center"),
            (row["theme"],                "center"),
            (row["title"],                "left"),
            (row["description"],          "left"),
            (row["status"],               "center"),  # status cell
            (row["owner"] or "—",         "center"),
            (row["implementation_date"] or "—", "center"),
            (row["last_reviewed"] or "—", "center"),
            (", ".join(artifacts),         "left"),
            (row["test_procedure"],        "left"),
            (row["notes"] or "",           "left"),
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 5:  # Status column
                _status_cell(ws, r_idx, c_idx, val)
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 10, "B": 16, "C": 35, "D": 45, "E": 18,
        "F": 20, "G": 20, "H": 20, "I": 40, "J": 45, "K": 30
    })

    # Add theme legend
    legend_row = len(rows) + 3
    ws.cell(row=legend_row, column=1, value="Theme Legend:").font = _font(bold=True)
    for i, (theme, color) in enumerate(theme_colors.items(), 1):
        c = ws.cell(row=legend_row, column=i + 1, value=theme)
        c.fill = _fill(color)
        c.font = _font(size=9)
        c.alignment = _center()
        c.border = _border()


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 3 — RISK REGISTER
# ─────────────────────────────────────────────────────────────────────────────

def _build_risk_register(wb, conn):
    ws = wb.create_sheet("⚠ Risk Register")
    ws.sheet_view.showGridLines = False

    headers = ["Risk ID", "Title", "Asset", "Threat", "Vulnerability",
               "Likelihood\n(1-5)", "Impact\n(1-5)", "Inherent Risk",
               "Risk Level", "Treatment", "Treatment Notes",
               "Residual Risk", "Control IDs", "Owner", "Review Date", "Status"]
    _header_row(ws, headers)
    _freeze(ws)

    def risk_level(score):
        if score >= 15: return ("CRITICAL", RED)
        if score >= 10: return ("HIGH", AMBER)
        if score >= 6:  return ("MEDIUM", MID_BLUE)
        return ("LOW", GREEN)

    rows = conn.execute("SELECT * FROM risks ORDER BY inherent_risk DESC").fetchall()
    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        level, level_color = risk_level(row["inherent_risk"] or 0)
        ctrl_ids = ", ".join(json.loads(row["control_ids"] or "[]"))
        cols_data = [
            (row["risk_id"],          "center"),
            (row["title"],            "left"),
            (row["asset"] or "—",     "left"),
            (row["threat"] or "—",    "left"),
            (row["vulnerability"] or "—", "left"),
            (row["likelihood"],       "center"),
            (row["impact"],           "center"),
            (row["inherent_risk"],    "center"),
            (level,                   "center"),  # risk level — colored
            (row["treatment"] or "—", "center"),
            (row["treatment_notes"] or "—", "left"),
            (row["residual_risk"],    "center"),
            (ctrl_ids,                "left"),
            (row["owner"] or "—",     "center"),
            (row["review_date"] or "—", "center"),
            (row["status"] or "Open", "center"),
        ]
        for c_idx, (val, align) in enumerate(cols_data, 1):
            if c_idx == 9:  # Risk level
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.fill = _fill(level_color)
                cell.font = _font(bold=True, color=WHITE, size=10)
                cell.alignment = _center()
                cell.border = _border()
            elif c_idx == 10:  # Treatment
                treat_color = {"Accept": AMBER, "Mitigate": GREEN,
                               "Transfer": MID_BLUE, "Avoid": RED}.get(val, WHITE)
                _data_cell(ws, r_idx, c_idx, val, bg=treat_color, fg=WHITE,
                           bold=True, align="center")
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 14, "B": 30, "C": 20, "D": 22, "E": 25,
        "F": 12, "G": 10, "H": 14, "I": 12, "J": 12,
        "K": 30, "L": 14, "M": 20, "N": 18, "O": 14, "P": 12
    })


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 4 — CONTROL TEST RESULTS
# ─────────────────────────────────────────────────────────────────────────────

def _build_test_results(wb, conn):
    ws = wb.create_sheet("🧪 Control Tests")
    ws.sheet_view.showGridLines = False

    headers = ["Test ID", "Control ID", "Control Title", "Test Name",
               "Tester", "Test Date", "Test Type", "Result",
               "Finding", "Recommendation", "Next Test Date"]
    _header_row(ws, headers)
    _freeze(ws)

    rows = conn.execute("""
        SELECT t.*, c.title as ctrl_title
        FROM control_tests t
        LEFT JOIN controls c ON c.id = t.control_id
        ORDER BY t.test_date DESC
    """).fetchall()

    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        test_date = row["test_date"][:10] if row["test_date"] else "—"
        next_date  = row["next_test_date"][:10] if row["next_test_date"] else "—"
        cols = [
            (row["test_id"],        "center"),
            (row["control_id"],     "center"),
            (row["ctrl_title"] or "—", "left"),
            (row["test_name"] or "—", "left"),
            (row["tester"] or "—",  "center"),
            (test_date,             "center"),
            (row["test_type"] or "—", "center"),
            (row["result"] or "—",  "center"),  # colored
            (row["finding"] or "—", "left"),
            (row["recommendation"] or "—", "left"),
            (next_date,             "center"),
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 8:  # Result
                _status_cell(ws, r_idx, c_idx, val)
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 18, "B": 12, "C": 35, "D": 35, "E": 20,
        "F": 14, "G": 24, "H": 12, "I": 40, "J": 40, "K": 14
    })


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 5 — AUDIT TRACKER
# ─────────────────────────────────────────────────────────────────────────────

def _build_audit_tracker(wb, conn):
    ws = wb.create_sheet("📋 Audit Tracker")
    ws.sheet_view.showGridLines = False

    headers = ["Audit ID", "Type", "Name", "Auditor", "Start Date",
               "End Date", "Scope", "Lead Contact", "Status", "Report Ref", "Notes"]
    _header_row(ws, headers)
    _freeze(ws)

    rows = conn.execute("SELECT * FROM audits ORDER BY audit_start DESC").fetchall()
    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        type_colors = {"Internal": LIGHT_BLUE, "External": "FEF9E7",
                       "Surveillance": "EAFAF1", "Certification": "F4ECF7"}
        row_bg = type_colors.get(row["audit_type"], WHITE)

        cols = [
            (row["audit_id"],         "center"),
            (row["audit_type"],       "center"),
            (row["audit_name"],       "left"),
            (row["auditor"] or "—",   "center"),
            (row["audit_start"] or "—", "center"),
            (row["audit_end"] or "—", "center"),
            (row["scope"] or "—",     "left"),
            (row["lead_contact"] or "—", "center"),
            (row["status"],           "center"),  # colored
            (row["report_ref"] or "—", "center"),
            (row["notes"] or "—",     "left"),
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 9:
                _status_cell(ws, r_idx, c_idx, val)
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=row_bg, align=align)

    _set_col_widths(ws, {
        "A": 16, "B": 14, "C": 35, "D": 20, "E": 14,
        "F": 14, "G": 45, "H": 20, "I": 14, "J": 20, "K": 30
    })


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 6 — AUDIT FINDINGS & CAR LOG
# ─────────────────────────────────────────────────────────────────────────────

def _build_findings_log(wb, conn):
    ws = wb.create_sheet("🔍 Findings & CARs")
    ws.sheet_view.showGridLines = False

    headers = ["Finding ID", "Audit ID", "Audit Name", "Control ID",
               "Type", "Severity", "Title", "Description", "Root Cause",
               "Corrective Action", "CA Owner", "Due Date",
               "Status", "Closure Date", "Closure Evidence"]
    _header_row(ws, headers)
    _freeze(ws)

    rows = conn.execute("""
        SELECT f.*, a.audit_name
        FROM audit_findings f
        LEFT JOIN audits a ON a.audit_id = f.audit_id
        ORDER BY f.severity, f.due_date
    """).fetchall()

    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        cols = [
            (row["finding_id"],          "center"),
            (row["audit_id"],            "center"),
            (row["audit_name"] or "—",   "left"),
            (row["control_id"] or "—",   "center"),
            (row["finding_type"] or "—", "center"),
            (row["severity"] or "—",     "center"),  # colored
            (row["title"] or "—",        "left"),
            (row["description"] or "—",  "left"),
            (row["root_cause"] or "—",   "left"),
            (row["corrective_action"] or "—", "left"),
            (row["ca_owner"] or "—",     "center"),
            (row["due_date"] or "—",     "center"),
            (row["status"],              "center"),  # colored
            (row["closure_date"] or "—", "center"),
            (row["closure_evidence"] or "—", "left"),
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 6:  # Severity
                _status_cell(ws, r_idx, c_idx, val)
            elif c_idx == 13:  # Status
                _status_cell(ws, r_idx, c_idx, val)
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 16, "B": 14, "C": 28, "D": 12, "E": 12,
        "F": 10, "G": 35, "H": 40, "I": 35, "J": 40,
        "K": 18, "L": 14, "M": 12, "N": 14, "O": 35
    })


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 7 — ARTIFACT COLLECTION
# ─────────────────────────────────────────────────────────────────────────────

def _build_artifact_sheet(wb, conn):
    ws = wb.create_sheet("📁 Artifacts")
    ws.sheet_view.showGridLines = False

    headers = ["Artifact ID", "Control ID", "Control Title", "Artifact Name",
               "Type", "Description", "File / URL", "Collected By",
               "Collection Date", "Expiry Date", "Status", "Notes"]
    _header_row(ws, headers)
    _freeze(ws)

    rows = conn.execute("""
        SELECT a.*, c.title as ctrl_title
        FROM artifacts a
        LEFT JOIN controls c ON c.id = a.control_id
        ORDER BY a.status, a.control_id
    """).fetchall()

    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        cols = [
            (row["artifact_id"],          "center"),
            (row["control_id"] or "—",    "center"),
            (row["ctrl_title"] or "—",    "left"),
            (row["artifact_name"],        "left"),
            (row["artifact_type"] or "—", "center"),
            (row["description"] or "—",   "left"),
            (row["file_path"] or "—",     "left"),
            (row["collected_by"] or "—",  "center"),
            ((row["collected_date"] or "—")[:10], "center"),
            (row["expiry_date"] or "—",   "center"),
            (row["status"],               "center"),  # colored
            (row["notes"] or "—",         "left"),
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 11:
                _status_cell(ws, r_idx, c_idx, val)
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 18, "B": 12, "C": 30, "D": 35, "E": 14,
        "F": 35, "G": 40, "H": 20, "I": 16, "J": 14, "K": 12, "L": 25
    })


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 8 — JIRA TICKETS
# ─────────────────────────────────────────────────────────────────────────────

def _build_jira_sheet(wb, conn):
    ws = wb.create_sheet("🎫 Jira Tickets")
    ws.sheet_view.showGridLines = False

    headers = ["Ticket ID", "Jira Key", "Source Type", "Source ID",
               "Control", "Summary", "Issue Type", "Priority",
               "Status", "Assignee", "Due Date", "Jira URL",
               "Created At", "Mode"]
    _header_row(ws, headers, bg=PURPLE)
    _freeze(ws)

    try:
        rows = conn.execute("""
            SELECT * FROM jira_tickets ORDER BY created_at DESC
        """).fetchall()
    except Exception:
        rows = []

    type_icons = {"finding": "🔍", "test": "🧪", "risk": "⚠️",
                  "artifact": "📁", "monitor": "🤖"}
    priority_colors = {
        "Highest": RED, "High": AMBER, "Medium": MID_BLUE,
        "Low": GREEN, "Lowest": LIGHT_GREY
    }

    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        icon = type_icons.get(row["source_type"], "•")
        mode_label = "MOCK" if row["mock_mode"] else "LIVE"
        mode_color = MID_GREY if row["mock_mode"] else GREEN

        cols = [
            (row["ticket_id"],            "center"),
            (row["jira_key"] or "—",      "center"),
            (f"{icon} {row['source_type']}", "center"),
            (row["source_id"] or "—",     "center"),
            (row["control_id"] or "—",    "center"),
            (row["summary"] or "—",       "left"),
            (row["issue_type"] or "—",    "center"),
            (row["priority"] or "—",      "center"),   # priority coloured
            (row["status"] or "Open",     "center"),   # status coloured
            (row["assignee"] or "—",      "center"),
            (row["due_date"] or "—",      "center"),
            (row["jira_url"] or "—",      "left"),
            ((row["created_at"] or "")[:16], "center"),
            (mode_label,                  "center"),   # mode coloured
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 8:  # Priority
                p_color = priority_colors.get(val, WHITE)
                _data_cell(ws, r_idx, c_idx, val, bg=p_color,
                           fg=WHITE, bold=True, align="center")
            elif c_idx == 9:  # Status
                _status_cell(ws, r_idx, c_idx, val)
            elif c_idx == 14:  # Mode
                _data_cell(ws, r_idx, c_idx, val, bg=mode_color,
                           fg=WHITE, bold=True, align="center")
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 16, "B": 12, "C": 14, "D": 16, "E": 10,
        "F": 55, "G": 14, "H": 10, "I": 10, "J": 18,
        "K": 12, "L": 45, "M": 18, "N": 8
    })

    # Summary panel below tickets
    if rows:
        summary_row = len(rows) + 3
        ws.merge_cells(start_row=summary_row, start_column=1,
                       end_row=summary_row, end_column=4)
        ws.cell(row=summary_row, column=1, value="Ticket Summary").fill = _fill(PURPLE)
        ws.cell(row=summary_row, column=1).font = _font(bold=True, color=WHITE)
        ws.cell(row=summary_row, column=1).alignment = _center()

        counts = {}
        for row in rows:
            counts[row["source_type"]] = counts.get(row["source_type"], 0) + 1

        for i, (stype, cnt) in enumerate(counts.items()):
            r = summary_row + 1 + i
            ws.cell(row=r, column=1, value=f"{type_icons.get(stype,'')} {stype.title()}").font = _font(bold=True)
            ws.cell(row=r, column=2, value=cnt).font = _font(bold=True, size=14)


# ─────────────────────────────────────────────────────────────────────────────
# SHEET 9 — DRATA SYNC LOG
# ─────────────────────────────────────────────────────────────────────────────

def _build_drata_log(wb, conn):
    ws = wb.create_sheet("🔄 Drata Sync Log")
    ws.sheet_view.showGridLines = False

    headers = ["Sync ID", "Sync Type", "Synced At", "Records Synced",
               "Status", "Summary"]
    _header_row(ws, headers)
    _freeze(ws)

    rows = conn.execute(
        "SELECT * FROM drata_sync_log ORDER BY synced_at DESC"
    ).fetchall()

    for r_idx, row in enumerate(rows, 2):
        bg = LIGHT_GREY if r_idx % 2 == 0 else WHITE
        status_color = GREEN if "Success" in (row["status"] or "") else RED
        cols = [
            (row["sync_id"],             "center"),
            (row["sync_type"],           "center"),
            ((row["synced_at"] or "")[:19], "center"),
            (row["records_synced"] or 0, "center"),
            (row["status"] or "—",       "center"),
            (row["response_summary"] or "—", "left"),
        ]
        for c_idx, (val, align) in enumerate(cols, 1):
            if c_idx == 5:
                cell = _data_cell(ws, r_idx, c_idx, val, bg=status_color,
                                  fg=WHITE, bold=True, align="center")
            else:
                _data_cell(ws, r_idx, c_idx, val, bg=bg, align=align)

    _set_col_widths(ws, {
        "A": 20, "B": 18, "C": 22, "D": 16, "E": 20, "F": 60
    })


# ─────────────────────────────────────────────────────────────────────────────
# MAIN REPORT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(output_path: str):
    """Generate the full GRC Excel workbook."""
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl is required: pip install openpyxl")

    print("\n[Report] Generating ISO 27001 GRC Report...")
    conn = get_connection()

    wb = openpyxl.Workbook()
    # Remove default sheet
    if "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    _build_dashboard(wb, conn)
    print("[Report] ✓ Dashboard")
    _build_control_register(wb, conn)
    print("[Report] ✓ Control Register")
    _build_risk_register(wb, conn)
    print("[Report] ✓ Risk Register")
    _build_test_results(wb, conn)
    print("[Report] ✓ Control Test Results")
    _build_audit_tracker(wb, conn)
    print("[Report] ✓ Audit Tracker")
    _build_findings_log(wb, conn)
    print("[Report] ✓ Findings & CARs")
    _build_artifact_sheet(wb, conn)
    print("[Report] ✓ Artifact Collection")
    _build_jira_sheet(wb, conn)
    print("[Report] ✓ Jira Tickets")
    _build_drata_log(wb, conn)
    print("[Report] ✓ Drata Sync Log")

    conn.close()
    wb.save(output_path)
    print(f"\n[Report] ✅ Report saved to: {output_path}")
    return output_path
