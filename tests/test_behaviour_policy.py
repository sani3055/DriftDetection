import numpy as np
from scripts.run_behaviour_comparison import requested,quarantined_release


class Normal:
    def predict(self,matrix):return np.zeros(len(matrix),dtype=int)


def test_quarantine_never_releases_current_or_missing_pool():
    positions,reason=quarantined_release(None,Normal(),0,.1)
    assert len(positions)==0 and reason=='no_previous_pool'
    pool=np.zeros((20,2))
    assert quarantined_release(pool,Normal(),.11,.1)[1]=='current_alarm_fraction'
    positions,reason=quarantined_release(pool,Normal(),.1,.1)
    assert reason=='eligible' and np.array_equal(positions,np.arange(20))


def test_coupling_is_incremental_gate_not_alternative_magnitude_test():
    gates={'feature_score':1.,'shap_score':1.,'coupling_score':.8,'score_wasserstein':1.}
    signal={'feature_score':2.,'shap_score':2.,'coupling_score':.7,'score_wasserstein':0.}
    assert requested('dual_signal',signal,gates,0)
    for policy in ('coupled_signal','guarded_coupled','delayed_guarded_coupled'):
        assert not requested(policy,signal,gates,0)
    signal['coupling_score']=.9
    assert requested('delayed_guarded_coupled',signal,gates,0)
    assert not requested('static',signal,gates,0)
