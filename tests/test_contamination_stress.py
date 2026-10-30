import numpy as np
from scripts.stress_candidate_contamination import controlled_indices


def test_candidate_pool_has_declared_fraction_without_duplicates():
    labels=np.r_[np.zeros(300),np.ones(100)]
    selected=controlled_indices(labels,200,.10,42)
    assert len(selected)==len(set(selected))==200
    assert labels[selected].sum()==20
    assert np.array_equal(selected,controlled_indices(labels,200,.10,42))
