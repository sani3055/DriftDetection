"""Frozen source models on independent, labelled, cloud-neutral synthetic events."""
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.experiments.behaviour_context import CausalHistory, timestamp
from src.experiments.generic_cloud_adapter import adapt_generic_event
from src.experiments.journal_protocol import confusion, metrics

COMMIT = '535a2bd48c74ffd1652af7d092ba95b0fcb660b8'
URL = f'https://raw.githubusercontent.com/katerina20/cloud-threat-anomaly-lab/{COMMIT}/datasets/demo.jsonl'
LICENSE = f'https://raw.githubusercontent.com/katerina20/cloud-threat-anomaly-lab/{COMMIT}/LICENSE'
HEADERS = {'User-Agent': 'CloudTrail-Research-Audit/1.0'}


def fetch(url, limit):
    with urlopen(Request(url, headers=HEADERS), timeout=45) as response:
        raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError('Source exceeds declared byte cap')
    return raw


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = ROOT/'results/journal_v5_labelled_generic'
    if (output/'manifest.json').exists():
        raise FileExistsError('Preserve completed evaluation')
    models = sorted((ROOT/'results/journal_v4_tiesafe').glob('*_s42/manifest.json'))
    if len(models) != 20:
        raise ValueError('All 20 fixed seed-42 source models are required')
    hashes = {p.parent.name: {'manifest_sha256': sha(p), 'model_sha256': sha(p.parent/'frozen_detector.joblib')}
              for p in models}
    data = fetch(URL, 2_000_000)
    license_bytes = fetch(LICENSE, 100_000)
    if b'Apache License' not in license_bytes:
        raise ValueError('Unexpected source licence')
    raw = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    if any(type(r.get('is_anomaly')) is not bool for r in raw):
        raise ValueError('Missing or non-boolean source label')
    if len({r.get('event_id') for r in raw}) != len(raw):
        raise ValueError('Duplicate source event identifiers')
    records = [adapt_generic_event(row) for row in raw]
    order = sorted(range(len(records)), key=lambda i: (timestamp(records[i]), records[i]['eventID']))
    records = [records[i] for i in order]
    # Labels and scenarios stay in a separate evaluation-only vector, never passed to an encoder.
    labels = np.array([int(raw[i]['is_anomaly']) for i in order])
    scenarios = np.array([str(raw[i].get('scenario', 'unknown')) for i in order])
    if len(records) != 801 or int(labels.sum()) != 14:
        raise ValueError('Pinned sample does not match the inspected published summary')
    context = CausalHistory().transform(records)
    summary, by_scenario = [], []
    for path in models:
        bundle = joblib.load(path.parent/'frozen_detector.joblib')
        matrix = bundle['encoder'].transform(records, context)
        scores = -bundle['model'].score_samples(matrix)
        predictions = (scores > float(bundle['cutoff'])).astype(int)
        counts = confusion(labels, predictions)
        summary.append({'configuration': path.parent.name, 'cutoff': float(bundle['cutoff']),
                        'events': len(records), **counts, **metrics(counts)})
        for scenario in sorted(set(scenarios)):
            mask = scenarios == scenario
            by_scenario.append({'configuration': path.parent.name, 'scenario_evaluation_only': scenario,
                                'events': int(mask.sum()), 'positive_labels': int(labels[mask].sum()),
                                'alerts': int(predictions[mask].sum())})
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(summary).to_csv(output/'summary.csv', index=False)
    pd.DataFrame(by_scenario).to_csv(output/'scenarios.csv', index=False)
    meta = {'source_url': URL, 'source_repository': 'https://github.com/katerina20/cloud-threat-anomaly-lab',
            'source_commit': COMMIT, 'source_license': 'Apache-2.0',
            'source_sha256': hashlib.sha256(data).hexdigest(),
            'source_license_sha256': hashlib.sha256(license_bytes).hexdigest(),
            'events': len(records), 'positive_synthetic_labels': int(labels.sum()),
            'negative_synthetic_labels': int((1-labels).sum()),
            'target_first': records[0]['eventTime'], 'target_last': records[-1]['eventTime'],
            'models': hashes, 'protocol_sha256': sha(ROOT/'docs/INDEPENDENT_LABELLED_SYNTHETIC_PROTOCOL.md'),
            'adapter_sha256': sha(ROOT/'src/experiments/generic_cloud_adapter.py'),
            'runner_sha256': sha(Path(__file__)),
            'limitations': ['Cloud-neutral synthetic schema, not real AWS CloudTrail',
                'Lossful adapter and missing fields; readOnly defaults to false',
                'Retrospective replay predates model training; not a future deployment',
                'Only fourteen labelled synthetic anomalies from one generator',
                'No target tuning, adaptation evaluation or production accuracy claim']}
    (output/'manifest.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'events':len(records), 'anomalies':int(labels.sum()), 'models':len(summary),
                      'target_start':records[0]['eventTime'], 'target_end':records[-1]['eventTime']}, indent=2))


if __name__ == '__main__':
    main()
