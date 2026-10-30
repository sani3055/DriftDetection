"""Paired dependence-aware descriptive inference and representation failure audit."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.experiments.journal_comparison import moving_block_indices
from src.experiments.journal_protocol import ordered_unique,normalise,FEATURES
from scripts.run_journal_temporal import load


def metric_arrays(counts):
    tp,fp,tn,fn=counts.T
    def divide(a,b):return np.divide(a,b,out=np.full_like(a,np.nan,dtype=float),where=b!=0)
    return {'recall':divide(tp,tp+fn),'false_positive_rate':divide(fp,fp+tn),'f1':divide(2*tp,2*tp+fp+fn)}


def main():
    out=ROOT/'results/journal_v3_analysis'
    out.mkdir(parents=True,exist_ok=True)
    manifests=sorted((ROOT/'results/journal_v3').glob('*/manifest.json'))
    if len(manifests)!=20:raise ValueError(f'Expected all 20 settings, found {len(manifests)}')
    all_rows=[];gate_rows=[];paired=[];checks=[]
    for path in manifests:
        manifest=json.loads(path.read_text(encoding='utf-8'))
        params=manifest['parameters'];folder=path.parent
        assert pd.Timestamp(manifest['fit_last'])<pd.Timestamp(manifest['calibration_first'])
        assert pd.Timestamp(manifest['calibration_last'])<pd.Timestamp(manifest['guard_first'])
        assert all(pd.Timestamp(manifest['guard_last'])<pd.Timestamp(row['first_time']) for row in manifest['sessions'])
        for relative,digest in manifest['code_sha256'].items():
            assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest
        summary=pd.read_csv(folder/'summary.csv')
        pooled=summary[summary.session=='pooled'].copy()
        assert (pooled[['tp','fp','tn','fn']].sum(axis=1)==11531).all()
        assert (pooled.tp+pooled.fn==3126).all()
        assert (pooled.fp+pooled.tn==8405).all()
        pooled['configuration']=folder.name
        for name,value in params.items():pooled[name]=value
        all_rows.append(pooled)
        checks.append({'configuration':folder.name,'chronology_passed':True,'paired_totals_passed':True,
                       'code_hashes_passed':True,'grouped_shap_residual':manifest['max_grouped_shap_additivity_residual']})
        if params['seed']!=42 or params['window_size']!=128:continue
        calibration=pd.read_csv(folder/'calibration_signals.csv')
        signals=pd.read_csv(folder/'signals.csv')
        for name,frame in [('calibration',calibration),('attack_free_test',signals[signals.attack_events_evaluation_only==0]),
                           ('attack_containing_test',signals[signals.attack_events_evaluation_only>0])]:
            if not len(frame):continue
            gates=manifest['gates']
            feature=frame.feature_score>gates['feature_score']
            shap=frame.shap_score>gates['shap_score']
            coupled=feature&shap&(frame.coupling_score>gates['coupling_score'])
            gate_rows.append({'configuration':folder.name,'subset':name,'windows':len(frame),
                'coupling_q05':float(frame.coupling_score.quantile(.05)),
                'coupling_median':float(frame.coupling_score.median()),
                'coupling_q95':float(frame.coupling_score.quantile(.95)),
                'coupling_threshold':gates['coupling_score'],'feature_pass_rate':float(feature.mean()),
                'shap_pass_rate':float(shap.mean()),'dual_pass_rate':float((feature&shap).mean()),
                'coupled_pass_rate':float(coupled.mean()),
                'psi_effective_features_median':float(frame.psi_effective_features.median()),
                'attribution_effective_features_median':float(frame.attribution_effective_features.median())})
        labels=(signals.attack_events_evaluation_only>0).astype(int)
        gate_rows.append({'configuration':folder.name,'subset':'posthoc_window_discrimination',
            'coupling_auc':float(roc_auc_score(labels,signals.coupling_score)),
            'feature_auc':float(roc_auc_score(labels,signals.feature_score)),
            'shap_auc':float(roc_auc_score(labels,signals.shap_score)),
            'note':'Posthoc attack-containing-window discrimination, not runtime calibration or independent-incident inference'})
        counts=pd.read_csv(folder/'window_counts.csv')
        static=counts[counts.policy=='static'].sort_values(['session','window_index'])
        keys=static[['session','window_index']]
        sizes=static.groupby('session',sort=True).size().tolist()
        base=static[['tp','fp','tn','fn']].to_numpy(dtype=float)
        central={'dual_signal','coupled_signal','guarded_dual','adwin_score','page_hinkley_score','score_wasserstein'}
        for block in (2,5,10):
            rng=np.random.default_rng(20261030)
            indices=np.vstack([moving_block_indices(sizes,block,rng) for _ in range(2000)])
            base_resampled=metric_arrays(base[indices].sum(axis=1))
            base_point=metric_arrays(base.sum(axis=0,keepdims=True))
            for policy in sorted(set(counts.policy)-{'static'}):
                if block!=5 and policy not in central:continue
                selected=counts[counts.policy==policy].sort_values(['session','window_index'])
                assert selected[['session','window_index']].reset_index(drop=True).equals(keys.reset_index(drop=True))
                current=selected[['tp','fp','tn','fn']].to_numpy(dtype=float)
                points=metric_arrays(current.sum(axis=0,keepdims=True))
                samples=metric_arrays(current[indices].sum(axis=1))
                for metric in ['false_positive_rate','recall','f1']:
                    differences=samples[metric]-base_resampled[metric]
                    finite=differences[np.isfinite(differences)]
                    interval=np.quantile(finite,[.025,.975]) if len(finite) else [None,None]
                    paired.append({'configuration':folder.name,'policy':policy,'reference':'static',
                        'metric':metric,'difference':float(points[metric][0]-base_point[metric][0]),
                        'ci_low':interval[0],'ci_high':interval[1],'block_length':block,
                        'resamples':2000,'finite_resamples':len(finite),
                        'interpretation':'Exploratory session-stratified moving-block bootstrap within this corpus; no independent-site guarantee'})
    combined=pd.concat(all_rows,ignore_index=True)
    combined.to_csv(out/'all_factorial_results.csv',index=False)
    pd.DataFrame(gate_rows).to_csv(out/'gate_failure_analysis.csv',index=False)
    pd.DataFrame(paired).to_csv(out/'paired_block_intervals.csv',index=False)
    (out/'integrity_checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    # A labelled diagnostic ceiling on deterministic seven-feature classifiers,
    # never a fitted model, training target, or held-out performance claim.
    directory=ROOT/'data/external/cloud_log_sampling-main'
    benign,_=ordered_unique(load(directory/'TrainOn/base_a.zip'))
    cutoff=max(pd.Timestamp(row['eventTime']) for row in benign)
    records=[]
    for archive in [directory/'TestOn/labeled_cloudtrail_a.zip',directory/'TrainOn/train_labeled_a.zip']:
        part,_=ordered_unique(load(archive))
        records.extend(row for row in part if pd.Timestamp(row['eventTime'])>cutoff)
    profiles={}
    for row in records:
        normal=normalise(row)
        key=tuple(str(normal[name]) for name in FEATURES)
        counts=profiles.setdefault(key,[0,0])
        counts[int(bool(row.get('should_sample',False)))]+=1
    mixed=[v for v in profiles.values() if v[0] and v[1]]
    collision={'events':len(records),'unique_seven_feature_profiles':len(profiles),'mixed_label_profiles':len(mixed),
        'attack_events_in_mixed_profiles':sum(v[1] for v in mixed),'benign_events_in_mixed_profiles':sum(v[0] for v in mixed),
        'minimum_empirical_errors_of_deterministic_profile_classifier':sum(min(v) for v in profiles.values()),
        'scope':'Label-informed empirical feature-collision analysis, not trained/tested predictive accuracy or a population Bayes-error estimate'}
    (out/'feature_collision_diagnostic.json').write_text(json.dumps(collision,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'settings':len(manifests),'policy_configurations':len(combined),
                     'paired_intervals':len(paired),'collision_diagnostic':collision},indent=2),flush=True)


if __name__=='__main__':main()
