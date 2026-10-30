"""Audit the complete main grid and retain paired, non-independent contrasts."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score,roc_auc_score

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.experiments.journal_comparison import moving_block_indices


def rates(values):
    tp,fp,tn,fn=values[...,0],values[...,1],values[...,2],values[...,3]
    def divide(a,b):return np.divide(a,b,out=np.full_like(a,np.nan,dtype=float),where=b!=0)
    return {'recall':divide(tp,tp+fn),'false_positive_rate':divide(fp,fp+tn),'f1':divide(2*tp,2*tp+fp+fn)}


def main():
    manifests=sorted((ROOT/'results/journal_v4_tiesafe').glob('*_s42/manifest.json'))
    if len(manifests)!=20:raise ValueError(f'All twenty main cells required, found {len(manifests)}')
    out=ROOT/'results/journal_v4_tiesafe_analysis';out.mkdir(exist_ok=True)
    all_results=[];integrity=[];intervals=[];ranking=[]
    contrasts=[('coupled_signal','dual_signal'),('guarded_coupled','guarded_dual'),
               ('delayed_guarded_coupled','delayed_guarded_dual'),('guarded_dual','dual_signal'),
               ('delayed_guarded_dual','guarded_dual'),('coupled_signal','static'),('dual_signal','static')]
    for path in manifests:
        meta=json.loads(path.read_text(encoding='utf-8'));name=path.parent.name
        part=meta['partitions']
        assert all(a['last']<b['first'] for a,b in zip(part,part[1:])),name
        assert all(part[-1]['last']<session['first_time'] for session in meta['sessions']),name
        for rel,digest in meta['code_sha256'].items():
            assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,(name,rel)
        summary=pd.read_csv(path.parent/'summary.csv')
        pooled=summary[summary.session=='pooled'].copy()
        assert len(pooled)==14
        assert ((pooled.tp+pooled.fn)==3126).all()
        assert ((pooled.tp+pooled.fp+pooled.tn+pooled.fn)==11531).all()
        pooled['configuration']=name
        for key,value in meta['parameters'].items():pooled[key]=value
        all_results.append(pooled)
        scores=pd.read_csv(path.parent/'static_event_scores.csv')
        ranking.append({'configuration':name,**meta['parameters'],
                        'static_roc_auc':roc_auc_score(scores.label_evaluation_only,scores.score),
                        'static_average_precision':average_precision_score(scores.label_evaluation_only,scores.score),
                        'scope':'posthoc score ranking on the same corpus, not independent validation'})
        counts=pd.read_csv(path.parent/'window_counts.csv').sort_values(['session','window_index','policy'])
        base=counts[counts.policy=='static'].sort_values(['session','window_index'])
        sizes=base.groupby('session',sort=True).size().tolist()
        keys=base[['session','window_index']].to_numpy().tolist()
        arrays={}
        for policy,group in counts.groupby('policy'):
            group=group.sort_values(['session','window_index'])
            assert group[['session','window_index']].to_numpy().tolist()==keys
            arrays[policy]=group[['tp','fp','tn','fn']].to_numpy()
        for length in (2,5,10):
            rng=np.random.default_rng(20261030)
            index=np.stack([moving_block_indices(sizes,length,rng) for _ in range(2000)])
            draws={policy:rates(values[index].sum(axis=1)) for policy,values in arrays.items()}
            observed={policy:rates(values.sum(axis=0).astype(float)) for policy,values in arrays.items()}
            for policy,reference in contrasts:
                for endpoint in ('recall','false_positive_rate','f1'):
                    delta=draws[policy][endpoint]-draws[reference][endpoint]
                    finite=delta[np.isfinite(delta)]
                    lo,hi=np.quantile(finite,[.025,.975]) if len(finite) else (np.nan,np.nan)
                    intervals.append({'configuration':name,'policy':policy,'reference':reference,'endpoint':endpoint,
                        'difference':float(observed[policy][endpoint]-observed[reference][endpoint]),
                        'ci_low':lo,'ci_high':hi,'block_length':length,'resamples':2000,'finite_resamples':len(finite),
                        'interpretation':'descriptive paired within-corpus moving-block intervals, no population guarantee'})
        integrity.append({'configuration':name,'chronology_passed':True,'paired_totals_passed':True,
                          'code_hashes_passed':True,'grouped_shap_residual':meta['max_grouped_shap_residual']})
    results=pd.concat(all_results,ignore_index=True)
    results.to_csv(out/'all_main_results.csv',index=False)
    pd.DataFrame(ranking).to_csv(out/'static_ranking.csv',index=False)
    pd.DataFrame(intervals).to_csv(out/'paired_policy_intervals.csv',index=False)
    (out/'integrity_checks.json').write_text(json.dumps(integrity,indent=2)+'\n',encoding='utf-8')
    # Matched representation contrasts; no test-driven best-cell selection.
    comparisons=[]
    for (coverage,cutoff,encoding,policy),group in results[results.inputs.isin(['event','combined'])].groupby(
            ['coverage','event_cutoff','encoding','policy']):
        lookup=group.set_index('inputs')
        if not {'event','combined'}.issubset(lookup.index):continue
        comparisons.append({'coverage':coverage,'event_cutoff':cutoff,'encoding':encoding,'policy':policy,
            **{'combined_minus_event_'+key:float(lookup.loc['combined',key]-lookup.loc['event',key])
               for key in ['recall','false_positive_rate','f1']}})
    pd.DataFrame(comparisons).to_csv(out/'matched_input_contrasts.csv',index=False)
    print(json.dumps({'main_settings':len(manifests),'policy_configurations':len(results),
                      'integrity_checks':'passed','paired_intervals':len(intervals)},indent=2))


if __name__=='__main__':main()
