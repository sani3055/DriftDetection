from copy import deepcopy
import pytest
from src.experiments.generic_cloud_adapter import adapt_generic_event


def sample():
    return {'event_id':'evt-1', 'timestamp':'2026-01-01T00:00:00Z',
            'action':'storage.object.read', 'actor_id':'actor-1', 'actor_type':'human',
            'result':'success', 'resource_id':'bucket/x', 'is_anomaly':False,
            'scenario':'normal', 'incident_id':None}


def test_outcome_and_scenario_never_affect_adapter():
    a=sample(); b=deepcopy(a)
    b.update(is_anomaly=True, scenario='attack', incident_id='incident', request_count_5m=9999)
    assert adapt_generic_event(a) == adapt_generic_event(b)
    assert 'is_anomaly' not in adapt_generic_event(a)
    assert 'readOnly' not in adapt_generic_event(a)


def test_result_mapping_is_explicit():
    a=sample(); a['result']='denied'
    assert adapt_generic_event(a)['errorCode']=='generic:denied'
    a['result']='mystery'
    with pytest.raises(ValueError): adapt_generic_event(a)


def test_missing_core_fields_fail_closed():
    a=sample(); del a['actor_id']
    with pytest.raises(ValueError): adapt_generic_event(a)
