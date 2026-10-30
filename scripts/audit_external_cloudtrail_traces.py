"""Parse inert traces, deduplicate events and disclose missing security labels."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/external/splunk_cloudtrail_v4'


def decode_objects(payload):
    if payload.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:payload=stream.read(20_000_001)
        if len(payload)>20_000_000:raise ValueError('Expanded size cap exceeded')
    text=payload.decode('utf-8-sig')
    decoder=json.JSONDecoder();position=0;objects=[]
    while position<len(text):
        while position<len(text) and text[position].isspace():position+=1
        if position==len(text):break
        value,end=decoder.raw_decode(text,position);objects.append(value);position=end
    return objects


def native_records(value):
    if isinstance(value,list):
        for row in value:yield from native_records(row)
    elif isinstance(value,dict):
        if value.get('eventTime') and value.get('eventName'):
            yield value
        elif isinstance(value.get('Records'),list):yield from native_records(value['Records'])
        elif '_raw' in value:
            raw=value['_raw']
            yield from native_records(json.loads(raw) if isinstance(raw,str) else raw)
        elif 'event' in value:
            raw=value['event']
            yield from native_records(json.loads(raw) if isinstance(raw,str) else raw)


def main():
    manifest=json.loads((OUT/'acquisition_manifest.json').read_text(encoding='utf-8'))
    audits=[];parsed=[];global_ids=set();global_hashes=set()
    for item in manifest['downloads']:
        audit={'source_path':item['source_path'],'status':item['status']}
        if item['status']!='downloaded_data_only':audits.append(audit);continue
        try:
            payload=(ROOT/item['path']).read_bytes()
            if hashlib.sha256(payload).hexdigest()!=item['sha256']:raise ValueError('Source hash mismatch')
            records=[record for value in decode_objects(payload) for record in native_records(value)]
            kept=[];duplicates=0;invalid=0
            for record in records:
                try:pd.Timestamp(record['eventTime'])
                except Exception:invalid+=1;continue
                identifier=str(record.get('eventID') or '')
                digest=hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                if (identifier and identifier in global_ids) or digest in global_hashes:
                    duplicates+=1;continue
                if identifier:global_ids.add(identifier)
                global_hashes.add(digest);kept.append(record)
            kept.sort(key=lambda row:(pd.Timestamp(row['eventTime']),str(row.get('eventID') or '')))
            audit.update(native_records=len(records),unique_native_records=len(kept),duplicates_removed=duplicates,
                         invalid_timestamps=invalid,earliest=kept[0]['eventTime'] if kept else None,
                         latest=kept[-1]['eventTime'] if kept else None,
                         identity_available=sum(bool(row.get('userIdentity')) for row in kept),
                         resources_available=sum(bool(row.get('resources')) for row in kept),
                         security_label_status='not established by trace filename or metadata',
                         native_schema_status='supported' if records else 'no_native_records_found')
            if kept:parsed.append({'source_path':item['source_path'],'records':kept})
        except Exception as exc:audit.update(parse_error=str(exc))
        audits.append(audit)
    (OUT/'native_traces.json').write_text(json.dumps(parsed,indent=2)+'\n',encoding='utf-8')
    report={'source_commit':manifest['commit'],'downloaded_files':manifest['downloaded'],
            'native_traces_with_unique_events':len(parsed),'unique_native_events':sum(len(row['records']) for row in parsed),
            'audits':audits,'per_event_attack_labels_available':False,
            'permitted_endpoints':['trace alert coverage','event alarm fraction on unlabelled traces'],
            'forbidden_claims':['external benign FPR','ground truth attack recall','future temporal validation across sources']}
    (OUT/'data_quality_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='audits'},indent=2))


if __name__=='__main__':main()
