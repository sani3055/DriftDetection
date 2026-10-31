"""Paired descriptive summaries for all declared candidate-filter conditions."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
source = ROOT/'results/journal_v5_safety_stress'
out = ROOT/'results/journal_v5_safety_analysis'
if (out/'manifest.json').exists():
    raise FileExistsError('Preserve existing completed analysis')
out.mkdir(parents=True, exist_ok=True)
manifests = sorted(source.glob('*/manifest.json'))
if len(manifests) != 5:
    raise ValueError(f'Need all five finished configurations; got {len(manifests)}')
all_rows, contrasts, evidence = [], [], {}
keys = ['configuration', 'pool_size', 'nominal_fraction', 'seed']
for manifest in manifests:
    name = manifest.parent.name
    new = pd.read_csv(manifest.parent/'conditions.csv')
    old_path = ROOT/'results/journal_v4_contamination'/name/'conditions.csv'
    old = pd.read_csv(old_path)
    assert len(new) == 120 and len(old) == 120
    assert not new.duplicated(keys+['policy']).any()
    base = old[old.policy == 'screened_refit'].set_index(keys)
    guard = old[old.policy == 'guarded_screened_refit'].set_index(keys)
    static = old[old.policy == 'static'].set_index(keys)
    assert len(base) == len(guard) == len(static) == 30
    for _, row in new.iterrows():
        key = tuple(row[k] for k in keys)
        reference = guard.loc[key] if row.policy.endswith('_guarded') else base.loc[key]
        normal = base.loc[key]
        assert row.selected_count <= normal.screened_count
        assert row.selected_attack_count_evaluation_only <= normal.screened_attack_count_evaluation_only
        old_accepted = (bool(reference.guard_allowed) if row.policy.endswith('_guarded')
                        else int(normal.screened_count) >= 10)
        if row.policy.endswith('_guarded') and int(normal.screened_count) < 10:
            old_accepted = False
        old_n = int(normal.screened_count) if old_accepted else 0
        old_attack = int(normal.screened_attack_count_evaluation_only) if old_accepted else 0
        contrast = {k: row[k] for k in keys}
        contrast.update({'policy': row.policy, 'selected_candidates': int(row.selected_count),
            'selected_attacks': int(row.selected_attack_count_evaluation_only),
            'old_screened_candidates': int(normal.screened_count),
            'old_screened_attacks': int(normal.screened_attack_count_evaluation_only),
            'accepted_candidates': int(row.accepted_candidates), 'accepted_attacks': int(row.accepted_attacks_evaluation_only),
            'old_accepted_candidates': old_n, 'old_accepted_attacks': old_attack,
            'accepted_refit': int(row.accepted_refit), 'old_accepted_refit': int(old_accepted),
            'delta_recall': row.recall-reference.recall,
            'delta_fpr': row.false_positive_rate-reference.false_positive_rate,
            'delta_f1': row.f1-reference.f1,
            'delta_recall_vs_static': row.recall-static.loc[key].recall,
            'delta_fpr_vs_static': row.false_positive_rate-static.loc[key].false_positive_rate})
        contrasts.append(contrast)
    all_rows.append(new)
    for path in (manifest, manifest.parent/'conditions.csv', old_path):
        evidence[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

rows = pd.concat(all_rows, ignore_index=True)
paired = pd.DataFrame(contrasts)
assert len(rows) == len(paired) == 600
paired['selected_benign'] = paired.selected_candidates-paired.selected_attacks
paired['old_screened_benign'] = paired.old_screened_candidates-paired.old_screened_attacks
grouped = paired.groupby(['configuration', 'policy', 'pool_size', 'nominal_fraction'], as_index=False).agg(
    n=('seed', 'size'), selected_candidates=('selected_candidates', 'mean'),
    selected_attacks=('selected_attacks', 'mean'), selected_benign=('selected_benign', 'mean'),
    old_screened_candidates=('old_screened_candidates', 'mean'), old_screened_attacks=('old_screened_attacks', 'mean'),
    accepted_candidates=('accepted_candidates', 'mean'), accepted_attacks=('accepted_attacks', 'mean'),
    old_accepted_candidates=('old_accepted_candidates', 'mean'), old_accepted_attacks=('old_accepted_attacks', 'mean'),
    accepted_refit=('accepted_refit', 'mean'), old_accepted_refit=('old_accepted_refit', 'mean'),
    delta_recall=('delta_recall', 'mean'), delta_fpr=('delta_fpr', 'mean'), delta_f1=('delta_f1', 'mean'))
for frame, filename in ((rows,'all_policy_outcomes.csv'),(paired,'paired_against_v4.csv'),(grouped,'descriptive_summary.csv')):
    frame.to_csv(out/filename,index=False)
meta={'configurations':len(manifests),'condition_count':150,'policy_rows':len(rows),
      'descriptive_only':True,'independent_environments':1,'evidence_sha256':evidence,
      'analysis_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(out/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:meta[k] for k in ['configurations','condition_count','policy_rows','independent_environments']},indent=2))


if __name__ == '__main__':
    pass
