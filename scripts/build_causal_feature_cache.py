"""Cache label-free numeric histories once, with source and ordering checks."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_journal_temporal import load
from src.experiments.journal_protocol import ordered_unique
from src.experiments.behaviour_context import CausalHistory,BEHAVIOUR_FEATURES


def order_hash(rows):
    digest=hashlib.sha256()
    for row in rows:
        digest.update(str(row.get('eventID') or '').encode())
        digest.update(b'\0')
        digest.update(str(row['eventTime']).encode())
        digest.update(b'\n')
    return digest.hexdigest()


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out=ROOT/'results/journal_v4_causal_cache'
    if (out/'manifest.json').exists():raise FileExistsError('Preserve completed causal cache')
    out.mkdir(parents=True,exist_ok=True)
    data=ROOT/'data/external/cloud_log_sampling-main'
    base,duplicates=ordered_unique(load(data/'TrainOn/base_a.zip'))
    history=CausalHistory()
    values=history.transform(base)
    np.savez_compressed(out/'base.npz',features=values)
    manifest={'protocol':'v4-causal-cache-before-outcome','base_sha256':sha(data/'TrainOn/base_a.zip'),
              'base_duplicates_removed':duplicates,'feature_names':BEHAVIOUR_FEATURES,
              'base_order_sha256':order_hash(base),'base_events':len(base),'files':{},
              'history_code_sha256':sha(ROOT/'src/experiments/behaviour_context.py'),
              'contents':'numeric past-only features and record-order hashes; no raw actor keys or outcome labels'}
    seen={row['eventID'] for row in base}
    for archive in [data/'TestOn/labeled_cloudtrail_a.zip',data/'TrainOn/train_labeled_a.zip']:
        unique,_=ordered_unique(load(archive))
        if seen & {row['eventID'] for row in unique}:raise ValueError('Event overlap')
        seen.update(row['eventID'] for row in unique)
        future=[row for row in unique if row['eventTime']>base[-1]['eventTime']]
        for day in sorted({row['eventTime'][:10] for row in future}):
            session=archive.stem+'_'+day
            sequence=[row for row in future if row['eventTime'][:10]==day]
            values=history.clone().transform(sequence)
            filename=session+'.npz'
            np.savez_compressed(out/filename,features=values)
            manifest['files'][session]={'name':filename,'events':len(sequence),'order_sha256':order_hash(sequence),
                                        'sha256':sha(out/filename),'source_archive_sha256':sha(archive)}
            print(f'{session}: {len(sequence)} causally constructed rows',flush=True)
    manifest['base_feature_sha256']=sha(out/'base.npz')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
