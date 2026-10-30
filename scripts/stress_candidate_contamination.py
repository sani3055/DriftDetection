"""Prespecified feature-matrix contamination stress, never deployable labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_journal_temporal import load
from scripts.build_causal_feature_cache import order_hash
from src.experiments.journal_protocol import ordered_unique,confusion,metrics
from src.experiments.behaviour_monitor import chronological_partitions
from src.experiments.journal_comparison import Deployed,score_cutoff,shadow_guard


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def controlled_indices(labels,size,fraction,seed):
    labels=np.asarray(labels,dtype=int)
    attack=np.where(labels==1)[0];benign=np.where(labels==0)[0]
    rng=np.random.default_rng(seed+size*1000)
    attack=rng.permutation(attack);benign=rng.permutation(benign)
    wanted=int(round(size*fraction))
    if wanted>len(attack) or size-wanted>len(benign):raise ValueError('Not enough labelled candidate events')
    selected=np.concatenate([attack[:wanted],benign[:size-wanted]])
    return rng.permutation(selected)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--inputs',choices=['event','behaviour','combined'],required=True)
    parser.add_argument('--encoding',choices=['ordinal','onehot','none'],required=True)
    args=parser.parse_args()
    name=f'{args.inputs}_{args.encoding}_narrow_training_offset_s42'
    modeldir=ROOT/'results/journal_v4_tiesafe'/name
    if not (modeldir/'manifest.json').exists():raise FileNotFoundError('The locked source model must finish first')
    out=ROOT/'results/journal_v4_contamination'/name
    if (out/'manifest.json').exists():raise FileExistsError('Preserve completed stress output')
    out.mkdir(parents=True,exist_ok=True)
    started=perf_counter()
    data=ROOT/'data/external/cloud_log_sampling-main';cache=ROOT/'results/journal_v4_causal_cache'
    cache_manifest=json.loads((cache/'manifest.json').read_text(encoding='utf-8'))
    source_model=json.loads((modeldir/'manifest.json').read_text(encoding='utf-8'))
    if source_model['causal_cache_manifest_sha256']!=sha(cache/'manifest.json'):raise ValueError('Cache hash mismatch')
    bundle=joblib.load(modeldir/'frozen_detector.joblib')
    model,encoder=bundle['model'],bundle['encoder']
    baseline=Deployed(model,float(bundle['cutoff']))
    base=ordered_unique(load(data/'TrainOn/base_a.zip'))[0]
    if order_hash(base)!=cache_manifest['base_order_sha256']:raise ValueError('Base order mismatch')
    behaviour=np.load(cache/'base.npz',allow_pickle=False)['features']
    fit_indices,_,cal_indices,guard_indices=chronological_partitions(base,'narrow')
    def matrix(indices):return encoder.transform([base[i] for i in indices],behaviour[indices])
    training,cal_x,guard_x=matrix(fit_indices),matrix(cal_indices),matrix(guard_indices)
    anchors=training[np.argsort(model.score_samples(training),kind='stable')[:max(1,int(np.ceil(.05*len(training))))]]
    def session(archive_name,day):
        archive=data/archive_name
        rows=ordered_unique(load(archive))[0]
        rows=[row for row in rows if row['eventTime']>base[-1]['eventTime'] and row['eventTime'][:10]==day]
        key=archive.stem+'_'+day;meta=cache_manifest['files'][key]
        if meta['order_sha256']!=order_hash(rows) or meta['sha256']!=sha(cache/meta['name']):raise ValueError('Session cache mismatch')
        features=np.load(cache/meta['name'],allow_pickle=False)['features']
        return rows,encoder.transform(rows,features)
    candidate_rows,candidate_x=session('TestOn/labeled_cloudtrail_a.zip','2026-04-04')
    future_rows,future_x=session('TrainOn/train_labeled_a.zip','2026-04-28')
    # These labels construct explicit experimental contamination conditions.
    # The model and guard see only feature matrices, never these labels.
    candidate_labels=np.array([int(bool(row.get('should_sample',False))) for row in candidate_rows])
    future_labels=np.array([int(bool(row.get('should_sample',False))) for row in future_rows])
    before=baseline.predict(future_x)
    outputs=[]
    for size in (200,2000):
        for fraction in (0,.01,.05,.10,.20):
            for seed in (17,42,73):
                positions=controlled_indices(candidate_labels,size,fraction,seed)
                pool=candidate_x[positions]
                screened=baseline.predict(pool)==0
                all_fit=IsolationForest(**model.get_params()).fit(np.vstack([training,pool]))
                all_model=Deployed(all_fit,score_cutoff(all_fit,cal_x,'training_offset'))
                screened_model=None;guard=None
                if screened.sum()>=10:
                    fit=IsolationForest(**model.get_params()).fit(np.vstack([training,pool[screened]]))
                    screened_model=Deployed(fit,score_cutoff(fit,cal_x,'training_offset'))
                    guard=shadow_guard(baseline,screened_model,guard_x,anchors)
                predictions={'static':before,'unfiltered_refit':all_model.predict(future_x),
                             'screened_refit':screened_model.predict(future_x) if screened_model else before,
                             'guarded_screened_refit':screened_model.predict(future_x) if guard and guard['guard_allowed'] else before}
                for policy,prediction in predictions.items():
                    counts=confusion(future_labels,prediction)
                    outputs.append({'configuration':name,'pool_size':size,'nominal_fraction':fraction,'seed':seed,
                        'policy':policy,'pool_attack_count':int(candidate_labels[positions].sum()),
                        'screened_count':int(screened.sum()),
                        'screened_attack_count_evaluation_only':int(candidate_labels[positions][screened].sum()),
                        'guard_allowed':bool(guard['guard_allowed']) if guard else None,**counts,**metrics(counts)})
        print(f'{name}: pool size {size} complete',flush=True)
    pd.DataFrame(outputs).to_csv(out/'conditions.csv',index=False)
    manifest={'configuration':name,'protocol':'v4-feature-matrix-injected-contamination',
              'conditions':30,'policy_rows':len(outputs),'candidate_day':'2026-04-04','evaluation_day':'2026-04-28',
              'source_model_manifest_sha256':sha(modeldir/'manifest.json'),'source_model_sha256':sha(modeldir/'frozen_detector.joblib'),
              'cache_manifest_sha256':sha(cache/'manifest.json'),'code_sha256':sha(Path(__file__)),
              'wall_seconds':perf_counter()-started,
              'limitations':['Pool ratios use source labels solely to construct controlled conditions',
                'Counterfactual matrices are not a naturally occurring poisoning stream',
                'Candidate and test histories come from the original sampled stream, not a simulated new timeline',
                'Seed repeats share the same deployment and are not independent incidents',
                'Historical guard acceptance is not proof of future attack retention']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Completed {name} stress in {manifest["wall_seconds"]:.1f}s',flush=True)


if __name__=='__main__':main()
