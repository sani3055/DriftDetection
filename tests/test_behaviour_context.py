from copy import deepcopy
import numpy as np
import pytest
from src.experiments.behaviour_context import BEHAVIOUR_FEATURES, CausalHistory, actor_key, resource_tokens


def event(second, **changes):
    row = {'eventTime': f'2026-01-01T00:00:{second:02d}Z', 'eventName': 'GetObject',
           'eventSource': 's3.amazonaws.com', 'userIdentity': {'type': 'IAMUser', 'arn': 'actor'},
           'sourceIPAddress': 'source', 'userAgent': 'agent', 'requestParameters': {'bucketName': 'bucket'}}
    row.update(changes)
    return row


def test_current_event_does_not_count_itself_and_ties_are_not_ordered():
    matrix = CausalHistory().transform([event(0), event(0), event(1)])
    index = BEHAVIOUR_FEATURES.index('actor_log_events_1h')
    assert matrix[0, index] == matrix[1, index] == 0
    assert matrix[2, index] == pytest.approx(np.log1p(2))


def test_outcomes_future_and_multiplicity_cannot_change_prefix():
    rows = [event(0), event(1)]
    changed = deepcopy(rows)
    for row in changed:
        row.update(should_sample=True, attack_name='anything', count_of_same_events=999999)
    changed.append(event(2, eventName='DeleteTrail'))
    assert np.array_equal(CausalHistory().transform(rows), CausalHistory().transform(changed)[:2])


def test_missing_resources_are_not_new_and_response_secrets_are_ignored():
    row = event(0, requestParameters={}, responseElements={'secret': 'never read'})
    assert resource_tokens(row) == ()
    values = CausalHistory().transform([row])[0]
    assert values[BEHAVIOUR_FEATURES.index('actor_resource_new')] == 0


def test_failure_fraction_and_independent_clones():
    state = CausalHistory()
    state.transform([event(0, errorCode='Denied')])
    a, b = state.clone(), state.clone()
    result = a.transform([event(1)])
    assert result[0, BEHAVIOUR_FEATURES.index('actor_failure_fraction_1h')] == 1
    assert np.array_equal(result, b.transform([event(1)]))


def test_chronology_and_split_timestamp_groups_are_rejected():
    with pytest.raises(ValueError): CausalHistory().transform([event(1), event(0)])
    state = CausalHistory()
    state.transform([event(0)])
    with pytest.raises(ValueError): state.transform([event(0)])


def test_issuer_groups_assumed_sessions_without_exporting_raw_keys():
    identity = {'arn': 'session', 'sessionContext': {'sessionIssuer': {'arn': 'role'}}}
    assert actor_key(event(0, userIdentity=identity)) == ('issuer', 'role')
    assert CausalHistory().transform([event(0)]).shape == (1, 16)
