"""Future-only repaired counterfactual tests on the inherited monthly corpus."""
from copy import deepcopy
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
from src.experiments.journal_protocol import FEATURES,normalise,confusion,metrics
from src.experiments.journal_comparison import EventEncoder,FrozenMonitor,Deployed,scalar_thresholds,request_v3
from src.experiments.coherent_scenarios import SCENARIOS,coherent_perturbation

POLICIES=('static','periodic','feature_only','shap_only','dual_signal','coupled_signal',
          'conservative_coupled_signal','score_wasserstein')


def reconstruct(frame,category_maps):
    inverses={key:{int(v):k for k,v in mapping.items()} for key,mapping in category_maps.items()}
    result=[]
    for _,row in frame.iterrows():
        value={name:inverses.get(name,{}).get(int(row[name]),'__UNSEEN_SAVED_CATEGORY__') for name in FEATURES[:-1]}
        identity={'type':value['userIdentitytype']}
        if int(row['isRoot']):identity['arn']='derived:root'
        record={'eventName':value['eventName'],'eventSource':value['eventSource'],'awsRegion':value['awsRegion'],
                'userIdentity':identity,'errorCode':value['errorCode'],
                'requestParameters':{'instanceType':value['requestParametersinstanceType']}}
        if int(normalise(record)['isRoot'])!=int(row['isRoot']):
            raise ValueError('Source root flag inconsistent with decoded identity')
        result.append(record)
    return result


def main():
    out=ROOT/'results/journal_v3_primary_coherent'
    if (out/'manifest.json').is_file():raise FileExistsError('Preserve completed controlled evidence')
    out.mkdir(parents=True,exist_ok=True)
    started=perf_counter()
    path=ROOT/'data/scores/event_score_sample.csv'
    frame=pd.read_csv(path)
    contract=joblib.load(ROOT/'models/isolation_forest_event_baseline.joblib')
    split=json.loads((ROOT/'data/processed/temporal_split.json').read_text())
    train=frame[frame.window_id.isin(split['train'])].sort_values(['window_id','row_index_within_stream'])
    training_records=reconstruct(train,contract['category_maps'])
    encoder=EventEncoder('ordinal').fit(training_records)
    x_train=encoder.transform(training_records)
    model=IsolationForest(n_estimators=100,contamination=.05,random_state=42,n_jobs=1).fit(x_train)
    baseline=Deployed(model,-model.offset_)
    reference_indices=np.linspace(0,len(training_records)-1,200,dtype=int)
    monitor=FrozenMonitor(model,encoder,[training_records[i] for i in reference_indices])
    monthly={month:reconstruct(frame[frame.window_id==month].sort_values('row_index_within_stream'),contract['category_maps'])
             for month in split['validation']+split['test']}
    calibration=[]
    for month in split['validation']:
        _,_,signal=monitor.signals(monthly[month])
        calibration.append({'month':month,**signal})
    thresholds=scalar_thresholds(calibration)
    pd.DataFrame(calibration).to_csv(out/'calibration_signals.csv',index=False)
    results=[];signals=[];unit=0
    months=split['test']
    for transition,(earlier,later) in enumerate(zip(months,months[1:])):
        for seed in (17,42,73):
            rng=np.random.default_rng(seed+1000*transition)
            a=rng.choice(len(monthly[earlier]),200,replace=False)
            b=rng.choice(len(monthly[later]),200,replace=False)
            monitor_base=[monthly[earlier][i] for i in a]
            future_base=[monthly[later][i] for i in b]
            for intensity in (.125,.25):
                for scenario in SCENARIOS:
                    current,changed=coherent_perturbation(monitor_base,scenario,intensity,
                        np.random.default_rng(seed+1000*transition))
                    future,mask=coherent_perturbation(future_base,scenario,intensity,
                        np.random.default_rng(seed+1000*transition+100000))
                    matrix,scores,signal=monitor.signals(current)
                    future_matrix=encoder.transform(future)
                    requests={policy:request_v3(policy,signal,thresholds,unit) for policy in POLICIES}
                    candidate_mask=scores<=baseline.cutoff
                    candidate_count=int(candidate_mask.sum())
                    candidate=None
                    if any(requests.values()) and candidate_count>=10:
                        refit=IsolationForest(**model.get_params()).fit(np.vstack([x_train,matrix[candidate_mask]]))
                        candidate=Deployed(refit,-refit.offset_)
                    # Neither future rows nor their masks enter reference, gates, fitting or candidate screening.
                    before=baseline.predict(future_matrix)
                    after=candidate.predict(future_matrix) if candidate is not None else before
                    target=mask.astype(int) if scenario.startswith('security_') else np.zeros(len(mask),dtype=int)
                    metadata={'unit':unit,'transition':f'{earlier}__{later}','monitor_month':earlier,'future_month':later,
                        'seed':seed,'intensity':intensity,'scenario':scenario,'monitor_changed_rows':int(changed.sum()),
                        'future_changed_rows':int(mask.sum()),'positive_targets':int(target.sum())}
                    signals.append({**metadata,**signal})
                    for policy in POLICIES:
                        adapted=requests[policy] and candidate is not None
                        prediction=after if adapted else before
                        results.append({**metadata,'policy':policy,'request':int(requests[policy]),
                            'refit':int(adapted),'candidates':candidate_count if requests[policy] else 0,
                            **confusion(target,prediction)})
                    unit+=1
        print(f'Controlled transition {earlier} -> {later} complete ({unit} units)',flush=True)
    pd.DataFrame(signals).to_csv(out/'signals.csv',index=False)
    counts=pd.DataFrame(results)
    counts.to_csv(out/'paired_future_counts.csv',index=False)
    summaries=[]
    for policy,group in counts.groupby('policy',sort=True):
        values={name:int(group[name].sum()) for name in ['tp','fp','tn','fn']}
        summaries.append({'policy':policy,**values,**metrics(values),'requests':int(group.request.sum()),'refits':int(group.refit.sum())})
    summary=pd.DataFrame(summaries)
    summary.to_csv(out/'summary.csv',index=False)
    manifest={'protocol':'coherent-primary-future-window-counterfactual','fit_rows':len(training_records),
        'training_months':split['train'],'calibration_months':split['validation'],'test_months':split['test'],
        'units_per_policy':unit,'policies':POLICIES,'seed':42,'scenario_seeds':[17,42,73],
        'intensities':[.125,.25],'sample_size':200,'model_parameters':model.get_params(),'gates':thresholds,
        'max_shap_additivity_residual':monitor.max_additivity_residual,
        'score_prefix_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'wall_seconds':perf_counter()-started,
        'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__),ROOT/'src/experiments/coherent_scenarios.py']},
        'limitations':['Targets are synthetic actual-change masks, not real attack labels',
            'Negative-class rate is a mask-relative proxy, not verified benign-event FPR',
            'Monthly prefixes are not representative reservoir samples; saved unknown codes cannot be decoded to distinct raw names',
            'Month-level chronology does not establish event/session order inside a month',
            'Shared months, seeds and scenarios do not constitute independent incidents',
            'No known-benign guard is available on this corpus; no guard-based security claim']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(summary.to_string(index=False),flush=True)
    print(f'Controlled benchmark saved in {manifest["wall_seconds"]:.1f}s',flush=True)


if __name__=='__main__':main()
