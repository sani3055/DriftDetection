from pathlib import Path

import pytest

pytest.importorskip("streamlit", reason="Install requirements-demo.txt for optional UI tests")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_scenario_selector_and_missed_case():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.selectbox(key="seed").value == 5
    assert app.subheader[0].value == "Stable period"
    assert not app.error
    for scenario in ["benign_region", "benign_identity", "benign_service"]:
        app.selectbox(key="scenario").set_value(scenario).run()
        assert not app.exception
        assert app.subheader[0].value == "Routine drift"
        assert not app.error
    app.selectbox(key="scenario").set_value("security_privilege").run()
    assert not app.exception
    assert app.subheader[0].value == "Routine drift"
    assert any("Missed security-related scenario" in item.value for item in app.error)
    for scenario in ["security_defense", "security_credential"]:
        app.selectbox(key="scenario").set_value(scenario).run()
        assert not app.exception
        assert app.subheader[0].value == "Security-relevant drift"
        assert not app.error
        assert any(item.value == "**Update requested**" for item in app.markdown)


def test_streamlit_every_held_out_run_renders():
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
    for seed in range(5, 15):
        app.selectbox(key="seed").set_value(seed).run()
        assert not app.exception
        assert app.selectbox(key="seed").value == seed
        assert app.subheader[0].value == "Stable period"


def test_chart_preserves_real_values_and_independent_scales():
    import runpy
    from src.demo.review_data import load_review_data

    module = runpy.run_path(str(ROOT / "streamlit_app.py"), run_name="demo_test_helpers")
    examples, thresholds = load_review_data()
    example = next(item for item in examples if item.seed == 5 and item.scenario == "security_defense")
    specification = module["signal_chart"](example, thresholds, examples).to_dict()
    assert specification["resolve"]["scale"]["x"] == "independent"
    assert len(specification["vconcat"]) == 3
    assert any(example.feature_drift_score == row.get("Score") for rows in specification["datasets"].values() for row in rows)
