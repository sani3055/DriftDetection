from __future__ import annotations

import csv

from src.models.isolation_forest import score_csv, train_detector


def test_detector_trains_on_selected_months_and_scores(tmp_path) -> None:
    path = tmp_path / "events.csv"
    header = [
        "eventTime", "eventName", "eventSource", "awsRegion", "userIdentitytype",
        "errorCode", "requestParametersinstanceType",
    ]
    rows = []
    for month in ("2020-01", "2020-02", "2020-03"):
        for index in range(8):
            rows.append([month, "ListBuckets" if index < 6 else "DeleteTrail", "s3.amazonaws.com", "us-east-1", "IAMUser", "None", "NotApplicable"])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)

    artifact_path = tmp_path / "model.joblib"
    artifact = train_detector(path, ["2020-01"], artifact_path, n_estimators=10, n_jobs=1, chunk_size=4)
    scores = score_csv(path, artifact, tmp_path / "scores.csv", sample_per_window=3, chunk_size=4)
    assert artifact["training_rows"] == 8
    assert set(scores["window_id"]) == {"2020-01", "2020-02", "2020-03"}
    assert len(scores) == 9

