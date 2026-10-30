"""Versioned v4 behavioural ablations, prediction before update, no test-label tuning."""
from __future__ import annotations
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
import joblib
import numpy as np
import pandas as pd
from river import drift
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_journal_temporal import load
from src.experiments.behaviour_context import CausalHistory, BEHAVIOUR_FEATURES
from src.experiments.behaviour_monitor import MixedEncoder, MixedMonitor, chronological_partitions
from src.experiments.journal_comparison import Deployed, score_cutoff, shadow_guard
from src.experiments.journal_protocol import ordered_unique, confusion, metrics

POLICIES = ('static','periodic','feature_only','shap_only','dual_signal','coupled_signal',
            'score_wasserstein','adwin_score','page_hinkley_score','guarded_periodic',
            'guarded_dual','guarded_coupled','delayed_guarded_dual','delayed_guarded_coupled')


def requested(policy, signal, gates, index, adwin=False, ph=False):
    if policy == 'static': return False
    if policy in {'periodic','guarded_periodic'}: return (index + 1) % 5 == 0
    feature, attribution = signal['feature_score'] > gates['feature_score'], signal['shap_score'] > gates['shap_score']
    if policy == 'feature_only': return bool(feature)
    if policy == 'shap_only': return bool(attribution)
    if policy in {'dual_signal','guarded_dual','delayed_guarded_dual'}: return bool(feature and attribution)
    if policy in {'coupled_signal','guarded_coupled','delayed_guarded_coupled'}:
        return bool(feature and attribution and signal['coupling_score'] > gates['coupling_score'])
    if policy == 'score_wasserstein': return signal['score_wasserstein'] > gates['score_wasserstein']
    if policy == 'adwin_score': return bool(adwin)
    if policy == 'page_hinkley_score': return bool(ph)
    raise ValueError(policy)


def quarantined_release(pool, current_model, alarm_fraction, alarm_limit):
    """No labels: return row positions in the preceding-window candidate pool."""
    if pool is None: return np.array([],dtype=int), 'no_previous_pool'
    if alarm_fraction > alarm_limit: return np.array([],dtype=int), 'current_alarm_fraction'
    selected = np.where(current_model.predict(pool) == 0)[0]
    return selected, 'eligible' if len(selected) >= 10 else 'insufficient_retained_candidates'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs',choices=['event','behaviour','combined'],default='combined')
    parser.add_argument('--encoding',choices=['ordinal','onehot','none'],default='ordinal')
    parser.add_argument('--coverage',choices=['narrow','broad'],default='narrow')
    parser.add_argument('--event-cutoff',choices=['training_offset','benign_quantile'],default='training_offset')
    parser.add_argument('--seed',type=int,default=42)
    args = parser.parse_args()
    name = f'{args.inputs}_{args.encoding}_{args.coverage}_{args.event_cutoff}_s{args.seed}'
    out = ROOT / 'results/journal_v4' / name
    if (out/'manifest.json').exists(): raise FileExistsError('Preserve completed results')
    out.mkdir(parents=True,exist_ok=True)
    started = perf_counter()
    data = ROOT/'data/external/cloud_log_sampling-main'
    base, duplicates = ordered_unique(load(data/'TrainOn/base_a.zip'))
    if any(row.get('should_sample',False) for row in base): raise ValueError('Expected historical benign archive')
    parts = chronological_partitions(base,args.coverage)
    history = CausalHistory()
    behaviour = history.transform(base)
    fitting, reference, calibration, guard_rows = [[base[i] for i in part] for part in parts]
    fit_b, ref_b, cal_b, guard_b = [behaviour[part] for part in parts]
    encoder = MixedEncoder(args.inputs,args.encoding).fit(fitting,fit_b)
    training = encoder.transform(fitting,fit_b)
    cal_x, guard_x = encoder.transform(calibration,cal_b), encoder.transform(guard_rows,guard_b)
    model = IsolationForest(n_estimators=100,contamination=.05,random_state=args.seed,n_jobs=1).fit(training)
    baseline = Deployed(model,score_cutoff(model,cal_x,args.event_cutoff))
    anchors = training[np.argsort(model.score_samples(training),kind='stable')[:max(1,int(np.ceil(.05*len(training))))]]
    monitor = MixedMonitor(model,encoder,reference,ref_b)
    cal_signals = []
    for index,start in enumerate(range(0,len(calibration),128)):
        batch, vector = calibration[start:start+128],cal_b[start:start+128]
        _, scores, signal = monitor.signals(batch,vector)
        cal_signals.append({'window_index':index,'n_events':len(batch),
                            'alarm_fraction':float((scores>baseline.cutoff).mean()),**signal})
    gates = {key:float(np.quantile([row[key] for row in cal_signals],.95,method='higher'))
             for key in ['feature_score','shap_score','coupling_score','score_wasserstein']}
    alarm_limit = float(np.quantile([row['alarm_fraction'] for row in cal_signals],.95,method='higher'))
    pd.DataFrame(cal_signals).to_csv(out/'calibration_signals.csv',index=False)
    adwin, ph = drift.ADWIN(), drift.PageHinkley()
    for score in -model.score_samples(cal_x):
        adwin.update(float(np.clip(score,0,1))); ph.update(float(np.clip(score,0,1)))
    counts, actions, signals, event_scores, scenarios, sessions = [],[],[],[],[],[]
    seen_ids = {row['eventID'] for row in base}
    for archive in [data/'TestOn/labeled_cloudtrail_a.zip',data/'TrainOn/train_labeled_a.zip']:
        unique, _ = ordered_unique(load(archive))
        if seen_ids & {row['eventID'] for row in unique}: raise ValueError('Event overlap')
        seen_ids.update(row['eventID'] for row in unique)
        future = [row for row in unique if row['eventTime'] > base[-1]['eventTime']]
        for day in sorted({row['eventTime'][:10] for row in future}):
            session = archive.stem + '_' + day
            sequence = [row for row in future if row['eventTime'][:10] == day]
            test_b = history.clone().transform(sequence)
            deployed = {policy:baseline for policy in POLICIES}
            versions = {policy:0 for policy in POLICIES}
            stream_a, stream_p = deepcopy(adwin), deepcopy(ph)
            previous_pool = previous_labels = None
            for index,start in enumerate(range(0,len(sequence),128)):
                batch, vector = sequence[start:start+128],test_b[start:start+128]
                matrix, scores, signal = monitor.signals(batch,vector)
                # All predictions use states deployed before this batch's update.
                predictions = {id(value.model):value.predict(matrix) for value in deployed.values()}
                a_alarm = p_alarm = False
                for score in scores:
                    stream_a.update(float(np.clip(score,0,1))); stream_p.update(float(np.clip(score,0,1)))
                    a_alarm |= stream_a.drift_detected; p_alarm |= stream_p.drift_detected
                requests = {policy:requested(policy,signal,gates,index,a_alarm,p_alarm) for policy in POLICIES}
                normal = scores <= baseline.cutoff
                alarm_fraction = float((~normal).mean())
                candidates, guard_info, released = {},{},{}
                immediate = None
                if any(requests[p] for p in POLICIES if not p.startswith('delayed_')) and normal.sum() >= 10:
                    fit = IsolationForest(**model.get_params()).fit(np.vstack([training,matrix[normal]]))
                    immediate = Deployed(fit,score_cutoff(fit,cal_x,args.event_cutoff))
                    immediate_guard = shadow_guard(baseline,immediate,guard_x,anchors)
                for policy in POLICIES:
                    if not requests[policy]: continue
                    if policy.startswith('delayed_'):
                        positions, reason = quarantined_release(previous_pool,deployed[policy],alarm_fraction,alarm_limit)
                        released[policy] = (positions,reason)
                        if reason == 'eligible':
                            fit = IsolationForest(**model.get_params()).fit(np.vstack([training,previous_pool[positions]]))
                            candidates[policy] = Deployed(fit,score_cutoff(fit,cal_x,args.event_cutoff))
                            guard_info[policy] = shadow_guard(baseline,candidates[policy],guard_x,anchors)
                    elif immediate is not None:
                        candidates[policy], guard_info[policy] = immediate,immediate_guard
                # Runtime decisions are now fixed. Only evaluation below reads labels.
                labels = np.array([int(bool(row.get('should_sample',False))) for row in batch])
                names = np.array([str(row.get('attack_name') or 'benign') for row in batch])
                signals.append({'session':session,'window_index':index,'n_events':len(batch),
                                'attack_events_evaluation_only':int(labels.sum()),'alarm_fraction':alarm_fraction,**signal})
                for position,(row,score,label) in enumerate(zip(batch,scores,labels)):
                    event_scores.append({'session':session,'event_index':start+position,'score':float(score),
                                         'label_evaluation_only':int(label),'static_prediction':int(score>baseline.cutoff)})
                for policy in POLICIES:
                    prediction = predictions[id(deployed[policy].model)]
                    candidate = candidates.get(policy)
                    guarded = policy.startswith(('guarded_','delayed_'))
                    allowed = bool(candidate is not None and (not guarded or guard_info[policy]['guard_allowed']))
                    positions, reason = released.get(policy,(None,''))
                    if policy.startswith('delayed_'):
                        candidate_count = len(positions) if positions is not None else 0
                        attack_candidates = int(previous_labels[positions].sum()) if previous_labels is not None and positions is not None else 0
                    else:
                        candidate_count = int(normal.sum()) if requests[policy] else 0
                        attack_candidates = int(labels[normal].sum()) if requests[policy] else 0
                    counts.append({'session':session,'window_index':index,'policy':policy,
                                   'model_version_used':versions[policy],**confusion(labels,prediction)})
                    actions.append({'session':session,'window_index':index,'policy':policy,'request':int(requests[policy]),
                        'accepted_refit':int(allowed),'guard_rejected':int(candidate is not None and guarded and not allowed),
                        'deferred':int(requests[policy] and policy.startswith('delayed_') and reason != 'eligible'),
                        'defer_reason':reason,'candidate_rows':candidate_count,
                        'accepted_candidates':candidate_count if allowed else 0,
                        'accepted_attack_candidates_evaluation_only':attack_candidates if allowed else 0,
                        'has_future_window':int(start+128<len(sequence))})
                    for name_ in np.unique(names):
                        mask = names == name_
                        scenarios.append({'session':session,'policy':policy,'scenario_evaluation_only':name_,**confusion(labels[mask],prediction[mask])})
                    if allowed:
                        deployed[policy] = candidate; versions[policy] += 1
                previous_pool, previous_labels = matrix[normal].copy(), labels[normal].copy()
            sessions.append({'session':session,'first_time':sequence[0]['eventTime'],
                             'last_time':sequence[-1]['eventTime'],'events':len(sequence),'archive_sha256':sha(archive)})
            print(f'{name}: {session} complete',flush=True)
    outcomes, decisions = pd.DataFrame(counts),pd.DataFrame(actions)
    outcomes.to_csv(out/'window_counts.csv',index=False)
    decisions.to_csv(out/'decisions.csv',index=False)
    pd.DataFrame(signals).to_csv(out/'signals.csv',index=False)
    pd.DataFrame(event_scores).to_csv(out/'static_event_scores.csv',index=False)
    pd.DataFrame(scenarios).to_csv(out/'scenario_counts.csv',index=False)
    summaries = []
    for session in ['pooled',*outcomes.session.unique()]:
        for policy in POLICIES:
            part = outcomes[(outcomes.policy==policy) & ((outcomes.session==session) if session!='pooled' else True)]
            decisions_part = decisions[(decisions.policy==policy) & ((decisions.session==session) if session!='pooled' else True)]
            values = {key:int(part[key].sum()) for key in ['tp','fp','tn','fn']}
            summaries.append({'session':session,'policy':policy,**values,**metrics(values),
                              **{key:int(decisions_part[key].sum()) for key in ['request','accepted_refit','guard_rejected','deferred',
                                   'accepted_candidates','accepted_attack_candidates_evaluation_only']}})
    pd.DataFrame(summaries).to_csv(out/'summary.csv',index=False)
    joblib.dump({'model':model,'encoder':encoder,'cutoff':baseline.cutoff,'parameters':vars(args)},out/'frozen_detector.joblib')
    manifest = {'protocol':'journal-v4-causal-behaviour','parameters':vars(args),'created_utc':datetime.now(timezone.utc).isoformat(),
        'base_sha256':sha(data/'TrainOn/base_a.zip'),'base_duplicates_removed':duplicates,
        'partitions':[{'events':len(part),'first':base[part[0]]['eventTime'],'last':base[part[-1]]['eventTime']} for part in parts],
        'feature_names':encoder.features,'encoded_columns':encoder.width,'numeric_bins':{k:v.tolist() for k,v in monitor.edges.items()},
        'model_parameters':model.get_params(),'event_cutoff':baseline.cutoff,'gates':gates,'quarantine_alarm_limit':alarm_limit,
        'max_grouped_shap_residual':monitor.max_residual,'sessions':sessions,'wall_seconds':perf_counter()-started,
        'code_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/experiments/behaviour_context.py',ROOT/'src/experiments/behaviour_monitor.py']},
        'limitations':['Previously inspected single controlled deployment; not blind independent validation',
            'History describes retained records; source multiplicity is not used',
            'Actor grouping can combine sessions; missing context remains ambiguous',
            'Delay and historical guards do not guarantee future security or uncontaminated data',
            'Grouped signed SHAP is not coalition SHAP; timing shares candidate fits']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Completed {name} in {manifest["wall_seconds"]:.1f}s',flush=True)


if __name__ == '__main__': main()
