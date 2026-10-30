"""Run prespecified v3 controls; all outcome labels are accessed after decisions."""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from river import drift
import river

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_journal_temporal import load  # noqa: E402
from src.experiments.journal_protocol import ordered_unique, windows, confusion, metrics  # noqa: E402
from src.experiments.journal_comparison import (  # noqa: E402
    EventEncoder, FrozenMonitor, Deployed, V3_POLICIES, score_cutoff, shadow_guard,
    scalar_thresholds, request_v3,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--representation',choices=['ordinal','onehot'],default='ordinal')
    parser.add_argument('--event-cutoff',choices=['training_offset','benign_quantile'],default='training_offset')
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--window-size',type=int,default=128)
    args=parser.parse_args()
    output=ROOT/f'results/journal_v3/{args.representation}_{args.event_cutoff}_w{args.window_size}_s{args.seed}'
    if (output/'manifest.json').exists(): raise FileExistsError(f'Preserve completed result {output}')
    output.mkdir(parents=True,exist_ok=True)
    tick=perf_counter()
    base_dir=ROOT/'data/external/cloud_log_sampling-main'
    base_path=base_dir/'TrainOn/base_a.zip'
    base,removed=ordered_unique(load(base_path))
    if any(row.get('should_sample',False) for row in base): raise ValueError('Expected benign development archive')
    first_day=base[0]['eventTime'][:10]
    first=[row for row in base if row['eventTime'][:10]==first_day]
    boundary=pd.Timestamp(first[int(.7*len(first))]['eventTime'])
    fitting=[row for row in first if pd.Timestamp(row['eventTime'])<boundary]
    reference=[row for row in first if pd.Timestamp(row['eventTime'])>=boundary]
    subsequent=sorted({row['eventTime'][:10] for row in base if row['eventTime'][:10]>first_day})
    if len(subsequent)!=2: raise ValueError('Protocol expects two later benign days')
    calibration=[row for row in base if row['eventTime'][:10]==subsequent[0]]
    guard_rows=[row for row in base if row['eventTime'][:10]==subsequent[1]]
    encoder=EventEncoder(args.representation).fit(fitting)
    training,calibration_x,guard_x=(encoder.transform(part) for part in (fitting,calibration,guard_rows))
    model=IsolationForest(n_estimators=100,contamination=.05,random_state=args.seed,n_jobs=1)
    model.fit(training)
    baseline=Deployed(model,score_cutoff(model,calibration_x,args.event_cutoff))
    scores_fit=-model.score_samples(training)
    anchor_count=max(1,int(np.ceil(.05*len(training))))
    anchors=training[np.argsort(-scores_fit,kind='stable')[:anchor_count]]
    monitor=FrozenMonitor(model,encoder,reference)
    calibration_signals=[]
    for i,batch in enumerate(windows(calibration,args.window_size)):
        _,_,signal=monitor.signals(batch)
        calibration_signals.append({'window_index':i,'n_events':len(batch),**signal})
    thresholds=scalar_thresholds(calibration_signals)
    pd.DataFrame(calibration_signals).to_csv(output/'calibration_signals.csv',index=False)
    adwin=drift.ADWIN(delta=.002,clock=32,max_buckets=5,min_window_length=5,grace_period=10)
    ph=drift.PageHinkley(min_instances=30,delta=.005,threshold=50,alpha=.9999,mode='both')
    for score in -model.score_samples(calibration_x):
        adwin.update(float(np.clip(score,0,1)))
        ph.update(float(np.clip(score,0,1)))
    rows,decisions,signals,by_scenario=[],[],[],[]
    audits=[]
    all_ids={row['eventID'] for row in base}
    cutoff=max(pd.Timestamp(row['eventTime']) for row in base)
    labels_for_audit=[]
    for archive in [base_dir/'TestOn/labeled_cloudtrail_a.zip',base_dir/'TrainOn/train_labeled_a.zip']:
        unique,duplicates=ordered_unique(load(archive))
        if all_ids & {row['eventID'] for row in unique}: raise ValueError('Event-ID overlap')
        all_ids.update(row['eventID'] for row in unique)
        future=[row for row in unique if pd.Timestamp(row['eventTime'])>cutoff]
        for day in sorted({row['eventTime'][:10] for row in future}):
            session=f'{archive.stem}_{day}'
            sequence=[row for row in future if row['eventTime'][:10]==day]
            deployed={policy:baseline for policy in V3_POLICIES}
            versions={policy:0 for policy in V3_POLICIES}
            adwin_session,ph_session=deepcopy(adwin),deepcopy(ph)
            for index,batch in enumerate(windows(sequence,args.window_size)):
                signal_tick=perf_counter()
                matrix,frozen_scores,signal=monitor.signals(batch)
                signal_seconds=perf_counter()-signal_tick
                unique_models={id(state.model):state for state in deployed.values()}
                predicted={key:state.predict(matrix) for key,state in unique_models.items()}
                adwin_alarms=ph_alarms=0
                for score in frozen_scores:
                    adwin_session.update(float(np.clip(score,0,1)))
                    ph_session.update(float(np.clip(score,0,1)))
                    adwin_alarms+=int(adwin_session.drift_detected)
                    ph_alarms+=int(ph_session.drift_detected)
                requests={policy:request_v3(policy,signal,thresholds,index,adwin_alarms>0,ph_alarms>0)
                          for policy in V3_POLICIES}
                candidate_mask=frozen_scores<=baseline.cutoff
                candidate_count=int(candidate_mask.sum())
                candidate=None
                guard_values={'guard_allowed':False,'baseline_guard_alarm_rate':None,
                              'candidate_guard_alarm_rate':None,'baseline_anchor_score':None,'candidate_anchor_score':None}
                fit_seconds=0.0
                if any(requests.values()) and candidate_count>=10:
                    fit_tick=perf_counter()
                    refit=IsolationForest(**model.get_params())
                    refit.fit(np.vstack([training,matrix[candidate_mask]]))
                    candidate=Deployed(refit,score_cutoff(refit,calibration_x,args.event_cutoff))
                    guard_values=shadow_guard(baseline,candidate,guard_x,anchors)
                    fit_seconds=perf_counter()-fit_tick
                # All runtime decisions fixed: only now access held-out outcome labels.
                labels=np.asarray([int(bool(row.get('should_sample',False))) for row in batch])
                names=np.asarray([str(row.get('attack_name') or 'benign') for row in batch])
                labels_for_audit.extend(labels.tolist())
                signal.update({'session':session,'window_index':index,'n_events':len(batch),
                    'first_time':batch[0]['eventTime'],'last_time':batch[-1]['eventTime'],
                    'attack_events_evaluation_only':int(labels.sum()),'adwin_alarms':adwin_alarms,'ph_alarms':ph_alarms,
                    'signal_seconds':signal_seconds})
                signals.append(signal)
                for policy in V3_POLICIES:
                    prediction=predicted[id(deployed[policy].model)]
                    accepted=(requests[policy] and candidate is not None and
                              (not policy.startswith('guarded_') or guard_values['guard_allowed']))
                    rows.append({'session':session,'window_index':index,'policy':policy,'n_events':len(batch),
                                 'model_version_used':versions[policy],**confusion(labels,prediction)})
                    decisions.append({'session':session,'window_index':index,'policy':policy,'request':int(requests[policy]),
                        'accepted_refit':int(accepted),'guard_rejected':int(requests[policy] and candidate is not None and
                            policy.startswith('guarded_') and not guard_values['guard_allowed']),
                        'candidates':candidate_count if requests[policy] else 0,
                        'attack_candidates_evaluation_only':int(labels[candidate_mask].sum()) if requests[policy] else 0,
                        'attack_events_evaluation_only':int(labels.sum()),
                        'has_future_window':int(index<(len(sequence)-1)//args.window_size),
                        'fit_work_seconds':fit_seconds if requests[policy] else 0.0,**guard_values})
                    for name in np.unique(names):
                        mask=names==name
                        by_scenario.append({'session':session,'window_index':index,'policy':policy,
                                            'scenario_evaluation_only':name,**confusion(labels[mask],prediction[mask])})
                    if accepted:
                        deployed[policy]=candidate
                        versions[policy]+=1
                if index%20==0: print(f'{output.name}: {session} batch {index+1}',flush=True)
            audits.append({'session':session,'archive':str(archive.relative_to(ROOT)),'sha256':sha(archive),
                'events':len(sequence),'duplicates_removed_from_archive':duplicates,
                'first_time':sequence[0]['eventTime'],'last_time':sequence[-1]['eventTime']})
    result=pd.DataFrame(rows)
    decision=pd.DataFrame(decisions)
    pd.DataFrame(signals).to_csv(output/'signals.csv',index=False)
    result.to_csv(output/'window_counts.csv',index=False)
    decision.to_csv(output/'decisions.csv',index=False)
    pd.DataFrame(by_scenario).to_csv(output/'scenario_counts.csv',index=False)
    summaries=[]
    for session in ['pooled',*result.session.unique()]:
        for policy in V3_POLICIES:
            selected=result[(result.policy==policy)&((result.session==session) if session!='pooled' else True)]
            actions=decision[(decision.policy==policy)&((decision.session==session) if session!='pooled' else True)]
            counts={name:int(selected[name].sum()) for name in ['tp','fp','tn','fn']}
            summaries.append({'session':session,'policy':policy,**counts,**metrics(counts),
                'requests':int(actions.request.sum()),'accepted_refits':int(actions.accepted_refit.sum()),
                'guard_rejections':int(actions.guard_rejected.sum()),
                'attack_free_window_requests':int(actions.loc[actions.attack_events_evaluation_only==0,'request'].sum()),
                'accepted_attack_candidates_evaluation_only':int(actions.loc[actions.accepted_refit==1,'attack_candidates_evaluation_only'].sum()),
                'accepted_candidates':int(actions.loc[actions.accepted_refit==1,'candidates'].sum())})
    summary=pd.DataFrame(summaries)
    summary.to_csv(output/'summary.csv',index=False)
    manifest={'protocol':'journal-v3-factorial-prequential','parameters':vars(args),'created_utc':datetime.now(timezone.utc).isoformat(),
        'base_sha256':sha(base_path),'base_duplicates_removed':removed,'fit_events':len(fitting),
        'reference_events':len(reference),'calibration_events':len(calibration),'guard_events':len(guard_rows),
        'fit_last':fitting[-1]['eventTime'],'calibration_first':calibration[0]['eventTime'],
        'calibration_last':calibration[-1]['eventTime'],'guard_first':guard_rows[0]['eventTime'],
        'guard_last':guard_rows[-1]['eventTime'],'encoded_columns':encoder.width,'model_parameters':model.get_params(),
        'category_vocabulary':encoder.maps,'event_score_cutoff':baseline.cutoff,'gates':thresholds,
        'max_grouped_shap_additivity_residual':monitor.max_additivity_residual,
        'river_version':river.__version__,'adwin_parameters':{'delta':.002,'clock':32,'max_buckets':5,'min_window_length':5,'grace_period':10},
        'ph_parameters':{'min_instances':30,'delta':.005,'threshold':50,'alpha':.9999,'mode':'both'},
        'guard_parameters':{'fpr_margin':.01,'anchor_score_margin':.02,'anchor_count':anchor_count},
        'sessions':audits,'events':len(labels_for_audit),'attacks_for_evaluation_only':sum(labels_for_audit),
        'wall_seconds':perf_counter()-tick,
        'code_sha256':{str(path.relative_to(ROOT)):sha(path) for path in
            [Path(__file__),ROOT/'src/experiments/journal_comparison.py']},
        'limitations':['Post-v2 development on a previously inspected deployment, not a blind independent corpus',
            'Session/date resets, sparse dates and shared events limit external generality',
            'Historical guard and fitting-data anchors do not prove future attack recall',
            'Grouped signed SHAP sums are not coalition/Owen SHAP values',
            'No event-label input to runtime gates; candidate contamination is audited after decisions',
            'Timing shares identical predictions/refits between policies; no independent throughput claim']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(summary[summary.session=='pooled'].to_string(index=False),flush=True)
    print(f'Saved {output} in {manifest["wall_seconds"]:.1f}s',flush=True)


if __name__=='__main__':main()
