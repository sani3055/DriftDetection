"""Build the v3 paper from versioned evidence without modifying old outputs."""
from pathlib import Path
import hashlib
import json

import build_journal_paper as b

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'tmp/journal_paper_v3/assets'
b.SOURCE = ROOT / 'docs/journal_paper_v3_source.md'
b.OUT = ROOT / 'outputs/SHAP_CloudTrail_Journal_Paper_v3.docx'
b.RESOLVED = ROOT / 'docs/journal_paper_v3.md'
b.AUDIT = ROOT / 'tmp/journal_paper_v3'
b.REFERENCES['lara'] = {
    'authors': 'Antonio Lara-Gutierrez, Carmen Fernandez-Gago and Jose A. Onieva',
    'title': 'A Framework for Drift Detection and Adaptation in AI-driven Anomaly and Threat Detection Systems',
    'venue': 'International Journal of Information Security', 'year': '2025',
    'volume': '24', 'pages': '199', 'url': 'https://doi.org/10.1007/s10207-025-01118-9'}
b.REFERENCES['river'] = {
    'authors': 'River contributors', 'title': 'ADWIN and PageHinkley API documentation',
    'venue': 'River documentation', 'year': '2026',
    'url': 'https://riverml.xyz/dev/api/drift/ADWIN/ ; https://riverml.xyz/dev/api/drift/PageHinkley/'}
b.REFERENCES['kunsch'] = {
    'authors': 'Hans R. Kunsch', 'title': 'The jackknife and the bootstrap for general stationary observations',
    'venue': 'The Annals of Statistics', 'year': '1989', 'volume': '17', 'issue': '3',
    'pages': '1217-1241', 'url': 'https://doi.org/10.1214/aos/1176347265'}

NAMES = {'static': 'Static', 'periodic': 'Periodic', 'feature_only': 'Feature only',
    'shap_only': 'SHAP only', 'dual_signal': 'Dual signal', 'coupled_signal': 'Coupled',
    'conservative_coupled_signal': 'Conservative coupled', 'score_wasserstein': 'Score Wasserstein',
    'adwin_score': 'ADWIN score', 'page_hinkley_score': 'Page Hinkley score',
    'guarded_dual': 'Guarded dual', 'guarded_feature': 'Guarded feature',
    'guarded_periodic': 'Guarded periodic'}


def rows(config):
    return {r['policy']: r for r in b.read_csv(f'results/journal_v3/{config}/summary.csv') if r['session'] == 'pooled'}


def build_table(key):
    if key == 'v3_design':
        b.table(key, 'Chronological data allocation', ['Partition', 'Events', 'Role'], [
            ['18 February fitting', '6,881', 'Learn vocabulary and initial detector'],
            ['18 February reference', '2,949', 'Frozen distributions and SHAP reference'],
            ['19 February calibration', '4,182', 'Event cutoff and monitoring gates'],
            ['20 February guard', '2,474', 'Candidate checks only'],
            ['April test sessions', '11,531', '3,126 attack and 8,405 benign events'],
        ], [1.65, .75, 4.1], 'Test sessions are 4, 27 and 28 April 2026. They originate from one controlled AWS deployment, not three independent sites. Timestamp ties are purged at the fitting boundary.')
    elif key == 'v3_controls':
        b.table(key, 'Declared comparison factors', ['Factor', 'Settings'], [
            ['Representation', 'Ordinal and one hot with training only vocabularies'],
            ['Event cutoff', 'Training offset and earlier benign 95th percentile'],
            ['Random seeds', '17, 42 and 73 at 128 events per window'],
            ['Window sensitivity', '64 and 256 events at seed 42'],
            ['Policies', '13 policies in every setting'],
            ['Total', '20 settings and 260 policy configurations'],
        ], [1.55, 4.95], 'The four representation by cutoff cells at seed 42 and 128 events are the main comparison. Sensitivity settings reuse the same events and cannot establish independent replication.')
    elif key.startswith('v3_cell_'):
        suffix = key.removeprefix('v3_cell_')
        config = suffix + '_w128_s42'
        data = rows(config)
        body = [[NAMES[k]] + [b.f4(data[k][c]) for c in ['recall', 'false_positive_rate', 'f1']]
                + [data[k]['requests'], data[k]['accepted_refits']] for k in NAMES]
        title = suffix.replace('onehot', 'one hot').replace('_', ' ')
        b.table(key, f'Future event results for {title}', ['Policy', 'Recall', 'FPR', 'F1', 'Requests', 'Refits'],
                body, [2.0, .9, .9, .9, .9, .9],
                'Rates pool confusion counts over the identical 11,531 events. Requests and accepted refits differ when candidates are insufficient or rejected. A terminal refit has no later observation in its session.')
    elif key == 'v3_intervals':
        source = b.read_csv('results/journal_v3_analysis/paired_block_intervals.csv')
        chosen = [r for r in source if r['configuration'] == 'ordinal_training_offset_w128_s42'
                  and r['block_length'] == '5' and r['policy'] in ['dual_signal', 'coupled_signal', 'adwin_score', 'guarded_dual']
                  and r['metric'] in ['recall', 'false_positive_rate']]
        body = [[NAMES[r['policy']], 'Recall' if r['metric'] == 'recall' else 'FPR', b.f4(r['difference']),
                 f"[{b.f4(r['ci_low'])}, {b.f4(r['ci_high'])}]"] for r in chosen]
        assert len(body) == 8
        b.table(key, 'Paired differences from static under ordinal training offset',
                ['Policy', 'Endpoint', 'Difference', 'Descriptive 95% interval'], body,
                [1.55, .8, 1.0, 3.15], 'Session stratified moving blocks of five windows, 2,000 paired resamples. Positive recall and negative FPR are favourable. These intervals describe resampling within this corpus and are not population guarantees. Block lengths two and ten are retained in the supplement.')
    elif key == 'v3_primary':
        source = {r['policy']: r for r in b.read_csv('results/journal_v3_primary_coherent/summary.csv')}
        b.table(key, 'Future month controlled intervention results',
                ['Policy', 'Mask recall', 'Mask FPR proxy', 'Pooled F1', 'Refits'],
                [[NAMES[k]] + [b.f4(source[k][c]) for c in ['recall', 'false_positive_rate', 'f1']]
                 + [source[k]['refits']] for k in list(NAMES)[:8]], [2.05, 1.05, 1.25, 1.15, 1.0],
                '336 counterfactual units per policy. Positive targets are actual changed rows in intended security scenarios. Unchanged rows are unlabelled background, so the negative class rate is not a verified benign event FPR. Scores are pooled across repeated counterfactual evaluations, not unique independent events.')
    elif key == 'v3_collision':
        r = b.read_json('results/journal_v3_analysis/feature_collision_diagnostic.json')
        keys = [('events', 'Evaluated events'), ('unique_seven_feature_profiles', 'Unique seven feature profiles'),
                ('mixed_label_profiles', 'Profiles with both labels'), ('attack_events_in_mixed_profiles', 'Attack events in mixed profiles'),
                ('benign_events_in_mixed_profiles', 'Benign events in mixed profiles'),
                ('minimum_empirical_errors_of_deterministic_profile_classifier', 'Minimum pooled errors for a fixed profile classifier')]
        b.table(key, 'Retrospective feature collision diagnostic', ['Quantity', 'Count'],
                [[label, f'{r[k]:,}'] for k, label in keys], [5.2, 1.3],
                'This diagnostic uses test labels after evaluation. The minimum applies to a single deterministic classifier of these seven fields on this pooled sample. It is not a learned classifier, a population Bayes error bound, or a bound on adaptive models using time or history.')
    else:
        raise KeyError(key)


old_equation = b.equation


def equation(key):
    if key not in {'feature', 'wasserstein', 'effective'}:
        return old_equation(key)
    b.equation_count += 1
    if key == 'feature':
        parts = [b.sub('F', 't'), ' = ', b.frac('1', '7'), b.summation('j = 1', '7', b.sub('d', 'j,t'))]
    elif key == 'wasserstein':
        parts = [b.sub('w', 'j,t'), ' = ', b.frac([b.sub('W', '1'), '(', b.sup(b.sub('Φ', 'j'), 'R'), ', ', b.sup(b.sub('Φ', 'j'), 't'), ')'],
                 ['max(', b.sup(b.sub('σ', 'j'), 'R'), ', s)'])]
    else:
        parts = [b.sub('N', 'eff'), '(v) = ', b.frac(b.sup(['(', b.summation('j = 1', '7', b.delimiter(b.sub('v', 'j'))), ')'], '2'),
                                                   b.summation('j = 1', '7', b.sup(b.sub('v', 'j'), '2')))]
    p = b.doc.add_paragraph()
    p.alignment = b.WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = b.Pt(5)
    p.paragraph_format.space_after = b.Pt(7)
    math = b.OxmlElement('m:oMath')
    b.append(math, parts)
    p._p.append(math)
    b.font(p.add_run(f'    ({b.equation_count})'), 10)
    b.resolved_blocks.append(f'[Editable equation {b.equation_count} {key}]')


def figure(key):
    settings = {
        'factorial': ('factorial_tradeoffs.png', 'Figure 1 Detection tradeoffs in the four main comparison cells. Each point is a policy; overlapping points share outcomes. A lower false positive rate is useful only in conjunction with adequate attack recall. All panels use the same events and scales.'),
        'alignment': ('alignment_overlap.png', 'Figure 2 Frozen cosine alignment by representation and window annotation. Calibration is earlier benign activity. Test windows are labelled attack free or attack containing only after runtime decisions. Dashed lines are the unchanged calibration gates. Overlap prevents interpreting alignment as a security probability.'),
    }
    filename, caption = settings[key]
    p = b.doc.add_paragraph()
    p.alignment = b.WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(str(ASSETS / filename), width=b.Inches(6.45))
    run._r.xpath('.//wp:docPr')[0].set('descr', caption)
    b.paragraph(caption, 'Caption')


if __name__ == '__main__':
    checks = b.read_json('results/journal_v3_analysis/integrity_checks.json')
    assert len(checks) == 20
    assert all(all(row[k] for k in ['chronology_passed', 'paired_totals_passed', 'code_hashes_passed']) for row in checks)
    original_table = b.table
    def table_together(*args, **kwargs):
        original_table(*args, **kwargs)
        current = b.doc.tables[-1]
        # Each v3 comparison fits a page; avoid an isolated final data row.
        for i, row in enumerate(current.rows):
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = i < len(current.rows) - 1
    b.table = table_together
    original_paragraph = b.paragraph
    def paragraph_with_urls(text, style=None, align=None):
        if 'https://' in text and style is None and align is None:
            align = b.WD_ALIGN_PARAGRAPH.LEFT
        return original_paragraph(text, style, align)
    b.paragraph = paragraph_with_urls
    original_references = b.add_references
    def references_together():
        first = len(b.doc.paragraphs)
        original_references()
        for p in b.doc.paragraphs[first:]:
            p.paragraph_format.keep_together = True
    b.add_references = references_together
    b.build_table, b.equation, b.figure = build_table, equation, figure
    b.doc.core_properties.title = 'Attribution Guided Adaptation in Cloud Audit Logs and Its Limits under Temporal Shift'
    b.main()
    audit_path = b.AUDIT / 'build_audit.json'
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    evidence = [*sorted((ROOT / 'results/journal_v3').glob('*/summary.csv')),
                *sorted((ROOT / 'results/journal_v3_analysis').glob('*.*')),
                ROOT / 'results/journal_v3_primary_coherent/summary.csv',
                ROOT / 'results/journal_v3_primary_coherent/manifest.json']
    audit['v3_evidence_hashes'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence}
    audit_path.write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
