"""Post-hoc matched historical-normality screening stress; not a deployment."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_causal_feature_cache import order_hash
from scripts.run_journal_temporal import load
from scripts.stress_candidate_contamination import controlled_indices, sha
from src.experiments.behaviour_monitor import chronological_partitions
from src.experiments.candidate_safety import historical_normal_mask, historical_score_threshold
from src.experiments.journal_comparison import Deployed, score_cutoff, shadow_guard
from src.experiments.journal_protocol import confusion, metrics, ordered_unique


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputs', choices=['event', 'behaviour', 'combined'], required=True)
    parser.add_argument('--encoding', choices=['ordinal', 'onehot', 'none'], required=True)
    args = parser.parse_args()
    name = f'{args.inputs}_{args.encoding}_narrow_training_offset_s42'
    modeldir = ROOT / 'results/journal_v4_tiesafe' / name
    out = ROOT / 'results/journal_v5_safety_stress' / name
    if (out / 'manifest.json').exists():
        raise FileExistsError('Preserve completed stress evidence')
    out.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    data = ROOT / 'data/external/cloud_log_sampling-main'
    cache = ROOT / 'results/journal_v4_causal_cache'
    cache_manifest = json.loads((cache / 'manifest.json').read_text(encoding='utf-8'))
    source = json.loads((modeldir / 'manifest.json').read_text(encoding='utf-8'))
    if source['causal_cache_manifest_sha256'] != sha(cache / 'manifest.json'):
        raise ValueError('Source model cache manifest mismatch')
    if cache_manifest['base_sha256'] != sha(data / 'TrainOn/base_a.zip'):
        raise ValueError('Source archive hash mismatch')
    if cache_manifest['base_feature_sha256'] != sha(cache / 'base.npz'):
        raise ValueError('Base feature hash mismatch')
    bundle = joblib.load(modeldir / 'frozen_detector.joblib')
    model, encoder = bundle['model'], bundle['encoder']
    baseline = Deployed(model, float(bundle['cutoff']))
    base = ordered_unique(load(data / 'TrainOn/base_a.zip'))[0]
    if order_hash(base) != cache_manifest['base_order_sha256']:
        raise ValueError('Base event order mismatch')
    behaviour = np.load(cache / 'base.npz', allow_pickle=False)['features']
    fit_indices, _, cal_indices, guard_indices = chronological_partitions(base, 'narrow')
    def matrix(indices):
        return encoder.transform([base[i] for i in indices], behaviour[indices])
    training, cal_x, guard_x = matrix(fit_indices), matrix(cal_indices), matrix(guard_indices)
    anchors = training[np.argsort(model.score_samples(training), kind='stable')[:max(1, int(np.ceil(.05 * len(training))))]]
    historical_scores = -model.score_samples(cal_x)
    thresholds = {q: historical_score_threshold(historical_scores, q) for q in (.25, .5)}

    def session(archive_name, day):
        archive = data / archive_name
        rows = ordered_unique(load(archive))[0]
        rows = [r for r in rows if r['eventTime'] > base[-1]['eventTime'] and r['eventTime'][:10] == day]
        meta = cache_manifest['files'][archive.stem + '_' + day]
        if (meta['order_sha256'] != order_hash(rows) or meta['sha256'] != sha(cache / meta['name'])
                or meta['source_archive_sha256'] != sha(archive)):
            raise ValueError('Session provenance mismatch')
        features = np.load(cache / meta['name'], allow_pickle=False)['features']
        return rows, encoder.transform(rows, features)

    candidate_rows, candidate_x = session('TestOn/labeled_cloudtrail_a.zip', '2026-04-04')
    future_rows, future_x = session('TrainOn/train_labeled_a.zip', '2026-04-28')
    labels = np.array([int(bool(r.get('should_sample', False))) for r in candidate_rows])
    future_labels = np.array([int(bool(r.get('should_sample', False))) for r in future_rows])
    static_predictions = baseline.predict(future_x)
    outputs = []
    for size in (200, 2000):
        for fraction in (0, .01, .05, .10, .20):
            for seed in (17, 42, 73):
                positions = controlled_indices(labels, size, fraction, seed)
                pool = candidate_x[positions]
                pool_labels = labels[positions]
                normal = baseline.predict(pool) == 0
                scores = -model.score_samples(pool)
                for q, threshold in thresholds.items():
                    selected = historical_normal_mask(scores, normal, threshold)
                    n = int(selected.sum())
                    attacks = int(pool_labels[selected].sum())
                    guard = None
                    candidate = None
                    if n >= 10:
                        fitted = IsolationForest(**model.get_params()).fit(np.vstack([training, pool[selected]]))
                        candidate = Deployed(fitted, score_cutoff(fitted, cal_x, 'training_offset'))
                        guard = shadow_guard(baseline, candidate, guard_x, anchors)
                    for guarded in (False, True):
                        accepted = candidate is not None and (not guarded or guard['guard_allowed'])
                        prediction = candidate.predict(future_x) if accepted else static_predictions
                        counts = confusion(future_labels, prediction)
                        outputs.append({'configuration': name, 'pool_size': size, 'nominal_fraction': fraction,
                            'seed': seed, 'policy': f'historical_q{int(q*100):02d}' + ('_guarded' if guarded else ''),
                            'historical_threshold': threshold, 'selected_count': n,
                            'selected_attack_count_evaluation_only': attacks,
                            'selected_benign_count_evaluation_only': n-attacks,
                            'guard_allowed': guard['guard_allowed'] if guard is not None else None,
                            'accepted_refit': int(accepted), 'accepted_candidates': n if accepted else 0,
                            'accepted_attacks_evaluation_only': attacks if accepted else 0,
                            **counts, **metrics(counts)})
        print(f'{name}: pool size {size} complete', flush=True)
    pd.DataFrame(outputs).to_csv(out / 'conditions.csv', index=False)
    manifest = {'configuration': name, 'protocol': 'post-hoc-v5-historical-normality-stress',
        'conditions': 30, 'policy_rows': len(outputs), 'thresholds': thresholds,
        'source_model_manifest_sha256': sha(modeldir/'manifest.json'),
        'source_model_sha256': sha(modeldir/'frozen_detector.joblib'),
        'cache_manifest_sha256': sha(cache/'manifest.json'),
        'protocol_sha256': sha(ROOT/'docs/JOURNAL_V5_SAFETY_PROTOCOL.md'),
        'screen_code_sha256': sha(ROOT/'src/experiments/candidate_safety.py'),
        'runner_code_sha256': sha(Path(__file__)), 'wall_seconds': perf_counter()-started,
        'limitations': ['Post-hoc thresholds and same previously inspected deployment',
            'Candidate labels construct controlled pools and audit outcomes only',
            'Feature matrices are not a chronological poisoning stream',
            'No independent population or safety guarantee']}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'{name}: completed in {manifest["wall_seconds"]:.1f}s', flush=True)


if __name__ == '__main__':
    main()
