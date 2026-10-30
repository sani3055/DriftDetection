"""Cross-environment, cold-start, unlabelled trace alert coverage; no FPR claims."""
import hashlib
import json
from pathlib import Path
import sys
import joblib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_journal_temporal import load
from src.experiments.behaviour_context import CausalHistory
from src.experiments.journal_comparison import EventEncoder


def event_key(row):
    if row.get('eventID'):return 'eventID:'+str(row['eventID'])
    return 'record:'+hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    folders=[ROOT/'data/external/splunk_cloudtrail_v4',ROOT/'data/external/splunk_cloudtrail_v4_extension']
    models=sorted((ROOT/'results/journal_v4_tiesafe').glob('*_s42/manifest.json'))
    if len(models)!=20:raise ValueError('Freeze and complete all 20 main settings before replay')
    commits=[json.loads((folder/'acquisition_manifest.json').read_text(encoding='utf-8'))['commit'] for folder in folders]
    if len(set(commits))!=1:raise ValueError('External source revisions differ')
    data=ROOT/'data/external/cloud_log_sampling-main'
    source_ids=set()
    for rel in ['TrainOn/base_a.zip','TestOn/labeled_cloudtrail_a.zip','TrainOn/train_labeled_a.zip']:
        source_ids.update(str(row['eventID']) for row in load(data/rel) if row.get('eventID'))
    seen=set();traces=[];audit=[];overlap=0
    for folder in folders:
        for trace in json.loads((folder/'native_traces.json').read_text(encoding='utf-8')):
            kept=[]
            for row in trace['records']:
                key=event_key(row)
                if key in seen:continue
                seen.add(key)
                if row.get('eventID') and str(row['eventID']) in source_ids:
                    overlap+=1;continue
                kept.append(row)
            kept.sort(key=lambda row:(pd.Timestamp(row['eventTime']),str(row.get('eventID') or '')))
            if not kept:continue
            try:
                # Enforce the same native event schema for every model mode.
                EventEncoder.frame(kept)
                # Separate trace cold start: no future-dated model-training history.
                context=CausalHistory().transform(kept)
                traces.append((trace['source_path'],kept,context))
                audit.append({'source_path':trace['source_path'],'events':len(kept),'status':'included_unlabelled'})
            except Exception as exc:
                audit.append({'source_path':trace['source_path'],'events':len(kept),'status':'incompatible','reason':str(exc)})
    outputs=[];summary=[]
    for manifest in models:
        bundle=joblib.load(manifest.parent/'frozen_detector.joblib')
        encoder,model,cutoff=bundle['encoder'],bundle['model'],float(bundle['cutoff'])
        results=[]
        for source,records,context in traces:
            try:
                matrix=encoder.transform(records,context)
                score=-model.score_samples(matrix)
                alarms=int((score>cutoff).sum())
                result={'configuration':manifest.parent.name,'source_path':source,'events':len(records),
                        'alarms':alarms,'any_alarm':int(alarms>0),'alert_fraction':alarms/len(records)}
                results.append(result);outputs.append(result)
            except Exception as exc:
                audit.append({'configuration':manifest.parent.name,'source_path':source,'status':'model_incompatible','reason':str(exc)})
        if len(results)!=len(traces):
            raise ValueError(f'Model-specific schema mismatch in {manifest.parent.name}; do not compare unequal trace sets')
        total=sum(row['events'] for row in results)
        summary.append({'configuration':manifest.parent.name,'compatible_traces':len(results),'events':total,
                        'traces_with_any_alarm':sum(row['any_alarm'] for row in results),
                        'alarms':sum(row['alarms'] for row in results),
                        'event_alarm_fraction':sum(row['alarms'] for row in results)/total if total else None,
                        'meaning':'unlabelled trace alarm coverage, not attack recall or benign FPR'})
    out=ROOT/'results/journal_v4_external_trace_replay'
    if (out/'manifest.json').exists():raise FileExistsError('Preserve completed replay')
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(outputs).to_csv(out/'per_trace.csv',index=False)
    pd.DataFrame(summary).to_csv(out/'summary.csv',index=False)
    record={'protocol':'frozen main models on independently acquired unlabelled CloudTrail traces',
            'source_commit':commits[0],'unique_included_traces':len(traces),
            'unique_included_events':sum(len(row[1]) for row in traces),'overlap_event_ids_excluded':overlap,
            'configuration_count':len(models),'audit':audit,
            'caveats':['No event-level security truth or verified benign controls',
                       'Trace name does not establish every record is malicious',
                       'Records without source event IDs cannot establish complete cross-source event disjointness',
                       'Cold actor history per trace differs from model development context',
                       'Some trace timestamps predate model training: retrospective cross-environment replay',
                       'Related scenarios from one curated repository are not independent production incidents']}
    (out/'manifest.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in record.items() if k!='audit'},indent=2))


if __name__=='__main__':main()
