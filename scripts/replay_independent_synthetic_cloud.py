"""Acquire inert published sample logs and replay frozen models; never run repo code."""
from datetime import datetime,timezone,timedelta
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
from urllib.request import Request,urlopen
import zipfile
import joblib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.experiments.behaviour_context import CausalHistory
from scripts.run_journal_temporal import load

OUT=ROOT/'data/external/trailhunt_synthetic_v4'
RESULT=ROOT/'results/journal_v4_synthetic_independent'
HEAD={'User-Agent':'DriftDetection-Research/4.0','Accept':'application/vnd.github+json'}


def fetch(url,cap):
    with urlopen(Request(url,headers=HEAD),timeout=45) as response:payload=response.read(cap+1)
    if len(payload)>cap:raise ValueError('Source exceeds fixed acquisition cap')
    return payload


def sanitise(row):
    identity=row.get('userIdentity') if isinstance(row.get('userIdentity'),dict) else {}
    session=identity.get('sessionContext') if isinstance(identity.get('sessionContext'),dict) else {}
    issuer=session.get('sessionIssuer') if isinstance(session.get('sessionIssuer'),dict) else {}
    request=row.get('requestParameters') if isinstance(row.get('requestParameters'),dict) else {}
    result={name:row.get(name) for name in ['eventID','eventTime','eventName','eventSource','awsRegion',
                                            'sourceIPAddress','userAgent','errorCode','readOnly']}
    result['userIdentity']={name:identity.get(name) for name in ['type','arn','principalId','accountId','invokedBy']}
    result['userIdentity']['sessionContext']={'sessionIssuer':{'arn':issuer.get('arn')}}
    result['requestParameters']={name:request.get(name) for name in ['bucketName','tableName','functionName','secretId',
        'roleArn','policyArn','resourceArn','trailName','instanceType']}
    raw_resources=row.get('resources') if isinstance(row.get('resources'),list) else []
    result['resources']=[{'ARN':entry.get('ARN') or entry.get('arn')} for entry in raw_resources if isinstance(entry,dict)]
    return result


def main():
    if (RESULT/'manifest.json').exists():raise FileExistsError('Preserve completed synthetic evaluation')
    model_paths=sorted((ROOT/'results/journal_v4_tiesafe').glob('*_s42/manifest.json'))
    if len(model_paths)!=20:raise ValueError('Freeze all 20 main models before evaluation')
    repo=json.loads(fetch('https://api.github.com/repos/Opsbreak/trailhunt',2_000_000))
    commit=json.loads(fetch('https://api.github.com/repos/Opsbreak/trailhunt/commits/'+repo['default_branch'],2_000_000))['sha']
    url=f'https://api.github.com/repos/Opsbreak/trailhunt/zipball/{commit}'
    archive_bytes=fetch(url,30_000_000)
    archive=zipfile.ZipFile(io.BytesIO(archive_bytes))
    names=sorted(n for n in archive.namelist() if '/examples/sample-logs/' in n and n.endswith('.json.gz'))
    if not 1<=len(names)<=2000:raise ValueError(f'Unexpected sample file count: {len(names)}')
    records=[];seen={};duplicates=0
    for name in names:
        info=archive.getinfo(name)
        if info.file_size>2_000_000:raise ValueError('Unexpected sample member size')
        with gzip.GzipFile(fileobj=io.BytesIO(archive.read(name))) as stream:payload=stream.read(5_000_001)
        if len(payload)>5_000_000:raise ValueError('Expanded sample member exceeds cap')
        data=json.loads(payload)
        for raw in data.get('Records',[]):
            row=sanitise(raw)
            if not row['eventID'] or not row['eventTime'] or not row['eventName']:raise ValueError('Missing core event fields')
            digest=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if row['eventID'] in seen:
                if seen[row['eventID']]!=digest:raise ValueError('Conflicting duplicate event ID')
                duplicates+=1;continue
            seen[row['eventID']]=digest;records.append(row)
    records.sort(key=lambda row:(pd.Timestamp(row['eventTime']),row['eventID']))
    times=pd.to_datetime([row['eventTime'] for row in records],utc=True)
    cutoff=pd.Timestamp('2026-09-08T00:00:00Z')
    background=np.asarray(times<cutoff)
    warm=np.asarray((times>=times[0]+pd.Timedelta(hours=24)) & (times<cutoff))
    starts=[pd.Timestamp(t) for t in ['2026-09-08T03:12:00Z','2026-09-09T01:47:00Z','2026-09-09T14:02:00Z']]
    windows=[np.asarray((times>=start)&(times<start+pd.Timedelta(minutes=15))) for start in starts]
    if not background.any() or not warm.any() or not all(window.any() for window in windows):
        raise ValueError('Sample does not match predeclared background and incident windows')
    if times[0]<pd.Timestamp('2026-09-01T00:00:00Z'):raise ValueError('Unexpected sample start date')
    data=ROOT/'data/external/cloud_log_sampling-main'
    source_ids={str(row['eventID']) for rel in ['TrainOn/base_a.zip','TestOn/labeled_cloudtrail_a.zip','TrainOn/train_labeled_a.zip']
                for row in load(data/rel) if row.get('eventID')}
    overlap=sum(row['eventID'] in source_ids for row in records)
    if overlap:raise ValueError('Unexpected event-ID overlap with the training/evaluation source')
    context=CausalHistory().transform(records)
    outputs=[];window_outputs=[]
    for path in model_paths:
        model_meta=json.loads(path.read_text(encoding='utf-8'))
        if pd.Timestamp(model_meta['partitions'][-1]['last'])>=times[0]:raise ValueError('Source does not follow model development')
        bundle=joblib.load(path.parent/'frozen_detector.joblib')
        matrix=bundle['encoder'].transform(records,context)
        alarms=(-bundle['model'].score_samples(matrix)>float(bundle['cutoff']))
        outputs.append({'configuration':path.parent.name,'total_events':len(records),
            'background_events':int(background.sum()),'background_alarms':int(alarms[background].sum()),
            'background_alarm_fraction':float(alarms[background].mean()),
            'post_warm_background_events':int(warm.sum()),'post_warm_background_alarms':int(alarms[warm].sum()),
            'post_warm_background_alarm_fraction':float(alarms[warm].mean()),
            'incident_windows_with_any_alarm':sum(bool(alarms[mask].any()) for mask in windows)})
        for index,mask in enumerate(windows):
            window_outputs.append({'configuration':path.parent.name,'incident_window':index+1,
                'start':starts[index].isoformat(),'events':int(mask.sum()),'alarms':int(alarms[mask].sum()),
                'any_alarm':bool(alarms[mask].any())})
    OUT.mkdir(parents=True,exist_ok=True);RESULT.mkdir(parents=True,exist_ok=True)
    licence=[n for n in archive.namelist() if n.count('/')==1 and n.endswith('/LICENSE')]
    if len(licence)!=1:raise ValueError('Expected one source licence file')
    (OUT/'SOURCE_LICENSE.txt').write_bytes(archive.read(licence[0]))
    with gzip.open(OUT/'sanitised_events.json.gz','wt',encoding='utf-8') as handle:
        json.dump(records,handle,separators=(',',':'))
    pd.DataFrame(outputs).to_csv(RESULT/'summary.csv',index=False)
    pd.DataFrame(window_outputs).to_csv(RESULT/'incident_windows.csv',index=False)
    manifest={'source_repository':'https://github.com/Opsbreak/trailhunt','source_commit':commit,'source_license':'MIT',
        'repository_archive_sha256':hashlib.sha256(archive_bytes).hexdigest(),'sample_files':len(names),
        'unique_events':len(records),'exact_duplicate_ids_removed':duplicates,'training_source_id_overlap':overlap,
        'first_event':times[0].isoformat(),'last_event':times[-1].isoformat(),
        'background_events':int(background.sum()),'post_warm_background_events':int(warm.sum()),
        'incident_window_event_counts':[int(mask.sum()) for mask in windows],'configurations':len(outputs),
        'sanitised_source_sha256':hashlib.sha256((OUT/'sanitised_events.json.gz').read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'label_interpretation':'Source-described synthetic benign days only; mixed incident windows do not label individual events',
        'limitations':['Synthetic single account; not production or independent incident populations',
          'A window alarm can originate from benign activity and is not confirmed attack recall',
          'Published simulator documentation defines the benign baseline and windows; event-level attack labels were not supplied',
          'Cold actor history in the synthetic environment may affect anomaly scores',
          'Twenty model cells are predeclared and share the same source events']}
    (RESULT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (OUT/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k!='limitations'},indent=2))


if __name__=='__main__':main()
