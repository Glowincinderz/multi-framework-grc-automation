"""
GRC as Code: vendor risk, security intake and risk register checks.

Everything this module reads lives in Git as YAML under grc_as_code/:
  questionnaire.yaml        security questionnaire with red-flag rules
  vendors/*.yaml            one file per vendor (tiering inputs, answers, attestations)
  intake_example.yaml       security intake request template
  risk_register.yaml        risk register with an appetite threshold

Commands:
  python vendor_risk.py validate                 check every YAML file (used in CI)
  python vendor_risk.py tier                     tier every vendor and show its next review date
  python vendor_risk.py assess <vendor-file>     red flags + Markdown risk memo
  python vendor_risk.py assess <file> --ai       draft the memo summary with Claude (needs ANTHROPIC_API_KEY)
  python vendor_risk.py intake <intake-file>     score a security intake request
  python vendor_risk.py register                 risks above appetite or overdue for review
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent / "grc_as_code"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"

DATA_SCORE = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
ACCESS_SCORE = {"none": 0, "read": 1, "write": 2, "admin": 3, "network": 3}
CRITICALITY_SCORE = {"low": 0, "medium": 1, "high": 2}
REVIEW_MONTHS = {1: 12, 2: 24, 3: 36}
ATTESTATION_MAX_AGE_DAYS = 365
VENDOR_REQUIRED = [
    "name", "category", "business_owner", "data_classification", "access_level",
    "business_criticality", "processes_data_with_ai", "attestations", "contract",
    "answers", "last_reviewed",
]
INTAKE_REQUIRED = [
    "request_id", "title", "type", "requested_by", "data_classification",
    "internet_facing", "handles_personal_data", "uses_ai",
]
AI_AUTONOMY_SCORE = {"none": 0, "suggest_only": 1, "acts_with_approval": 2, "acts_autonomously": 3}


# --- Loading ---

def load_yaml(path: Path | str) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a YAML mapping at the top level")
    return data


def load_questionnaire(base: Path = BASE_DIR) -> dict:
    return {q["id"]: q for q in load_yaml(base / "questionnaire.yaml")["questions"]}


def vendor_files(base: Path = BASE_DIR) -> list[Path]:
    return sorted((base / "vendors").glob("*.yaml"))


# --- Vendor tiering and red flags ---

@dataclass
class Assessment:
    vendor: str
    tier: int
    score: int
    next_review: date
    red_flags: list = field(default_factory=list)

    @property
    def overdue(self) -> bool:
        return self.next_review < date.today()


def vendor_score(vendor: dict) -> int:
    """Inherent risk score from data sensitivity, access, criticality and AI use (0-9)."""
    score = (DATA_SCORE[vendor["data_classification"]]
             + ACCESS_SCORE[vendor["access_level"]]
             + CRITICALITY_SCORE[vendor["business_criticality"]])
    if vendor.get("processes_data_with_ai"):
        score += 1
    return score


def tier_for_score(score: int) -> int:
    """Tier 1 = highest risk (full review, annual), Tier 3 = lowest."""
    if score >= 6:
        return 1
    if score >= 3:
        return 2
    return 3


def add_months(d: date, months: int) -> date:
    year = d.year + (d.month - 1 + months) // 12
    month = (d.month - 1 + months) % 12 + 1
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def red_flags(vendor: dict, questionnaire: dict, tier: int, as_of: date | None = None) -> list[dict]:
    """Return a list of {id, severity, detail} red flags for one vendor."""
    as_of = as_of or date.today()
    flags = []
    answers = vendor.get("answers", {})

    for qid, q in questionnaire.items():
        applies = q.get("applies_to")
        if applies and vendor["category"] not in applies:
            continue
        if qid not in answers:
            if tier == 1:
                flags.append({"id": qid, "severity": "medium",
                              "detail": f"No answer recorded: {q['question']}"})
            continue
        if answers[qid] == q["red_flag_if"]:
            answer = "Yes" if answers[qid] else "No"
            flags.append({"id": qid, "severity": q["severity"],
                          "detail": f"Answered {answer}: {q['question']}"})

    attestations = vendor.get("attestations") or []
    if tier == 1 and not attestations:
        flags.append({"id": "ATT-00", "severity": "high",
                      "detail": "Tier 1 vendor has no SOC 2 or ISO 27001 report on file"})
    for att in attestations:
        age = (as_of - att["period_end"]).days
        if age > ATTESTATION_MAX_AGE_DAYS:
            flags.append({"id": "ATT-01", "severity": "medium",
                          "detail": f"{att['type']} report period ended {att['period_end']} "
                                    f"({age} days ago); request a current report or bridge letter"})

    contract = vendor.get("contract", {})
    if DATA_SCORE[vendor["data_classification"]] >= 2 and not contract.get("dpa_signed"):
        flags.append({"id": "CON-01", "severity": "high",
                      "detail": "Confidential or restricted data without a signed DPA"})
    if vendor.get("processes_data_with_ai") and not contract.get("ai_data_use_terms"):
        flags.append({"id": "CON-02", "severity": "high",
                      "detail": "AI provider without contractual AI data-use terms "
                                "(no training on customer data, retention limits)"})
    return flags


def assess_vendor(vendor: dict, questionnaire: dict, as_of: date | None = None) -> Assessment:
    score = vendor_score(vendor)
    tier = tier_for_score(score)
    next_review = add_months(vendor["last_reviewed"], REVIEW_MONTHS[tier])
    return Assessment(vendor=vendor["name"], tier=tier, score=score, next_review=next_review,
                      red_flags=red_flags(vendor, questionnaire, tier, as_of))


# --- Risk memo (Markdown), with optional Claude drafting ---

def template_summary(a: Assessment) -> str:
    high = [f for f in a.red_flags if f["severity"] == "high"]
    if not a.red_flags:
        return f"{a.vendor} is Tier {a.tier} with no open red flags. Approve and review by {a.next_review}."
    verdict = "Do not approve until high-severity items are resolved" if high else \
              "Approve with conditions and track the items below to closure"
    return (f"{a.vendor} is Tier {a.tier} (score {a.score}/9) with {len(a.red_flags)} red flag(s), "
            f"{len(high)} high severity. {verdict}.")


def ai_summary(a: Assessment) -> str:
    """Ask Claude for a short decision summary. Falls back to the template on any problem."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set; using template summary.")
        return template_summary(a)
    import requests
    flags = "\n".join(f"- [{f['severity']}] {f['id']}: {f['detail']}" for f in a.red_flags) or "- none"
    prompt = (
        "You are a GRC analyst. Write a 3-sentence vendor risk decision summary for the Head of "
        "Information Security. Be direct, name the blocking issues, and recommend approve, "
        f"approve with conditions, or reject.\n\nVendor: {a.vendor}\nTier: {a.tier} (score {a.score}/9)\n"
        f"Red flags:\n{flags}"
    )
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": os.environ.get("GRC_AI_MODEL", "claude-sonnet-5-5"),
                  "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip() + "\n\n_Drafted with Claude; reviewed by GRC._"
    except Exception as exc:  # network, auth or schema problems never block the memo
        logger.warning("AI summary failed (%s); using template summary.", exc)
        return template_summary(a)


def render_memo(a: Assessment, summary: str) -> str:
    lines = [
        f"# Vendor Risk Memo: {a.vendor}",
        "",
        f"- **Tier:** {a.tier} (inherent score {a.score}/9)",
        f"- **Next review due:** {a.next_review}{' (OVERDUE)' if a.overdue else ''}",
        f"- **Generated:** {date.today()}",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Red flags",
        "",
    ]
    if a.red_flags:
        lines += ["| ID | Severity | Detail |", "|---|---|---|"]
        lines += [f"| {f['id']} | {f['severity']} | {f['detail']} |" for f in a.red_flags]
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


# --- Security intake ---

def score_intake(req: dict) -> dict:
    """Score a security intake request and list the reviews it needs."""
    score = DATA_SCORE[req["data_classification"]]
    reviews = ["Security architecture review"]
    if req.get("internet_facing"):
        score += 2
        reviews.append("Penetration test before launch")
    if req.get("handles_personal_data"):
        score += 2
        reviews.append("Privacy impact assessment (GDPR / CCPA / PIPEDA)")
    if req.get("uses_ai"):
        score += 1 + AI_AUTONOMY_SCORE.get(req.get("ai_autonomy", "none"), 0)
        reviews.append("AI risk and impact assessment (ISO/IEC 42001)")
    if req.get("third_party_vendor"):
        reviews.append(f"Third-party risk review: {req['third_party_vendor']}")
    if req.get("export_controlled_data"):
        score += 2
        reviews.append("Trade compliance review (export-controlled data)")
    if req.get("type") == "data_center":
        score += 2
        reviews.append("Physical security and colocation review")
    level = "high" if score >= 7 else "medium" if score >= 4 else "low"
    return {"request_id": req["request_id"], "score": score, "risk_level": level, "required_reviews": reviews}


# --- Risk register ---

def register_exceptions(register: dict, as_of: date | None = None) -> dict:
    """Risks at or above appetite that are still open, and risks overdue for review."""
    as_of = as_of or date.today()
    threshold = register["appetite_threshold"]
    above, overdue = [], []
    for r in register["risks"]:
        r = dict(r, score=r["likelihood"] * r["impact"])
        if r["score"] >= threshold and r["status"] != "closed":
            above.append(r)
        if r["review_date"] < as_of and r["status"] != "closed":
            overdue.append(r)
    return {"above_appetite": above, "overdue_review": overdue}


# --- Validation (run in CI on every pull request) ---

def validate_all(base: Path = BASE_DIR) -> list[str]:
    errors = []
    try:
        questionnaire = load_questionnaire(base)
    except Exception as exc:
        return [f"questionnaire.yaml: {exc}"]
    for qid, q in questionnaire.items():
        for key in ("domain", "question", "red_flag_if", "severity"):
            if key not in q:
                errors.append(f"questionnaire.yaml {qid}: missing '{key}'")
        if q.get("severity") not in ("low", "medium", "high"):
            errors.append(f"questionnaire.yaml {qid}: severity must be low, medium or high")

    for path in vendor_files(base):
        v = load_yaml(path)
        for key in VENDOR_REQUIRED:
            if key not in v:
                errors.append(f"{path.name}: missing '{key}'")
        for key, allowed in (("data_classification", DATA_SCORE), ("access_level", ACCESS_SCORE),
                             ("business_criticality", CRITICALITY_SCORE)):
            if key in v and v[key] not in allowed:
                errors.append(f"{path.name}: {key} '{v[key]}' not in {sorted(allowed)}")
        for qid in (v.get("answers") or {}):
            if qid not in questionnaire:
                errors.append(f"{path.name}: answer for unknown question '{qid}'")
        if "last_reviewed" in v and not isinstance(v["last_reviewed"], date):
            errors.append(f"{path.name}: last_reviewed must be a YYYY-MM-DD date")

    intake = load_yaml(base / "intake_example.yaml")
    for key in INTAKE_REQUIRED:
        if key not in intake:
            errors.append(f"intake_example.yaml: missing '{key}'")

    register = load_yaml(base / "risk_register.yaml")
    for r in register.get("risks", []):
        for key in ("likelihood", "impact"):
            if not 1 <= int(r.get(key, 0)) <= 5:
                errors.append(f"risk_register.yaml {r.get('id')}: {key} must be 1-5")
        if not isinstance(r.get("review_date"), date):
            errors.append(f"risk_register.yaml {r.get('id')}: review_date must be a YYYY-MM-DD date")
    return errors


# --- CLI ---

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GRC as Code: vendor risk, intake and risk register")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate all YAML (run in CI)")
    sub.add_parser("tier", help="tier every vendor")
    p_assess = sub.add_parser("assess", help="assess one vendor and write a Markdown memo")
    p_assess.add_argument("vendor_file")
    p_assess.add_argument("--ai", action="store_true", help="draft the summary with Claude")
    p_intake = sub.add_parser("intake", help="score a security intake request")
    p_intake.add_argument("intake_file")
    sub.add_parser("register", help="risks above appetite or overdue for review")
    args = parser.parse_args(argv)

    if args.command == "validate":
        errors = validate_all()
        for e in errors:
            print(f"ERROR {e}")
        print("All GRC YAML files are valid." if not errors else f"{len(errors)} error(s).")
        return 1 if errors else 0

    questionnaire = load_questionnaire()
    if args.command == "tier":
        print(f"{'Vendor':45} {'Tier':>4} {'Score':>5}  Next review   Flags")
        for path in vendor_files():
            a = assess_vendor(load_yaml(path), questionnaire)
            print(f"{a.vendor:45} {a.tier:>4} {a.score:>5}  {a.next_review}{'*' if a.overdue else ' '}  "
                  f"{len(a.red_flags)}")
        print("* overdue for review")
        return 0

    if args.command == "assess":
        a = assess_vendor(load_yaml(args.vendor_file), questionnaire)
        summary = ai_summary(a) if args.ai else template_summary(a)
        REPORTS_DIR.mkdir(exist_ok=True)
        out = REPORTS_DIR / f"{Path(args.vendor_file).stem}-risk-memo.md"
        out.write_text(render_memo(a, summary), encoding="utf-8")
        print(summary)
        print(f"Memo written to {out}")
        return 0

    if args.command == "intake":
        result = score_intake(load_yaml(args.intake_file))
        print(f"{result['request_id']}: {result['risk_level'].upper()} risk (score {result['score']})")
        for r in result["required_reviews"]:
            print(f"  - {r}")
        return 0

    if args.command == "register":
        res = register_exceptions(load_yaml(BASE_DIR / "risk_register.yaml"))
        print("Above appetite:")
        for r in res["above_appetite"]:
            print(f"  {r['id']} score {r['score']} | {r['title']} | owner: {r['owner']}")
        print("Overdue for review:")
        for r in res["overdue_review"]:
            print(f"  {r['id']} due {r['review_date']} | {r['title']}")
        return 0
    return 1


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("GRC_LOG_LEVEL", "INFO"))
    sys.exit(main())
