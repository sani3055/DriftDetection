from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from src.demo.review_data import PROJECT_ROOT, SCENARIO_NAMES, evaluate_example, load_review_data


def test_demo_exposes_all_held_out_scenarios_and_runs():
    examples, thresholds = load_review_data()
    assert len(examples) == 70
    assert {item.seed for item in examples} == set(range(5, 15))
    assert {item.scenario for item in examples} == set(SCENARIO_NAMES)
    for example in examples:
        result = evaluate_example(example, thresholds)
        assert result.diagnosis == example.recorded_diagnosis
        assert result.update_requested == example.recorded_update


@pytest.mark.parametrize("scenario,diagnosis,update,match", [
    ("stable", "stable", False, True),
    ("benign_region", "benign_drift", False, True),
    ("benign_identity", "benign_drift", False, True),
    ("benign_service", "benign_drift", False, True),
    ("security_privilege", "benign_drift", False, False),
    ("security_defense", "security_relevant_drift", True, True),
    ("security_credential", "security_relevant_drift", True, True),
])
def test_demo_preserves_successes_and_missed_cases(scenario, diagnosis, update, match):
    examples, thresholds = load_review_data()
    example = next(item for item in examples if item.seed == 5 and item.scenario == scenario)
    result = evaluate_example(example, thresholds)
    assert (result.diagnosis, result.update_requested, result.matches_target) == (diagnosis, update, match)


def test_scenario_target_cannot_change_the_decision():
    examples, thresholds = load_review_data()
    example = next(item for item in examples if item.seed == 5 and item.scenario == "security_defense")
    actual = evaluate_example(example, thresholds)
    changed = evaluate_example(replace(example, expected_class="stable", scenario="stable"), thresholds)
    assert changed.diagnosis == actual.diagnosis
    assert changed.update_requested == actual.update_requested
    assert changed.matches_target is False


def test_demo_does_not_modify_saved_evidence():
    paths = [PROJECT_ROOT / "data/benchmark" / name for name in (
        "diagnosis_results.csv", "adaptation_results.csv", "diagnosis_thresholds.json",
    )]
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    examples, thresholds = load_review_data()
    for example in examples:
        evaluate_example(example, thresholds)
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths} == before


def copied_evidence(tmp_path: Path) -> Path:
    folder = tmp_path / "data/benchmark"
    folder.mkdir(parents=True)
    for name in ("diagnosis_results.csv", "adaptation_results.csv", "diagnosis_thresholds.json"):
        shutil.copy2(PROJECT_ROOT / "data/benchmark" / name, folder / name)
    return tmp_path


def test_invalid_threshold_is_rejected(tmp_path):
    root = copied_evidence(tmp_path)
    path = root / "data/benchmark/diagnosis_thresholds.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["feature_threshold"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="Decision limits"):
        load_review_data(root)


def test_stale_saved_decision_is_rejected(tmp_path):
    root = copied_evidence(tmp_path)
    path = root / "data/benchmark/diagnosis_results.csv"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    header = lines[0].split(",")
    for i, line in enumerate(lines[1:], 1):
        values = line.split(",")
        if values[header.index("split")] == "test":
            values[header.index("coupled_diagnosis")] = "review_required"
            lines[i] = ",".join(values)
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="disagrees with saved evidence"):
        load_review_data(root)


def test_missing_evidence_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_review_data(tmp_path)
