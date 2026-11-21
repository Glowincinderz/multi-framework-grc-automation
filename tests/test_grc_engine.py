"""Smoke tests for the core GRC engine, using a throwaway SQLite database."""

import importlib

import pytest


@pytest.fixture()
def engine(tmp_path, monkeypatch):
    monkeypatch.setenv("GRC_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GRC_BACKUP_DIR", str(tmp_path / "backups"))
    import grc_engine
    grc_engine = importlib.reload(grc_engine)
    grc_engine.init_database()
    return grc_engine


@pytest.mark.parametrize("framework", ["ISO27001", "SOC2", "NISTCSF", "PCIDSS", "ISO42001"])
def test_control_library_loads_and_is_idempotent(engine, framework):
    engine.load_controls_from_library(framework)
    first = engine.get_control_summary(framework)
    engine.load_controls_from_library(framework)
    second = engine.get_control_summary(framework)
    assert first == second
    assert first["Total"] > 0


def test_add_risk_scores(engine):
    risk_id = engine.add_risk("Test", "desc", "asset", "threat", "vuln",
                              likelihood=4, impact=5, treatment="Mitigate")
    assert risk_id.startswith("RISK-")
    conn = engine.get_connection()
    row = conn.execute("SELECT inherent_risk, residual_risk FROM risks WHERE risk_id=?",
                       (risk_id,)).fetchone()
    conn.close()
    assert row["inherent_risk"] == 20
    assert row["residual_risk"] == 10


def test_add_risk_rejects_out_of_range(engine):
    with pytest.raises(ValueError):
        engine.add_risk("x", "d", "a", "t", "v", likelihood=6, impact=1, treatment="Accept")


def test_backup_creates_file(engine, tmp_path):
    path = engine.backup_database(str(tmp_path / "backups"))
    assert path and (tmp_path / "backups").exists()
