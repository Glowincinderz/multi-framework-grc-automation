"""Integrity checks for every control library: counts, unique IDs and required fields."""

import importlib

import pytest

import grc_engine

REQUIRED = ("id", "theme", "title", "description", "artifacts", "test_procedure")

LIBRARIES = {fw: spec for fw, spec in grc_engine._FRAMEWORK_MODULES.items()}


def load(framework):
    module_name, attr = LIBRARIES[framework]
    module = importlib.import_module(module_name)
    return module, getattr(module, attr)


def test_all_six_frameworks_registered():
    assert set(LIBRARIES) == {"ISO27001", "SOC1", "SOC2", "NISTCSF", "PCIDSS", "ISO42001"}


@pytest.mark.parametrize("framework", sorted(LIBRARIES))
def test_required_fields_and_unique_ids(framework):
    _, controls = load(framework)
    ids = [c["id"] for c in controls]
    assert len(ids) == len(set(ids)), f"duplicate IDs in {framework}"
    for c in controls:
        for key in REQUIRED:
            assert c.get(key), f"{framework} {c.get('id')}: missing {key}"
        assert isinstance(c["artifacts"], list) and c["artifacts"]


@pytest.mark.parametrize("framework", sorted(LIBRARIES))
def test_declared_control_count_matches(framework):
    module, controls = load(framework)
    expected = getattr(module, "CONTROL_COUNT_EXPECTED", None)
    if expected is not None:
        assert len(controls) == expected


def test_ids_unique_across_frameworks():
    """controls.id is the primary key, so IDs must not collide between libraries."""
    seen = {}
    for fw in LIBRARIES:
        for c in load(fw)[1]:
            assert c["id"] not in seen, f"{c['id']} in both {seen.get(c['id'])} and {fw}"
            seen[c["id"]] = fw


def test_soc2_covers_all_five_trust_services_categories():
    _, controls = load("SOC2")
    themes = {c["theme"] for c in controls}
    assert themes == {"Common Criteria", "Availability", "Confidentiality",
                      "Processing Integrity", "Privacy"}
    ids = {c["id"] for c in controls}
    assert {"PI1.1", "PI1.5", "P1.1", "P8.1"} <= ids


def test_soc1_covers_itgcs_business_processes_and_cuecs():
    _, controls = load("SOC1")
    themes = {c["theme"] for c in controls}
    assert {"Logical Access", "Change Management", "Computer Operations",
            "Transaction Processing", "Subservice & User Entities"} <= themes
    assert any("CUEC" in c["title"] for c in controls)
