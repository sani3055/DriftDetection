import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

from src.experiments.journal_comparison import (
    EventEncoder, FrozenMonitor, Deployed, cosine, effective_features,
    moving_block_indices, request_v3, score_cutoff, shadow_guard,
)


def event(name='GetObject', **extra):
    return {'eventName':name,'eventSource':'s3.amazonaws.com','awsRegion':'us-east-1',**extra}


@pytest.mark.parametrize('kind',['ordinal','onehot'])
def test_encoding_never_uses_labels(kind):
    rows=[event('A'),event('B')]
    encoder=EventEncoder(kind).fit(rows)
    changed=[{**row,'attack_name':'attack','should_sample':True} for row in rows]
    np.testing.assert_array_equal(encoder.transform(rows),encoder.transform(changed))
    assert encoder.transform([event('never seen')]).shape==(1,encoder.width)
    assert encoder.unknown_rates([event('never seen')])['eventName']==1


def test_signed_grouping_preserves_sum():
    encoder=EventEncoder('onehot').fit([event('A'),event('B')])
    values=np.random.default_rng(0).normal(size=(8,encoder.width))
    np.testing.assert_allclose(encoder.aggregate_attributions(values).sum(axis=1),values.sum(axis=1))


def test_onehot_unknown_block_is_zero_without_new_vocabulary():
    encoder=EventEncoder('onehot').fit([event('A'),event('B')])
    values=encoder.transform([event('unseen')])
    assert np.all(values[:,encoder.groups[0]]==0)
    assert 'unseen' not in encoder.maps['eventName']


def test_coupling_cannot_distinguish_single_feature_shift_magnitude():
    left=np.array([1,0,0,0,0,0,0],dtype=float)
    assert cosine(left,100*left)==pytest.approx(1)
    assert cosine(.001*left,10*left)==pytest.approx(1)
    assert effective_features(left)==1
    assert effective_features(np.ones(7))==7
    assert cosine(left,np.zeros(7))==0


@pytest.mark.parametrize('kind',['ordinal','onehot'])
def test_monitor_signed_additivity_and_raw_unknown_drift(kind):
    rows=[event('A'),event('B')]*30
    encoder=EventEncoder(kind).fit(rows)
    model=IsolationForest(n_estimators=10,random_state=42).fit(encoder.transform(rows))
    monitor=FrozenMonitor(model,encoder,rows[:20])
    _,_,signal=monitor.signals([event('C')]*20)
    assert signal['psi_eventName']>0
    assert signal['unknown_eventName']==1
    assert monitor.max_additivity_residual<1e-8


def test_calibrated_cutoff_uses_earlier_scores_and_strict_ties():
    values=np.random.default_rng(1).normal(size=(100,2))
    model=IsolationForest(n_estimators=10,random_state=42).fit(values)
    cutoff=score_cutoff(model,values,'benign_quantile')
    assert cutoff==float(np.quantile(-model.score_samples(values),.95,method='higher'))
    assert Deployed(model,cutoff).predict(values).mean()<=.05
    assert score_cutoff(model,values,'training_offset')==-model.offset_


def test_guard_accepts_identical_model_but_is_not_an_attack_label_test():
    data=np.random.default_rng(0).normal(size=(100,2))
    model=IsolationForest(n_estimators=10,random_state=42).fit(data)
    state=Deployed(model,-model.offset_)
    assert shadow_guard(state,state,data[:20],data[20:30])['guard_allowed']
    with pytest.raises(ValueError): shadow_guard(state,state,data[:0],data[:10])


def test_block_bootstrap_never_mixes_session_indices():
    sampled=moving_block_indices([1,8,12],5,np.random.default_rng(42))
    assert sampled.shape==(21,)
    assert sampled[0]==0
    assert np.all((sampled[1:9]>=1)&(sampled[1:9]<9))
    assert np.all((sampled[9:]>=9)&(sampled[9:]<21))
    with pytest.raises(ValueError): moving_block_indices([1,0],5,np.random.default_rng(0))


def test_score_and_stream_baselines_have_no_shap_requirement():
    s={'feature_score':0.,'shap_score':0.,'coupling_score':0.,'conservative_score':0.,'score_wasserstein':2.}
    t={key:1. for key in s}
    assert request_v3('score_wasserstein',s,t,0)
    assert request_v3('adwin_score',s,t,0,adwin_alarm=True)
    assert request_v3('page_hinkley_score',s,t,0,ph_alarm=True)
    assert not request_v3('guarded_dual',s,t,0)
    assert request_v3('guarded_periodic',s,t,4)
