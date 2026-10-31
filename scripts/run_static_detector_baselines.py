"""Post-hoc matched static baselines using one fixed historical calibration rule."""
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_causal_feature_cache import order_hash
from scripts.run_journal_temporal import load
from src.experiments.behaviour_monitor import MixedEncoder, chronological_partitions
from src.experiments.journal_protocol import confusion, metrics, ordered_unique


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output=ROOT/'results/journal_v6_static_baselines'
    if (output/'manifest.json').exists(): raise FileExistsError('Preserve completed comparison')
    data=ROOT/'data/external/cloud_log_sampling-main'
    cache=ROOT/'results/journal_v4_causal_cache'
    meta=json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    if (meta['base_sha256']!=sha(data/'TrainOn/base_a.zip') or
        meta['base_feature_sha256']!=sha(cache/'base.npz') or
        meta['history_code_sha256']!=sha(ROOT/'src/experiments/behaviour_context.py')):
        raise ValueError('Source or feature provenance mismatch')
    base=ordered_unique(load(data/'TrainOn/base_a.zip'))[0]
    if order_hash(base)!=meta['base_order_sha256']: raise ValueError('Base order mismatch')
    behaviour=np.load(cache/'base.npz',allow_pickle=False)['features']
    fit,reference,calibration,guard=chronological_partitions(base,'narrow')
    sessions=[]; seen={r['eventID'] for r in base}
    for archive in [data/'TestOn/labeled_cloudtrail_a.zip',data/'TrainOn/train_labeled_a.zip']:
        rows=ordered_unique(load(archive))[0]
        if seen & {r['eventID'] for r in rows}: raise ValueError('Source ID overlap')
        seen.update(r['eventID'] for r in rows)
        rows=[r for r in rows if r['eventTime']>base[-1]['eventTime']]
        for day in sorted({r['eventTime'][:10] for r in rows}):
            name=archive.stem+'_'+day
            sequence=[r for r in rows if r['eventTime'][:10]==day]
            entry=meta['files'][name]
            if (entry['order_sha256']!=order_hash(sequence) or entry['source_archive_sha256']!=sha(archive)
                or entry['sha256']!=sha(cache/entry['name'])): raise ValueError('Session provenance mismatch')
            sessions.append((name,sequence,np.load(cache/entry['name'],allow_pickle=False)['features']))
    outcomes=[]; timing=[]
    for representation in ('event','combined'):
        encoder=MixedEncoder(representation,'ordinal').fit([base[i] for i in fit],behaviour[fit])
        def transform(indices): return encoder.transform([base[i] for i in indices],behaviour[indices])
        scaler=StandardScaler().fit(transform(fit))
        train_x=scaler.transform(transform(fit)); cal_x=scaler.transform(transform(calibration))
        test_x=[scaler.transform(encoder.transform(seq,b)) for _,seq,b in sessions]
        detectors={'isolation_forest':IsolationForest(n_estimators=100,contamination=.05,random_state=42,n_jobs=1),
                   'one_class_svm':OneClassSVM(kernel='rbf',nu=.05,gamma='scale'),
                   'local_outlier_factor':LocalOutlierFactor(n_neighbors=20,novelty=True,n_jobs=1)}
        for name,model in detectors.items():
            start=perf_counter();model.fit(train_x);fit_s=perf_counter()-start
            start=perf_counter();cal_scores=-model.score_samples(cal_x)
            threshold=float(np.quantile(cal_scores,.95,method='higher'))
            scores=[-model.score_samples(x) for x in test_x];score_s=perf_counter()-start
            # Only after all predictions and thresholds are fixed are target labels read.
            labels=[np.array([int(bool(r.get('should_sample',False))) for r in seq]) for _,seq,_ in sessions]
            for session,score,label in [('pooled',np.concatenate(scores),np.concatenate(labels))]+[(s[0],z,y) for s,z,y in zip(sessions,scores,labels)]:
                pred=score>threshold; counts=confusion(label,pred)
                auc=float(roc_auc_score(label,score)) if len(np.unique(label))==2 else None
                ap=float(average_precision_score(label,score)) if len(np.unique(label))==2 else None
                outcomes.append({'representation':representation,'detector':name,'session':session,'events':len(label),
                                 'threshold':threshold,'calibration_alarm_fraction':float((cal_scores>threshold).mean()),
                                 **counts,**metrics(counts),'roc_auc':auc,'average_precision':ap})
            timing.append({'representation':representation,'detector':name,'fit_seconds':fit_s,
                           'calibration_plus_test_score_seconds':score_s,'fit_events':len(train_x),
                           'calibration_events':len(cal_x),'test_events':sum(len(x) for x in test_x)})
            print(f'{representation} {name} fit {fit_s:.1f}s score {score_s:.1f}s',flush=True)
    result=pd.DataFrame(outcomes); assert len(result)==24
    assert all(result[result.session=='pooled'].events==11531)
    output.mkdir(parents=True,exist_ok=True)
    result.to_csv(output/'metrics.csv',index=False);pd.DataFrame(timing).to_csv(output/'timings.csv',index=False)
    manifest={'representations':2,'detectors':3,'sessions':len(sessions),'events':11531,
              'protocol_sha256':sha(ROOT/'docs/JOURNAL_V6_BASELINE_PROTOCOL.md'),
              'cache_manifest_sha256':sha(cache/'manifest.json'),'runner_sha256':sha(Path(__file__)),
              'limitations':['post-hoc same deployment','static only','default hyperparameters','ordinal distances arbitrary']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
