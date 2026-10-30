"""Build a locally verified, raw-data-free reproducibility archive."""
from pathlib import Path
import hashlib
import json
import re
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'outputs/CloudTrail_Journal_Research_Evidence_v4.zip'
SIDECAR = ROOT / 'outputs/CloudTrail_Journal_Research_Evidence_v4.sha256.json'
if OUTPUT.exists() or SIDECAR.exists():
    raise FileExistsError('Preserve the existing evidence package; choose a new version')

files = set()
for folder in ('src', 'scripts', 'tests'):
    files.update(p for p in (ROOT / folder).rglob('*.py') if '__pycache__' not in p.parts)
for name in ('requirements.txt', 'requirements-journal.txt',
             'docs/REPRODUCIBILITY_V4.md', 'docs/JOURNAL_V4_PROTOCOL.md',
             'docs/PRIMARY_RICH_CONTEXT_PROTOCOL.md', 'docs/INDEPENDENT_SYNTHETIC_PROTOCOL.md',
             'docs/INDEPENDENT_CLOUD_DATA_AUDIT.md', 'docs/journal_paper_v4_source.md',
             'docs/journal_paper_v4.md', 'docs/journal_references.json',
             'outputs/SHAP_CloudTrail_Journal_Paper_v4.docx'):
    path = ROOT / name
    if not path.is_file():
        raise FileNotFoundError(path)
    files.add(path)

for folder in ('journal_v4_tiesafe_analysis', 'journal_v4_contamination',
               'journal_v4_primary_matched', 'journal_v4_primary_rich_context',
               'journal_v4_external_trace_replay', 'journal_v4_synthetic_independent'):
    files.update(p for p in (ROOT / 'results' / folder).rglob('*')
                 if p.is_file() and p.suffix in {'.csv', '.json'})
allow = {'manifest.json', 'summary.csv', 'window_counts.csv', 'decisions.csv',
         'signals.csv', 'scenario_counts.csv', 'static_event_scores.csv', 'calibration_signals.csv'}
cells = list((ROOT / 'results/journal_v4_tiesafe').glob('*/manifest.json'))
assert len(cells) == 60, f'Expected 60 finished cells, got {len(cells)}'
for manifest in cells:
    files.update(p for p in manifest.parent.iterdir() if p.is_file() and p.name in allow)

entries = []
secret_pattern = re.compile(rb'AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')
for path in sorted(files):
    relative = path.relative_to(ROOT).as_posix()
    data = path.read_bytes()
    if path.suffix in {'.py', '.md', '.json', '.txt', '.csv'} and secret_pattern.search(data):
        raise ValueError(f'Potential secret in {relative}; inspect before packaging')
    entries.append({'path': relative, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})

inventory = {'description': 'Local research evidence; raw data and fitted models excluded',
             'configuration_count': len(cells), 'files': entries}
with ZipFile(OUTPUT, 'x', compression=ZIP_DEFLATED, compresslevel=6) as archive:
    for entry in entries:
        archive.write(ROOT / entry['path'], entry['path'])
    archive.writestr('EVIDENCE_MANIFEST.json', json.dumps(inventory, indent=2) + '\n')
with ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
    for entry in entries:
        assert hashlib.sha256(archive.read(entry['path'])).hexdigest() == entry['sha256']
digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
SIDECAR.write_text(json.dumps({'file': OUTPUT.name, 'sha256': digest, 'file_count': len(entries)}, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'file': str(OUTPUT), 'sha256': digest, 'file_count': len(entries),
                  'bytes': OUTPUT.stat().st_size}, indent=2))
