import numpy as np
from sklearn.ensemble import IsolationForest
from src.experiments.behaviour_monitor import MixedEncoder, MixedMonitor, reference_edges, chronological_partitions
from src.experiments.behaviour_context import CausalHistory


def rows():
    return [{'eventTime':f'2026-01-01T00:{i//60:02d}:{i%60:02d}Z', 'eventName':'GetObject',
             'eventSource':'s3.amazonaws.com','userIdentity':{'type':'IAMUser','arn':str(i%2)}} for i in range(80)]


def test_constant_numeric_bins_preserve_new_values():
    edges = reference_edges(np.zeros(20))
    assert len(set(np.searchsorted(edges, [-1., 0., 1.], side='right'))) == 3


def test_modes_grouped_shap_and_no_outcome_input():
    records = rows()
    behaviour = CausalHistory().transform(records)
    for mode, encoding, width in [('event','ordinal',7),('behaviour','none',16),('combined','onehot',23)]:
        encoder = MixedEncoder(mode,encoding).fit(records,behaviour)
        matrix = encoder.transform(records,behaviour)
        forest = IsolationForest(n_estimators=8,random_state=42).fit(matrix)
        monitor = MixedMonitor(forest,encoder,records[:40],behaviour[:40])
        _,_,signal = monitor.signals(records[40:],behaviour[40:])
        assert len(encoder.features) == width
        assert monitor.max_residual < 1e-8
        assert np.isfinite(list(signal.values())).all()


def test_broad_partitions_never_split_timestamps():
    records = [{'eventTime':f'2026-01-01T{i//6:02d}:00:00Z'} for i in range(120)]
    partitions = chronological_partitions(records,'broad')
    assert sorted(i for part in partitions for i in part) == list(range(120))
    for a,b in zip(partitions,partitions[1:]):
        assert records[a[-1]]['eventTime'] < records[b[0]]['eventTime']
