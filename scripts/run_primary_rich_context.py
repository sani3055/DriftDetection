"""Unlabelled chronological feasibility study on the inherited richer export."""
from pathlib import Path
import hashlib
import json
import sys
from time import perf_counter
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.experiments.behaviour_context import CausalHistory
from src.experiments.behaviour_monitor import MixedEncoder,MixedMonitor
from src.experiments.journal_comparison import score_cutoff
from scripts.run_behaviour_tie_safe import requested

COLS=['eventID','eventTime','sourceIPAddress','userAgent','eventName','eventSource','awsRegion',
      'userIdentitytype','userIdentityaccountId','userIdentityprincipalId','userIdentityarn',
      'errorCode','requestParametersinstanceType']
POLICIES=['feature_only','shap_only','dual_signal','coupled_signal','score_wasserstein']


def file_hash(path):
    with path.open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def convert(row):
    return {'eventID':row['eventID'],'eventTime':row['eventTime'],'eventName':row['eventName'],
        'eventSource':row['eventSource'],'awsRegion':row['awsRegion'],'sourceIPAddress':row['sourceIPAddress'],
        'userAgent':row['userAgent'],'userIdentity':{'type':row['userIdentitytype'],
        'accountId':row['userIdentityaccountId'],'principalId':row['userIdentityprincipalId'],
        'arn':row['userIdentityarn']},'errorCode':row['errorCode'],
        'requestParameters':{'instanceType':row['requestParametersinstanceType']}}


def deduplicate_sample(frame):
    ids=frame.eventID.str.strip()
    if ids.str.lower().isin(['','nan','none','null','unknown']).any():
        raise ValueError('Missing or placeholder event identifiers need explicit resolution')
    duplicates=frame[ids.duplicated(keep=False)]
    if len(duplicates.drop_duplicates(subset=COLS))!=duplicates.eventID.nunique():
        raise ValueError('Repeated identifiers disagree on selected analysis fields')
    unique=frame.drop_duplicates(subset=['eventID'],keep='first').copy()
    return unique,len(frame)-len(unique)


def main():
    path=Path('D:/Projects/CloudGuard/data/nineteenFeaturesDf.csv')
    out=ROOT/'results/journal_v4_primary_rich_context'
    if (out/'manifest.json').exists():raise FileExistsError('Preserve completed result')
    if not path.is_file():raise FileNotFoundError('The inherited timestamped source is unavailable')
    out.mkdir(parents=True,exist_ok=True)
    start=perf_counter()
    split=json.loads((ROOT/'data/processed/temporal_split.json').read_text())
    months=split['train']+split['validation']+split['test']
    remaining={month:1000 for month in months};selected=[];read_rows=0
    for chunk in pd.read_csv(path,usecols=COLS,dtype=str,keep_default_na=False,chunksize=100000):
        read_rows+=len(chunk)
        chunk['_month']=chunk.eventTime.str.slice(0,7)
        for month,group in chunk.groupby('_month',sort=False):
            if month in remaining and remaining[month]>0:
                take=group.head(remaining[month]);selected.append(take);remaining[month]-=len(take)
        if not any(remaining.values()):break
    frame,duplicate_ids_removed=deduplicate_sample(pd.concat(selected,ignore_index=True))
    frame=frame.sort_values(['eventTime','eventID'],kind='stable').reset_index(drop=True)
    records=[convert(row) for row in frame.to_dict('records')]
    behaviour=CausalHistory().transform(records)
    train_positions=np.where(frame._month.isin(split['train']))[0]
    boundary=records[train_positions[int(.8*len(train_positions))]]['eventTime']
    fitting=np.array([i for i in train_positions if records[i]['eventTime']<boundary],dtype=int)
    reference=np.array([i for i in train_positions if records[i]['eventTime']>=boundary],dtype=int)
    if not len(fitting) or not len(reference):raise ValueError('Training tie boundary exhausted a partition')
    month_indices={month:np.where(frame._month.to_numpy()==month)[0] for month in months}
    if any(len(month_indices[month])==0 for month in months):raise ValueError('A required month has no source samples')
    take=lambda positions:[records[i] for i in positions]
    all_signals=[];model_info=[]
    for inputs,encoding in [('event','ordinal'),('behaviour','none'),('combined','ordinal')]:
        encoder=MixedEncoder(inputs,encoding).fit(take(fitting),behaviour[fitting])
        matrix=encoder.transform(take(fitting),behaviour[fitting])
        model=IsolationForest(n_estimators=100,contamination=.05,random_state=42,n_jobs=1).fit(matrix)
        monitor=MixedMonitor(model,encoder,take(reference),behaviour[reference])
        cal=[]
        for month in split['validation']:
            indices=month_indices[month]
            _,scores,signal=monitor.signals(take(indices),behaviour[indices])
            cal.append({'month':month,'events':len(indices),'scores':scores,'signal':signal})
        gates={name:float(np.quantile([row['signal'][name] for row in cal],.95,method='higher'))
               for name in ['feature_score','shap_score','coupling_score','score_wasserstein']}
        cal_matrix=np.vstack([encoder.transform(take(month_indices[m]),behaviour[month_indices[m]]) for m in split['validation']])
        cutoffs={mode:score_cutoff(model,cal_matrix,mode) for mode in ['training_offset','benign_quantile']}
        for period in ['validation','test']:
            for month in split[period]:
                indices=month_indices[month]
                _,scores,signal=monitor.signals(take(indices),behaviour[indices])
                all_signals.append({'inputs':inputs,'encoding':encoding,'split':period,'month':month,'events':len(indices),
                    'training_cutoff_alert_fraction':float((scores>cutoffs['training_offset']).mean()),
                    'validation_quantile_alert_fraction':float((scores>cutoffs['benign_quantile']).mean()),
                    **{f'{policy}_request':int(requested(policy,signal,gates,0)) for policy in POLICIES},**signal})
        model_info.append({'inputs':inputs,'encoding':encoding,'encoded_columns':encoder.width,
                           'gates':gates,'cutoffs':cutoffs,'max_shap_residual':monitor.max_residual})
        print(f'{inputs}: completed nine validation and nine test months',flush=True)
    pd.DataFrame(all_signals).to_csv(out/'monthly_observations.csv',index=False)
    digest=hashlib.sha256()
    for row in records:
        digest.update((row['eventID']+'\0'+row['eventTime']+'\n').encode())
    manifest={'protocol':'inherited-rich-context-unlabelled','source_sha256':file_hash(path),'source_size_bytes':path.stat().st_size,
        'source_rows_scanned':read_rows,'sample_rows':len(records),'duplicate_event_ids_removed':duplicate_ids_removed,
        'duplicate_check_scope':'selected analysis fields only; unselected fields were not read',
        'sample_counts_by_month':{month:len(month_indices[month]) for month in months},
        'sample_order_sha256':digest.hexdigest(),'selected_columns':COLS,'training_rows':len(fitting),'reference_rows':len(reference),
        'training_last_time':records[fitting[-1]]['eventTime'],'reference_first_time':records[reference[0]]['eventTime'],
        'feature_models':model_info,'wall_seconds':perf_counter()-start,
        'code_sha256':{str(p.relative_to(ROOT)):file_hash(p) for p in [Path(__file__),ROOT/'src/experiments/behaviour_context.py',ROOT/'src/experiments/behaviour_monitor.py']},
        'limitations':['No known attack labels or verified benign labels',
            'Source-order prefixes are not representative random samples and history reflects retained samples only',
            'Resource identities are not represented in this flattened export; access keys and raw identities are not stored',
            'Nine validation months yield a coarse maximum-like quantile gate',
            'Same inherited corpus, not an independent site; no actual model updates performed']}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'Primary rich context completed: {len(records)} sampled rows in {manifest["wall_seconds"]:.1f}s',flush=True)


if __name__=='__main__':main()
