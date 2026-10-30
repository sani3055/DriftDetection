"""Create a new versioned research paper from completed v4 evidence."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import build_journal_paper as b
import build_journal_v3 as v3

ROOT=Path(__file__).resolve().parents[1]
b.SOURCE=ROOT/'docs/journal_paper_v4_source.md'
b.OUT=ROOT/'outputs/SHAP_CloudTrail_Journal_Paper_v4.docx'
b.RESOLVED=ROOT/'docs/journal_paper_v4.md'
b.AUDIT=ROOT/'tmp/journal_paper_v4'
b.REFERENCES['adediran']={'authors':'Goodness Adediran, Kenny Awuson-David and Yussuf Ahmed',
 'title':'Retrieval-Augmented Large Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail Mitre ATT&CK Mapping',
 'venue':'Computers, Materials and Continua','year':'2026','volume':'87','issue':'2','pages':'100',
 'url':'https://doi.org/10.32604/cmc.2026.077606'}
b.REFERENCES['splunk']={'authors':'Splunk Security Research', 'title':'Attack Data repository',
 'venue':'GitHub repository','year':'2026','url':'https://github.com/splunk/attack_data'}
b.REFERENCES['trailhunt']={'authors':'Opsbreak', 'title':'Trailhunt synthetic CloudTrail sample and source repository',
 'venue':'GitHub repository','year':'2026','url':'https://github.com/Opsbreak/trailhunt'}

DATA=pd.read_csv(ROOT/'results/journal_v4_tiesafe_analysis/all_main_results.csv')
ITEMS=[('event','ordinal','Event ordinal'),('event','onehot','Event one hot'),
       ('behaviour','none','Behaviour'),('combined','ordinal','Combined ordinal'),('combined','onehot','Combined one hot')]


def select(inputs,encoding,coverage,cutoff,policy):
    found=DATA[(DATA.inputs==inputs)&(DATA.encoding==encoding)&(DATA.coverage==coverage)&
               (DATA.event_cutoff==cutoff)&(DATA.policy==policy)]
    if len(found)!=1:raise ValueError((inputs,encoding,coverage,cutoff,policy,len(found)))
    return found.iloc[0]


def triple(row):return '/'.join(f'{float(row[k]):.3f}' for k in ['recall','false_positive_rate','f1'])


def build_table(key):
    if key=='v4_split':
        cases=[]
        for coverage in ['narrow','broad']:
            path=ROOT/f'results/journal_v4_tiesafe/event_ordinal_{coverage}_training_offset_s42/manifest.json'
            item=json.loads(path.read_text(encoding='utf-8'))
            cases.append([coverage.title()]+[f"{entry['events']:,}" for entry in item['partitions']])
        b.table(key,'Historical chronological partitions',['Coverage','Fit','Reference','Calibration','Guard'],cases,
                [1.5,1.25,1.25,1.25,1.25],
                'All partitions use benign archive labels. Broad coverage uses chronological 70/10/10/10 boundaries with ties assigned to the later partition. Both splits precede the same April sessions.')
    elif key=='v4_main':
        rows=[]
        for inputs,encoding,name in ITEMS:
            values=[triple(select(inputs,encoding,'narrow','training_offset',policy))
                    for policy in ['static','dual_signal','coupled_signal']]
            rows.append([name,*values])
        b.table(key,'Main event outcomes under narrow history and training cutoff',
                ['Inputs','Static R/FPR/F1','Dual R/FPR/F1','Coupled R/FPR/F1'],rows,
                [1.65,1.62,1.62,1.61],
                'R is recall on attack-labelled events and FPR is the benign false-positive rate. Every policy predicts the same 11,531 events. Values are pooled and rounded to three decimals. Other declared splits and cutoffs are retained in Table 3 and supplementary results.')
    elif key=='v4_factorial':
        cells=[('narrow','training_offset'),('narrow','benign_quantile'),('broad','training_offset'),('broad','benign_quantile')]
        rows=[]
        for inputs,encoding,name in ITEMS:
            values=[]
            for coverage,cutoff in cells:
                values.append('/'.join(f"{select(inputs,encoding,coverage,cutoff,policy)['f1']:.3f}"
                                       for policy in ['static','dual_signal','coupled_signal']))
            rows.append([name,*values])
        b.table(key,'F1 across all twenty main input and calibration cells',
                ['Inputs','Narrow train','Narrow quantile','Broad train','Broad quantile'],rows,
                [1.55,1.24,1.24,1.24,1.23],
                'Each cell contains static / dual / coupled pooled F1 in that order. F1 alone cannot express the recall and false-positive tradeoff; all confusion counts are retained in the analysis data. The same source events are reused in every cell.')
    elif key=='v4_guard':
        rows=[]
        for inputs,encoding,name in ITEMS:
            values=[]
            for policy in ['dual_signal','guarded_dual','delayed_guarded_dual']:
                row=select(inputs,encoding,'narrow','training_offset',policy)
                values.append(f"{int(row['accepted_attack_candidates_evaluation_only'])} / {int(row['accepted_refit'])}")
            rows.append([name,*values])
        b.table(key,'Attack labelled accepted candidates and completed updates',
                ['Inputs','Dual','Guarded dual','Delayed guarded dual'],rows,[1.8,1.42,1.55,1.73],
                'Each entry is attack-labelled accepted candidate rows / completed refits. Labels were used only for the post-decision audit. Policies have different request counts, and a completed final-window refit may have no subsequent test window.')
    elif key=='v4_ci':
        data=pd.read_csv(ROOT/'results/journal_v4_tiesafe_analysis/paired_policy_intervals.csv')
        name='combined_ordinal_narrow_training_offset_s42'
        rows=[]
        for metric,label in [('recall','Recall'),('false_positive_rate','FPR'),('f1','F1')]:
            hit=data[(data.configuration==name)&(data.policy=='coupled_signal')&(data.reference=='dual_signal')&
                     (data.endpoint==metric)&(data.block_length==5)].iloc[0]
            rows.append([label,f"{hit['difference']:.4f}",f"[{hit['ci_low']:.4f}, {hit['ci_high']:.4f}]"])
        b.table(key,'Coupled minus dual in the combined ordinal main cell',
                ['Outcome','Difference','Descriptive paired 95% interval'],rows,[1.4,1.4,3.7],
                'Intervals use 2,000 session-stratified moving-block resamples at five windows, with the same paired indices. They describe this controlled corpus and are not population-level confidence guarantees. Length-two and length-ten sensitivity results are retained separately.')
    elif key=='v4_external':
        d=pd.read_csv(ROOT/'results/journal_v4_external_trace_replay/summary.csv').set_index('configuration')
        rows=[]
        for inputs,encoding,name in ITEMS:
            row=d.loc[f'{inputs}_{encoding}_narrow_training_offset_s42']
            rows.append([name,int(row['compatible_traces']),int(row['traces_with_any_alarm']),
                         int(row['events']),f"{row['event_alarm_fraction']:.3f}"])
        b.table(key,'Retrospective unlabelled cross-environment trace replay',
                ['Inputs','Traces','Traces with alerts','Events','Alarm fraction'],rows,[1.8,.85,1.35,1.0,1.5],
                'Static models only. A trace containing an attack scenario may also contain setup or benign actions. These are not attack recall, benign FPR or independent production incidents. Actor history starts cold for each trace.')
    elif key=='v4_synthetic':
        d=pd.read_csv(ROOT/'results/journal_v4_synthetic_independent/summary.csv').set_index('configuration')
        rows=[]
        for inputs,encoding,name in ITEMS:
            row=d.loc[f'{inputs}_{encoding}_narrow_training_offset_s42']
            rows.append([name,f"{row['background_alarm_fraction']:.3f}",
                         f"{row['post_warm_background_alarm_fraction']:.3f}",
                         f"{int(row['incident_windows_with_any_alarm'])} / 3"])
        b.table(key,'Independent synthetic background and mixed incident windows',
                ['Inputs','Background alerts','After warm-up','Windows with alerts'],rows,[1.7,1.6,1.5,1.7],
                'Static models only. Background contains 8,816 source-described benign synthetic events. After warm-up excludes the first 24 hours. Window alerts may be caused by benign records and do not establish attack recall. All settings use one simulated environment.')
    elif key=='v4_stress':
        rows=[]
        for inputs,encoding,name in ITEMS:
            path=ROOT/f'results/journal_v4_contamination/{inputs}_{encoding}_narrow_training_offset_s42/conditions.csv'
            d=pd.read_csv(path);s=d[(d.pool_size==2000)&(d.nominal_fraction==.20)&(d.policy=='guarded_screened_refit')]
            assert len(s)==3
            rows.append([name,f"{s.screened_attack_count_evaluation_only.mean():.1f} / {s.screened_count.mean():.1f}",
                         f"{(s.guard_allowed==True).sum()} / 3",f"{s.f1.mean():.3f}"])
        b.table(key,'Controlled contamination stress at a nominal twenty percent',
                ['Inputs','Attack / rows after screening','Guard accepted','Later F1'],rows,[1.6,2.0,1.45,1.45],
                'Pool size 2,000; averages over three seeds. Screening counts are before the guard, so they are not necessarily accepted updates. Guard count is the number accepted out of three. Attack labels construct the stress condition and audit outcomes, not runtime screening.')
    elif key=='v4_primary':
        d=pd.read_csv(ROOT/'results/journal_v4_primary_matched/summary.csv')
        rows=[]
        for mode,label in [('training_offset','Training offset'),('benign_quantile','Unlabelled quantile')]:
            vals=[]
            for policy in ['static','dual_signal','coupled_signal']:
                row=d[(d.event_cutoff==mode)&(d.policy==policy)].iloc[0]
                vals.append(triple(row))
            rows.append([label,*vals])
        b.table(key,'Size matched future month controlled intervention results',
                ['Cutoff','Static R/proxy/F1','Dual R/proxy/F1','Coupled R/proxy/F1'],rows,
                [1.65,1.62,1.62,1.61],
                'Calibration and monitoring samples both contain 200 rows. R measures synthetic changed-row targets, and proxy is the mask-relative negative-class alarm rate; it is not a verified benign FPR. Three seeds and repeated month pairs are dependent.')
    elif key=='v4_rich':
        data=pd.read_csv(ROOT/'results/journal_v4_primary_rich_context/monthly_observations.csv')
        rows=[]
        for inputs,name in [('event','Event ordinal'),('behaviour','Behaviour'),('combined','Combined ordinal')]:
            part=data[(data.inputs==inputs)&(data['split']=='test')]
            assert len(part)==9
            rows.append([name,f"{part.training_cutoff_alert_fraction.median():.3f}",
                         f"{part.validation_quantile_alert_fraction.median():.3f}",
                         f"{int(part.dual_signal_request.sum())} / {int(part.coupled_signal_request.sum())}"])
        b.table(key,'Unlabelled observations in the inherited timestamped export',
                ['Inputs','Median training alerts','Median validation quantile alerts','Dual / coupled requests'],
                rows,[1.6,1.6,1.65,1.65],
                'Alert columns are median per-month fractions over nine test months, not false-positive rates. The quantile uses earlier unlabelled validation scores. Requests are potential monitoring decisions; no updates were executed.')
    else:raise KeyError(key)


def equation(key):
    if key not in {'feature', 'effective'}:return v3.equation(key)
    b.equation_count+=1
    if key == 'feature':
        parts=[b.sub('F','t'),' = ',b.frac('1','m'),b.summation('j = 1','m',b.sub('d','j,t'))]
    else:
        parts=[b.sub('N','eff'),'(v) = ',b.frac(b.sup(['(',b.summation('j = 1','m',b.delimiter(b.sub('v','j'))),')'],'2'),
                                                   b.summation('j = 1','m',b.sup(b.sub('v','j'),'2')))]
    p=b.doc.add_paragraph();p.alignment=b.WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=b.Pt(5);p.paragraph_format.space_after=b.Pt(7)
    math=b.OxmlElement('m:oMath');b.append(math,parts);p._p.append(math)
    b.font(p.add_run(f'    ({b.equation_count})'),10)
    b.resolved_blocks.append(f'[Editable equation {b.equation_count} {key}]')


def figure(key):
    if key!='tradeoffs':raise KeyError(key)
    caption=('Figure 1 Static, dual and coupled outcomes in narrow-history conditions. '
             'Colours distinguish input representations and shapes distinguish policies. '
             'All points reuse the same 11,531 events; a low false positive rate is not useful if recall collapses.')
    p=b.doc.add_paragraph();p.alignment=b.WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.keep_with_next=True
    run=p.add_run();run.add_picture(str(ROOT/'tmp/journal_paper_v4/assets/tradeoffs.png'),width=b.Inches(6.45))
    run._r.xpath('.//wp:docPr')[0].set('descr',caption)
    b.paragraph(caption,'Caption')


if __name__=='__main__':
    assert len(json.loads((ROOT/'results/journal_v4_tiesafe_analysis/integrity_checks.json').read_text()))==20
    assert len(json.loads((ROOT/'results/journal_v4_tiesafe_analysis/seed_integrity_checks.json').read_text()))==60
    assert len(list((ROOT/'results/journal_v4_contamination').glob('*/manifest.json')))==5
    rich=json.loads((ROOT/'results/journal_v4_primary_rich_context/manifest.json').read_text())
    assert rich['sample_rows']==42513 and rich['duplicate_event_ids_removed']==2487
    original_table=b.table
    def table_together(*args,**kwargs):
        original_table(*args,**kwargs)
        for i,row in enumerate(b.doc.tables[-1].rows):
            for cell in row.cells:
                for p in cell.paragraphs:p.paragraph_format.keep_with_next=i<len(b.doc.tables[-1].rows)-1
    original_paragraph=b.paragraph
    def paragraph_urls(text,style=None,align=None):
        return original_paragraph(text,style,b.WD_ALIGN_PARAGRAPH.LEFT if 'https://' in text and style is None and align is None else align)
    original_refs=b.add_references
    def refs_together():
        first=len(b.doc.paragraphs);original_refs()
        for p in b.doc.paragraphs[first:]:p.paragraph_format.keep_together=True
    b.table,b.paragraph,b.add_references=table_together,paragraph_urls,refs_together
    b.build_table,b.equation,b.figure=build_table,equation,figure
    b.doc.core_properties.title='Behavioural Context and Attribution Guided Adaptation for Cloud Audit Logs'
    b.main()
    path=b.AUDIT/'build_audit.json';audit=json.loads(path.read_text(encoding='utf-8'))
    evidence=[*sorted((ROOT/'results/journal_v4_tiesafe_analysis').glob('*.*')),
              *sorted((ROOT/'results/journal_v4_contamination').glob('*/conditions.csv')),
              ROOT/'results/journal_v4_primary_matched/summary.csv',ROOT/'results/journal_v4_external_trace_replay/summary.csv',
              ROOT/'results/journal_v4_primary_rich_context/monthly_observations.csv',ROOT/'results/journal_v4_primary_rich_context/manifest.json',
              ROOT/'results/journal_v4_synthetic_independent/summary.csv',ROOT/'results/journal_v4_synthetic_independent/incident_windows.csv',
              ROOT/'results/journal_v4_synthetic_independent/manifest.json']
    audit['v4_evidence_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence}
    path.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
