"""Bounded acquisition of inert public attack traces, never attack execution."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/external/splunk_cloudtrail_v4'
HEADERS={'User-Agent':'DriftDetection-Research/4.0','Accept':'application/vnd.github+json'}


def fetch(url,limit):
    with urlopen(Request(url,headers=HEADERS),timeout=35) as response:
        value=response.read(limit+1)
    if len(value)>limit:raise ValueError('Acquisition size cap exceeded')
    return value


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'acquisition_manifest.json').exists():
        print('Preserving completed external acquisition');return
    repo=json.loads(fetch('https://api.github.com/repos/splunk/attack_data',2_000_000))
    commit=json.loads(fetch('https://api.github.com/repos/splunk/attack_data/commits/'+repo['default_branch'],2_000_000))['sha']
    tree=json.loads(fetch(f'https://api.github.com/repos/splunk/attack_data/git/trees/{commit}?recursive=1',15_000_000))
    (OUT/'repository_tree.json').write_text(json.dumps(tree,indent=2),encoding='utf-8')
    files=[row for row in tree['tree'] if row['type']=='blob' and 'cloudtrail' in row['path'].lower()
           and row['path'].lower().endswith(('.json','.json.gz','.log','.log.gz','.csv'))
           and row.get('size',0)<=5_000_000]
    # Freeze a deterministic bounded selection before parsing any trace outcomes.
    selected=sorted(files,key=lambda row:row['path'])[:20]
    plan={'repository':'https://github.com/splunk/attack_data','commit':commit,'tree_truncated':tree.get('truncated'),
          'eligible_path_count':len(files),'selection':'first 20 lexicographic CloudTrail data paths under 5MB; no outcome selection',
          'selected':selected,'per_file_cap_bytes':5_000_000,'total_file_limit':20,
          'label_caveat':'Attack trace context is not a per-event malicious label; no external FPR claim.'}
    (OUT/'selection_plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    licence=fetch(f'https://raw.githubusercontent.com/splunk/attack_data/{commit}/LICENSE',100_000)
    (OUT/'SOURCE_LICENSE.txt').write_bytes(licence)
    records=[]
    for row in selected:
        path=row['path'];item={'source_path':path,'git_blob_sha':row['sha']}
        try:
            url=f'https://raw.githubusercontent.com/splunk/attack_data/{commit}/'+quote(path,safe='/')
            content=fetch(url,5_000_000)
            if content.startswith(b'version https://git-lfs.github.com/spec/v1'):
                url=f'https://media.githubusercontent.com/media/splunk/attack_data/{commit}/'+quote(path,safe='/')
                content=fetch(url,5_000_000)
            digest=hashlib.sha256(content).hexdigest()
            destination=OUT/'traces'/(digest[:20]+'_'+Path(path).name)
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes(content)
            item.update(status='downloaded_data_only',path=str(destination.relative_to(ROOT)),
                        bytes=len(content),sha256=digest,url=url)
        except Exception as exc:item.update(status='failed',error=str(exc))
        records.append(item)
        print(f'{len(records)}/{len(selected)} {path}: {item["status"]}',flush=True)
    plan['downloads']=records
    plan['downloaded']=sum(row['status']=='downloaded_data_only' for row in records)
    (OUT/'acquisition_manifest.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'eligible_paths':len(files),'selected':len(selected),'downloaded':plan['downloaded']},indent=2))


if __name__=='__main__':main()
