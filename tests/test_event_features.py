from __future__ import annotations

import pandas as pd

from src.features.event_features import FEATURE_NAMES, encode_events, fit_category_maps


def test_event_encoding_is_train_only_and_unknown_safe() -> None:
    train = pd.DataFrame({
        "eventName": ["ListBuckets"],
        "eventSource": ["s3.amazonaws.com"],
        "awsRegion": ["us-east-1"],
        "userIdentitytype": ["IAMUser"],
        "errorCode": ["None"],
        "requestParametersinstanceType": ["NotApplicable"],
    })
    maps = fit_category_maps(train)
    current = train.copy()
    current.loc[0, "eventName"] = "NewFutureEvent"
    encoded = encode_events(current, maps)
    assert encoded.shape == (1, len(FEATURE_NAMES))
    assert encoded[0, 0] == -1

