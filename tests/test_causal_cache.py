from scripts.build_causal_feature_cache import order_hash


def test_cache_order_hash_detects_id_and_timestamp_changes_but_not_labels():
    rows=[{'eventID':'a','eventTime':'2026-01-01T00:00:00Z','should_sample':False},
          {'eventID':'b','eventTime':'2026-01-01T00:00:01Z','should_sample':True}]
    with_different_labels=[{**row,'should_sample':not row['should_sample']} for row in rows]
    assert order_hash(rows)==order_hash(with_different_labels)
    assert order_hash(rows)!=order_hash(list(reversed(rows)))
    assert order_hash(rows)!=order_hash([{**rows[0],'eventID':'other'},rows[1]])
