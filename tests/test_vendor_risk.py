"""Tests for GRC as Code: vendor tiering, red flags, intake scoring and the risk register."""

from datetime import date

import pytest

import vendor_risk as vr

AS_OF = date(2026, 11, 21)


@pytest.fixture(scope="module")
def questionnaire():
    return vr.load_questionnaire()


def base_vendor(**overrides):
    vendor = {
        "name": "Test Vendor",
        "category": "saas",
        "business_owner": "IT",
        "data_classification": "internal",
        "access_level": "none",
        "business_criticality": "low",
        "processes_data_with_ai": False,
        "attestations": [{"type": "SOC 2 Type II", "period_end": date(2026, 9, 30)}],
        "contract": {"dpa_signed": True, "ai_data_use_terms": True},
        "answers": {"IAM-01": True, "IAM-02": True, "END-01": True, "ENC-01": True,
                    "ENC-02": True, "AI-01": False, "AI-02": True, "PRIV-01": True,
                    "PRIV-02": True, "IR-01": True},
        "last_reviewed": date(2026, 6, 1),
    }
    vendor.update(overrides)
    return vendor


def test_repository_yaml_is_valid():
    assert vr.validate_all() == []


@pytest.mark.parametrize("score,tier", [(0, 3), (2, 3), (3, 2), (5, 2), (6, 1), (9, 1)])
def test_tier_thresholds(score, tier):
    assert vr.tier_for_score(score) == tier


def test_ai_processing_raises_score():
    plain = vr.vendor_score(base_vendor())
    with_ai = vr.vendor_score(base_vendor(processes_data_with_ai=True))
    assert with_ai == plain + 1


def test_clean_low_risk_vendor_has_no_flags(questionnaire):
    a = vr.assess_vendor(base_vendor(), questionnaire, as_of=AS_OF)
    assert a.tier == 3
    assert a.red_flags == []


def test_missing_mfa_is_high_severity_flag(questionnaire):
    v = base_vendor(answers={**base_vendor()["answers"], "IAM-02": False})
    flags = vr.red_flags(v, questionnaire, tier=2, as_of=AS_OF)
    assert any(f["id"] == "IAM-02" and f["severity"] == "high" for f in flags)


def test_training_on_customer_data_is_flagged(questionnaire):
    v = base_vendor(answers={**base_vendor()["answers"], "AI-01": True})
    flags = vr.red_flags(v, questionnaire, tier=2, as_of=AS_OF)
    assert any(f["id"] == "AI-01" for f in flags)


def test_stale_attestation_is_flagged(questionnaire):
    v = base_vendor(attestations=[{"type": "SOC 2 Type II", "period_end": date(2025, 1, 31)}])
    flags = vr.red_flags(v, questionnaire, tier=2, as_of=AS_OF)
    assert any(f["id"] == "ATT-01" for f in flags)


def test_tier1_without_attestation_is_flagged(questionnaire):
    flags = vr.red_flags(base_vendor(attestations=[]), questionnaire, tier=1, as_of=AS_OF)
    assert any(f["id"] == "ATT-00" for f in flags)


def test_confidential_data_without_dpa_is_flagged(questionnaire):
    v = base_vendor(data_classification="confidential", contract={"dpa_signed": False,
                                                                   "ai_data_use_terms": True})
    flags = vr.red_flags(v, questionnaire, tier=2, as_of=AS_OF)
    assert any(f["id"] == "CON-01" for f in flags)


def test_ai_vendor_without_ai_terms_is_flagged(questionnaire):
    v = base_vendor(processes_data_with_ai=True, contract={"dpa_signed": True,
                                                            "ai_data_use_terms": False})
    flags = vr.red_flags(v, questionnaire, tier=2, as_of=AS_OF)
    assert any(f["id"] == "CON-02" for f in flags)


def test_physical_question_only_applies_to_colocation(questionnaire):
    saas = vr.red_flags(base_vendor(), questionnaire, tier=1, as_of=AS_OF)
    colo = vr.red_flags(base_vendor(category="colocation"), questionnaire, tier=1, as_of=AS_OF)
    assert not any(f["id"] == "PHY-01" for f in saas)
    assert any(f["id"] == "PHY-01" for f in colo)


def test_next_review_follows_tier_cadence(questionnaire):
    a = vr.assess_vendor(base_vendor(), questionnaire, as_of=AS_OF)
    assert a.next_review == date(2029, 6, 1)  # Tier 3 = 36 months


def test_add_months_handles_month_end():
    assert vr.add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert vr.add_months(date(2027, 11, 30), 3) == date(2028, 2, 29)


def test_memo_contains_flags_and_summary(questionnaire):
    v = base_vendor(answers={**base_vendor()["answers"], "ENC-01": False})
    a = vr.assess_vendor(v, questionnaire, as_of=AS_OF)
    memo = vr.render_memo(a, vr.template_summary(a))
    assert "# Vendor Risk Memo: Test Vendor" in memo
    assert "ENC-01" in memo
    assert "Do not approve" in memo


def test_ai_summary_falls_back_without_api_key(monkeypatch, questionnaire):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    a = vr.assess_vendor(base_vendor(), questionnaire, as_of=AS_OF)
    assert vr.ai_summary(a) == vr.template_summary(a)


def test_intake_scoring_and_reviews():
    result = vr.score_intake({
        "request_id": "I-1", "title": "x", "type": "data_center", "requested_by": "Infra",
        "data_classification": "restricted", "internet_facing": False,
        "handles_personal_data": True, "uses_ai": False, "export_controlled_data": True,
    })
    assert result["risk_level"] == "high"
    assert "Trade compliance review (export-controlled data)" in result["required_reviews"]
    assert "Physical security and colocation review" in result["required_reviews"]


def test_low_risk_intake():
    result = vr.score_intake({
        "request_id": "I-2", "title": "x", "type": "internal_tool", "requested_by": "HR",
        "data_classification": "public", "internet_facing": False,
        "handles_personal_data": False, "uses_ai": False,
    })
    assert result["risk_level"] == "low"


def test_register_exceptions():
    register = {"appetite_threshold": 12, "risks": [
        {"id": "A", "title": "a", "likelihood": 4, "impact": 4, "status": "open",
         "owner": "x", "review_date": date(2027, 1, 1)},
        {"id": "B", "title": "b", "likelihood": 2, "impact": 2, "status": "open",
         "owner": "x", "review_date": date(2026, 1, 1)},
        {"id": "C", "title": "c", "likelihood": 5, "impact": 5, "status": "closed",
         "owner": "x", "review_date": date(2026, 1, 1)},
    ]}
    res = vr.register_exceptions(register, as_of=AS_OF)
    assert [r["id"] for r in res["above_appetite"]] == ["A"]
    assert [r["id"] for r in res["overdue_review"]] == ["B"]


def test_cli_validate_returns_zero(capsys):
    assert vr.main(["validate"]) == 0
    assert "valid" in capsys.readouterr().out
