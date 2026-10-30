import numpy as np
from scripts.run_behaviour_tie_safe import tie_safe_slices,quarantined_release


class ShouldNotPredict:
    def predict(self,matrix):raise AssertionError('Empty pool should never be passed to the model')


def test_batch_boundaries_keep_all_ties_together():
    rows=[{'eventTime':str(time)} for time in [0,1,1,1,2,3,3,4]]
    slices=list(tie_safe_slices(rows,2))
    assert slices==[(0,4),(4,7),(7,8)]
    assert all(rows[end-1]['eventTime']!=rows[end]['eventTime'] for _,end in slices[:-1])


def test_empty_quarantine_is_deferred_without_model_prediction():
    selected,reason=quarantined_release(np.empty((0,23)),ShouldNotPredict(),0.,.2)
    assert len(selected)==0 and reason=='insufficient_retained_candidates'
