"""V4 repair of controlled calibration size and earlier-data event cutoffs."""
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
from scripts.run_primary_coherent import reconstruct, POLICIES
from src.experiments.journal_protocol import confusion,metrics
from src.experiments.journal_comparison import EventEncoder,FrozenMonitor,Deployed,scalar_thresholds,request_v3,score_cutoff
from src.experiments.coherent_scenarios import SCENARIOS,coherent_perturbation


def main():
    out=ROOT/'results/journal_v4_primary_matched'
    if (out/'manifest.json').exists():raise FileExistsError('Preserve controlled evidence')
    out.mkdir(parents=True,exist_ok=True)
    started=perf_counter()
    path=ROOT/'data/scores/event_score_sample.csv'
    frame=pd.read_csv(path)
    contract=joblib.load(ROOT/'models/isolation_forest_event_baseline.joblib')
    split=json.loads((ROOT/'data/processed/temporal_split.json').read_text())
    train=frame[frame.window_id.isin(split['train'])].sort_values(['window_id','row_index_within_stream'])
    records=reconstruct(train,contract['category_maps'])
    encoder=EventEncoder('ordinal').fit(records)
    training=encoder.transform(records)
    model=IsolationForest(n_estimators=100,contamination=.05,random_state=42,n_jobs=1).fit(training)
    monitor=FrozenMonitor(model,encoder,[records[i] for i in np.linspace(0,len(records)-1,200,dtype=int)])
    monthly={month:reconstruct(frame[frame.window_id==month].sort_values('row_index_within_stream'),contract['category_maps'])
             for month in split['validation']+split['test']}
    calibration=[]
    for month in split['validation']:
        for seed in (17,42,73):
            chosen=np.random.default_rng(seed).choice(len(monthly[month]),200,replace=False)
            _,_,signal=monitor.signals([monthly[month][i] for i in chosen])
            calibration.append({'month':month,'seed':seed,'n_events':200,**signal})
    gates=scalar_thresholds(calibration)
    cal_x=encoder.transform([row for month in split['validation'] for row in monthly[month]])
    modes=('training_offset','benign_quantile')
    baseline={mode:Deployed(model,score_cutoff(model,cal_x,mode)) for mode in modes}
    result=[];signals=[];unit=0
    for transition,(earlier,later) in enumerate(zip(split['test'],split['test'][1:])):
        for seed in (17,42,73):
            rng=np.random.default_rng(seed+1000*transition)
            current_base=[monthly[earlier][i] for i in rng.choice(len(monthly[earlier]),200,replace=False)]
            future_base=[monthly[later][i] for i in rng.choice(len(monthly[later]),200,replace=False)]
            for intensity in (.125,.25):
                for scenario in SCENARIOS:
                    current,changed=coherent_perturbation(current_base,scenario,intensity,np.random.default_rng(seed+1000*transition))
                    future,mask=coherent_perturbation(future_base,scenario,intensity,np.random.default_rng(seed+1000*transition+100000))
                    matrix,scores,signal=monitor.signals(current)
                    future_x=encoder.transform(future)
                    requests={policy:request_v3(policy,signal,gates,unit) for policy in POLICIES}
                    metadata={'unit':unit,'transition':earlier+'__'+later,'seed':seed,'intensity':intensity,'scenario':scenario,
                              'monitor_changed_rows':int(changed.sum()),'future_changed_rows':int(mask.sum())}
                    signals.append({**metadata,**signal})
                    for mode in modes:
                        candidate=None
                        selected=scores<=baseline[mode].cutoff
                        if any(requests.values()) and selected.sum()>=10:
                            fit=IsolationForest(**model.get_params()).fit(np.vstack([training,matrix[selected]]))
                            candidate=Deployed(fit,score_cutoff(fit,cal_x,mode))
                        before=baseline[mode].predict(future_x)
                        after=candidate.predict(future_x) if candidate is not None else before
                        # Future masks enter outcomes only; no fitting or gate input.
                        target=mask.astype(int) if scenario.startswith('security_') else np.zeros(len(mask),dtype=int)
                        for policy in POLICIES:
                            adapted=bool(requests[policy] and candidate is not None)
                            result.append({**metadata,'event_cutoff':mode,'policy':policy,'request':int(requests[policy]),
                                           'refit':int(adapted),**confusion(target,after if adapted else before)})
                    unit+=1
        print(f'{earlier} -> {later}: {unit} units in both cutoff conditions',flush=True)
    counts=pd.DataFrame(result)
    counts.to_csv(out/'paired_future_counts.csv',index=False)
    pd.DataFrame(calibration).to_csv(out/'calibration_signals.csv',index=False)
    pd.DataFrame(signals).to_csv(out/'signals.csv',index=False)
    summary=[]
    for (mode,policy),part in counts.groupby(['event_cutoff','policy']):
        values={key:int(part[key].sum()) for key in ['tp','fp','tn','fn']}
        summary.append({'event_cutoff':mode,'policy':policy,**values,**metrics(values),
                        'requests':int(part.request.sum()),'refits':int(part.refit.sum())})
    pd.DataFrame(summary).to_csv(out/'summary.csv',index=False)
    manifest={'protocol':'v4-size-matched-monthly-counterfactual','units_per_policy_per_cutoff':unit,
              'fit_rows':len(training),'calibration_units':len(calibration),'calibration_sample_size':200,
              'monitor_sample_size':200,'gates':gates,'event_cutoffs':{mode:value.cutoff for mode,value in baseline.items()},
              'max_shap_residual':monitor.max_additivity_residual,'wall_seconds':perf_counter()-started,
              'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                             [Path(__file__),ROOT/'src/experiments/coherent_scenarios.py',ROOT/'scripts/run_primary_coherent.py']},
              'limitations':['Targets are synthetic interventions, not verified attacks',
                   'Earlier validation scores are unlabelled, not known benign calibration',
                   'Prefix samples and repeated scenarios are dependent; FPR is a mask-relative proxy']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Completed size matched controls in {manifest["wall_seconds"]:.1f}s',flush=True)


if __name__=='__main__':main()
