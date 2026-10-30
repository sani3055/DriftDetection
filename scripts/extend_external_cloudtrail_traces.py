"""Expand a frozen public source tree to remaining native-named trace files."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.acquire_external_cloudtrail_traces import fetch


def main():
    source=ROOT/'data/external/splunk_cloudtrail_v4'
    out=ROOT/'data/external/splunk_cloudtrail_v4_extension'
    out.mkdir(parents=True,exist_ok=True)
    if (out/'acquisition_manifest.json').exists():raise FileExistsError('Preserve extension acquisition')
    plan=json.loads((source/'selection_plan.json').read_text(encoding='utf-8'))
    tree=json.loads((source/'repository_tree.json').read_text(encoding='utf-8'))
    already={row['path'] for row in plan['selected']}
    selected=sorted([row for row in tree['tree'] if row['type']=='blob' and row['path'] not in already
        and 'cloudtrail' in row['path'].lower() and 'ocsf' not in row['path'].lower()
        and row['path'].lower().endswith(('.json','.json.gz','.log','.log.gz','.csv'))
        and row.get('size',0)<=5_000_000],key=lambda row:row['path'])
    manifest={'repository':plan['repository'],'commit':plan['commit'],'tree_truncated':plan['tree_truncated'],
        'selection':'all remaining CloudTrail-named native-format paths excluding OCSF under 5MB from the same frozen tree',
        'selected':selected,'per_file_cap_bytes':5_000_000,'label_caveat':plan['label_caveat'],
        'amendment':'Expanded coverage after source parsing and before external model outcome evaluation.'}
    (out/'selection_plan.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (out/'SOURCE_LICENSE.txt').write_bytes((source/'SOURCE_LICENSE.txt').read_bytes())
    (out/'traces').mkdir(exist_ok=True)
    def acquire(row):
        path=row['path'];result={'source_path':path,'git_blob_sha':row['sha']}
        try:
            url=f'https://raw.githubusercontent.com/splunk/attack_data/{plan["commit"]}/'+quote(path,safe='/')
            content=fetch(url,5_000_000)
            if content.startswith(b'version https://git-lfs.github.com/spec/v1'):
                url=f'https://media.githubusercontent.com/media/splunk/attack_data/{plan["commit"]}/'+quote(path,safe='/')
                content=fetch(url,5_000_000)
            digest=hashlib.sha256(content).hexdigest()
            destination=out/'traces'/(digest[:20]+'_'+Path(path).name)
            destination.write_bytes(content)
            result.update(status='downloaded_data_only',path=str(destination.relative_to(ROOT)),
                          bytes=len(content),sha256=digest,url=url)
        except Exception as exc:result.update(status='failed',error=str(exc))
        return result
    records=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(acquire,row) for row in selected]):
            records.append(future.result())
            print(f'{len(records)}/{len(selected)} {records[-1]["status"]}',flush=True)
    manifest['downloads']=sorted(records,key=lambda row:row['source_path'])
    manifest['downloaded']=sum(row['status']=='downloaded_data_only' for row in records)
    (out/'acquisition_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'selected':len(selected),'downloaded':manifest['downloaded']},indent=2))


if __name__=='__main__':main()
