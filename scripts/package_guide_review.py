"""Package the guide-review draft with its checklist and saved summary evidence."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
output=ROOT/'outputs/CloudTrail_Guide_Review_Package.zip'
if output.exists(): raise FileExistsError('Preserve existing guide-review package')
items=[
 'outputs/CloudTrail_Journal_Manuscript_Guide_Review_Final.docx',
 'docs/GUIDE_REVIEW_AND_SUBMISSION_CHECKLIST.md',
 'docs/JOURNAL_V6_BASELINE_PROTOCOL.md',
 'docs/JOURNAL_V5_SAFETY_PROTOCOL.md',
 'docs/JOURNAL_V5_SAFETY_FINDINGS.md',
 'docs/INDEPENDENT_LABELLED_SYNTHETIC_PROTOCOL.md',
 'docs/INDEPENDENT_LABELLED_SYNTHETIC_FINDINGS.md',
 'results/journal_v6_static_baselines/metrics.csv',
 'results/journal_v6_static_baselines/timings.csv',
 'results/journal_v6_static_baselines/manifest.json',
 'results/journal_v5_labelled_generic/summary.csv',
 'results/journal_v5_labelled_generic/scenarios.csv',
 'results/journal_v5_labelled_generic/manifest.json',
 'results/journal_v5_safety_analysis/descriptive_summary.csv',
 'results/journal_v5_safety_analysis/paired_against_v4.csv',
 'results/journal_v5_safety_analysis/manifest.json',
 'scripts/run_static_detector_baselines.py',
 'scripts/run_candidate_safety_stress.py',
 'scripts/replay_labelled_generic_synthetic.py',
 'src/experiments/candidate_safety.py',
 'src/experiments/generic_cloud_adapter.py',
 'outputs/CloudTrail_Journal_Research_Evidence_v4.zip',
]
entries=[]
for name in items:
    path=ROOT/name
    if not path.is_file(): raise FileNotFoundError(path)
    entries.append({'path':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
with ZipFile(output,'x',compression=ZIP_DEFLATED,compresslevel=6) as z:
    for item in entries:z.write(ROOT/item['path'],item['path'])
    z.writestr('PACKAGE_MANIFEST.json',json.dumps({'files':entries},indent=2)+'\n')
with ZipFile(output) as z:
    assert z.testzip() is None
    for item in entries:assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
print(f'{output} ({output.stat().st_size} bytes; {len(entries)} files)')
