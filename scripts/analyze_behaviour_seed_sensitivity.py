"""Audit all three declared forest seeds without selecting a favourable seed."""
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
manifests=sorted((ROOT/'results/journal_v4_tiesafe').glob('*/manifest.json'))
if len(manifests)!=60:raise ValueError(f'All sixty declared configurations are required; found {len(manifests)}')
rows=[];checks=[]
for path in manifests:
    meta=json.loads(path.read_text(encoding='utf-8'))
    for rel,expected in meta['code_sha256'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected,(path,rel)
    part=meta['partitions']
    assert all(a['last']<b['first'] for a,b in zip(part,part[1:]))
    summary=pd.read_csv(path.parent/'summary.csv')
    pooled=summary[summary.session=='pooled'].copy()
    assert len(pooled)==14 and ((pooled.tp+pooled.fn)==3126).all()
    assert ((pooled.tp+pooled.fp+pooled.tn+pooled.fn)==11531).all()
    for key,value in meta['parameters'].items():pooled[key]=value
    pooled['configuration']=path.parent.name
    rows.append(pooled);checks.append({'configuration':path.parent.name,'integrity':'passed'})
data=pd.concat(rows,ignore_index=True)
out=ROOT/'results/journal_v4_tiesafe_analysis'
data.to_csv(out/'all_seed_results.csv',index=False)
keys=['inputs','encoding','coverage','event_cutoff','policy']
grouped=data.groupby(keys,dropna=False)
assert grouped.size().eq(3).all()
ranges=grouped[['recall','false_positive_rate','f1']].agg(['min','max']).reset_index()
ranges.columns=['_'.join(str(p) for p in name if p) for name in ranges.columns]
ranges.to_csv(out/'seed_ranges.csv',index=False)
keys=['inputs','encoding','coverage','event_cutoff','seed']
dual=data[data.policy=='dual_signal'].set_index(keys)
coupled=data[data.policy=='coupled_signal'].set_index(keys)
assert dual.index.equals(coupled.index)
contrast=dual.index.to_frame(index=False)
for metric in ['recall','false_positive_rate','f1']:
    contrast['coupled_minus_dual_'+metric]=(coupled[metric]-dual[metric]).to_numpy()
contrast.to_csv(out/'seed_coupling_contrasts.csv',index=False)
(out/'seed_integrity_checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'configurations':len(manifests),'policy_configurations':len(data),
                  'matched_coupling_seed_cells':len(contrast),'integrity':'passed'},indent=2))
