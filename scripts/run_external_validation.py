"""Evaluate the primary detector on an independent labeled CloudTrail corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluation.metrics import binary_detection_metrics  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402


FEATURES = (
    "eventName",
    "eventSource",
    "awsRegion",
    "userIdentitytype",
    "errorCode",
    "requestParametersinstanceType",
    "isRoot",
)


def load_records(path: Path) -> list[dict]:
    with zipfile.ZipFile(path) as archive:
        json_name = next(name for name in archive.namelist() if name.endswith(".json"))
        with archive.open(json_name) as handle:
            payload = json.load(handle)
    return payload["Records"]


def normalize_record(record: dict) -> dict[str, str | int | bool]:
    identity = record.get("userIdentity") or {}
    request = record.get("requestParameters") or {}
    identity_type = str(identity.get("type") or "Unknown")
    return {
        "eventName": str(record.get("eventName") or "Unknown"),
        "eventSource": str(record.get("eventSource") or "Unknown"),
        "awsRegion": str(record.get("awsRegion") or "Unknown"),
        "userIdentitytype": identity_type,
        "errorCode": str(record.get("errorCode") or "NoError"),
        "requestParametersinstanceType": str(request.get("instanceType") or "NotApplicable"),
        "isRoot": int(identity_type == "Root" or ":root" in str(identity.get("arn") or "")),
    }


def encode(train: list[dict], test: list[dict]) -> tuple[np.ndarray, np.ndarray, dict[str, dict[str, int]]]:
    train_frame = pd.DataFrame([normalize_record(record) for record in train])
    test_frame = pd.DataFrame([normalize_record(record) for record in test])
    maps: dict[str, dict[str, int]] = {}
    train_matrix = np.zeros((len(train_frame), len(FEATURES)), dtype=np.float64)
    test_matrix = np.zeros((len(test_frame), len(FEATURES)), dtype=np.float64)
    for index, feature in enumerate(FEATURES):
        if feature == "isRoot":
            train_matrix[:, index] = train_frame[feature].astype(float)
            test_matrix[:, index] = test_frame[feature].astype(float)
            maps[feature] = {"0": 0, "1": 1}
            continue
        values = sorted(train_frame[feature].astype(str).unique().tolist())
        mapping = {value: number for number, value in enumerate(values)}
        maps[feature] = mapping
        train_matrix[:, index] = train_frame[feature].astype(str).map(mapping).fillna(-1).astype(float)
        test_matrix[:, index] = test_frame[feature].astype(str).map(mapping).fillna(-1).astype(float)
    return train_matrix, test_matrix, maps


def detector_predictions(name: str, train: np.ndarray, test: np.ndarray, seed: int) -> np.ndarray:
    if name == "isolation_forest":
        detector = IsolationForest(n_estimators=100, contamination=0.05, random_state=seed, n_jobs=1)
    elif name == "local_outlier_factor":
        detector = LocalOutlierFactor(n_neighbors=20, contamination=0.05, novelty=True)
    elif name == "one_class_svm":
        detector = OneClassSVM(nu=0.05, gamma="scale")
    else:
        raise ValueError(name)
    detector.fit(train)
    return (detector.predict(test) == -1).astype(int)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    config = load_yaml(ROOT / "configs" / "external.yaml")["external"]
    dataset_root = ROOT / config["dataset_root"]
    train_archive = dataset_root / config["train_archive"]
    test_archive = dataset_root / config["test_archive"]
    train_records = load_records(train_archive)
    test_records = load_records(test_archive)
    train_matrix, test_matrix, category_maps = encode(train_records, test_records)
    labels = np.asarray([int(bool(record.get("should_sample", False))) for record in test_records], dtype=int)
    output = ROOT / "data" / "external_validation"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    scenario_rows = []
    for detector_name in ["isolation_forest", "local_outlier_factor", "one_class_svm"]:
        predictions = detector_predictions(detector_name, train_matrix, test_matrix, int(config["random_state"]))
        rows.append({"detector": detector_name, **binary_detection_metrics(labels, predictions)})
        for scenario in sorted({str(record.get("attack_name") or "benign") for record in test_records}):
            mask = np.asarray([str(record.get("attack_name") or "benign") == scenario for record in test_records])
            scenario_rows.append({
                "detector": detector_name,
                "scenario": scenario,
                "n_records": int(mask.sum()),
                **binary_detection_metrics(labels[mask], predictions[mask]),
            })
    pd.DataFrame(rows).to_csv(output / "external_detector_metrics.csv", index=False)
    pd.DataFrame(scenario_rows).to_csv(output / "external_scenario_metrics.csv", index=False)
    manifest = {
        "dataset_name": "Cloud Log Sampling Dataset",
        "source_url": "https://github.com/ArielCyber/cloud_log_sampling",
        "train_archive": str(train_archive),
        "test_archive": str(test_archive),
        "train_records": len(train_records),
        "test_records": len(test_records),
        "test_attack_records": int(labels.sum()),
        "test_benign_records": int((labels == 0).sum()),
        "test_scenarios": sorted({str(record.get("attack_name") or "benign") for record in test_records}),
        "train_archive_sha256": sha256(train_archive),
        "test_archive_sha256": sha256(test_archive),
        "feature_contract": list(FEATURES),
        "protocol": "fit on benign-only training archive; evaluate on labeled mixed test archive",
        "note": "Independent validation of the detector representation; full SHAP drift diagnosis requires aligned temporal windows and is not claimed here.",
    }
    (output / "external_validation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
