"""Insert the user's seven replacement extracts, correcting factual errors only.

The previous final report supplies its unchanged structure, headings, tables,
figures, references, code, styles, geometry and opaque package parts. A private
audit records the supplied text, final text and reason for each correction.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
from zipfile import ZipFile

from lxml import etree as E
import finalize_report_revision as report

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/BCSE497J_Capstone_Report_Concise_10000.docx'
OUT = ROOT / 'outputs/BCSE497J_Capstone_Report_User_Text_Final.docx'
TMP = ROOT / 'tmp/report_supplied_text'
ATTACHMENTS = [
    'd93cb835-aa2f-46fc-a0db-7934c999d9dc',
    '99caaba1-829d-49dd-922c-b2b67a071f7d',
    '7f732b43-54a4-4af4-a6c5-c43aa9874a67',
    '609964ae-cd3f-4f82-bc26-83dceed0ecee',
    '641c5995-50f1-44c3-9f0b-c022cbaf2ad2',
    '7b39d088-3af9-4d8a-9a7f-b8b479858fcb',
    '7bd3a752-dab4-4cb6-aee0-21b693b99dbb',
]

# Attachment number -> source line : existing body paragraph. Numbered headings
# are deliberately retained from the approved report (not inserted as prose).
MAPPING = {
    1: {1:137,2:138,3:139,4:140,8:145,9:146,10:147,11:148,
        13:150,14:151,15:152,17:154,18:155,19:156,21:158,22:159,
        26:164,28:166,29:167},
    2: {1:169,2:170,4:172,5:173,7:175,8:176,10:180,11:181,12:182,
        14:184,15:185,17:187,18:188,20:190,21:193,25:197,26:201,
        28:203,29:206,32:209,33:210,35:212,36:213},
    3: {1:215,2:216,5:219,7:221,9:225,10:228,14:232,15:235,
        16:236,19:239,20:242,22:244,23:247,25:249,26:252,
        28:254,29:257,31:259,32:260,33:263,35:265,36:266},
    4: {3:270,4:273,6:275,7:276,8:277,10:279,11:280,12:281,
        14:283,15:284,16:285,18:287,19:288,20:289,22:291,23:292,24:293},
    5: {1:295,2:296,3:297,5:299,6:302,7:303,9:305,10:306,
        11:307,13:309,14:310,15:311,17:313,18:316,22:320,
        23:321,24:325,25:326,26:327},
    6: {1:329,2:330,4:332,5:333,9:337,10:340,12:342,13:345,
        15:349,16:350,17:353,19:355,20:356,21:359,23:361,
        24:364,25:365,27:367,28:370,29:371},
    7: {1:375,2:376,3:377,5:379,6:380,7:381,9:383,10:384,
        12:386,13:387,14:388,15:389,19:393,20:394,22:396,
        23:397,25:399,26:400,28:402},
}

# Local edits only: the left side must match the user's supplied text exactly.
FIXES = {
    139: [('It is not attacked with any attack labels.', 'It has no attack labels.', 'Unlabelled does not mean unattacked.')],
    140: [('unlabelled target scores were correlated', 'unlabelled target scores were calibrated', 'The experiment calibrates a threshold, not a correlation.')],
    146: [('Isolation Forest isolates observations easily that are isolated by random tree partitions', 'Isolation Forest scores observations that are easily isolated by random tree partitions', 'Correct the detector operation without changing its conclusion.')],
    154: [('outputs are saved to the source objects', 'outputs are saved as separate artifacts', 'Outputs do not overwrite the read-only source.')],
    158: [('It is manifest, chronologically split, features contract and fitted detector, SHAP samples and policy results, which enable reproducibility and live inspection.', 'Its manifest, chronological split, feature contract and fitted detector, SHAP samples and policy results enable reproducibility and live inspection.', 'Restore the names of the implemented artifacts.')],
    166: [('training compounds, and contaminations', 'training composition, and contamination settings', 'Restore the technical terms.'), ('There is no attack if it is just a low-density observation.', 'A low-density observation alone does not establish an attack.', 'Low density neither proves nor excludes an attack.')],
    167: [('It does not broach the concept of changing the behavior of the legitimate users.', 'It does not introduce the general concept of adapting anomaly detectors to changes in legitimate users\' behaviour.', 'The novelty concerns detector adaptation, not modifying users.')],
    169: [('Using attributions for drift monitoring, the realization of checks the numerical reconstruction of TreeSHAP.', 'Before using attributions for drift monitoring, the implementation checks the numerical reconstruction of TreeSHAP.', 'Restore the stated validation step.')],
    173: [('The accepted rows are only guaranteed to be benign by that filter.', 'The accepted rows are not guaranteed to be benign by that filter.', 'A model-normal filter does not guarantee clean training rows.')],
    176: [('The total number of records in the review collection is 100', 'The total number of DOI records in the review collection is 100', 'Distinguish collected records from included journal studies.'), ('The separate review-paper effort is guided by PRISMA.', 'The separate review-paper effort is guided by PRISMA [13].', 'Retain the existing PRISMA citation.')],
    181: [('divided into two types of testing', 'divided into three types of testing', 'Three separate evaluation tracks are listed.')],
    184: [('the reconstruction of the tree, TreeSHAP,', 'the TreeSHAP reconstruction', 'Additivity validates explanations, not reconstruction of a tree.')],
    187: [('The controller should not be involved in the decision path and should log actions by the controller.', 'Attack labels should not be involved in the decision path, and the controller should log its actions.', 'The controller makes decisions; labels must be excluded.')],
    188: [('Do evidence changes in the features influence feature-only update decisions? Do evidence changes in the features influence feature-only update decisions?', 'Do changes in SHAP evidence influence feature-only update decisions?', 'Restore the actual research question and remove accidental repetition.'), ('Does coupling choose joint alarms that are useful? Does coupling choose joint alarms that are useful?', 'Does coupling choose joint alarms that are useful?', 'Remove accidental duplicated question.'), ('Does source thresholds also transfer to another corpus? Does source thresholds also transfer to another corpus?', 'Do source thresholds also transfer to another corpus?', 'Remove accidental duplicated question.')],
    210: [('It is not self-contained or self-validating, as it is from the same corpus.', 'It is not independent validation, as it is from the same corpus.', 'A richer export is not an independent validation dataset.')],
    219: [('models and artifacts are stored in a ~831 MB source CSV', 'uses a ~831 MB source CSV, with models and artifacts stored separately', 'Models are separate files, not stored inside the input CSV.')],
    228: [('Unseen values map to −1 before mapping', 'Unseen values map to −1 during encoding', 'Unknown handling occurs in category encoding.')],
    236: [('It has been evaluated separately from its labels and temporal construction.', 'Its labels and temporal construction are evaluated separately from the primary corpus.', 'Independent labels are used for evaluation, not ignored.')],
    254: [('The user loads a reference (from the base or training)', 'The runner loads a baseline model and a training-derived reference', 'Restore the experiment inputs and actor.')],
    259: [('the high feature drift yields benign_drift', 'high feature drift alone yields benign_drift', 'Both high gates instead select the joint-alarm state.'), ('If both features have low drift and high SHAP drift, it is review required.', 'If feature drift is low and SHAP drift is high, it is review_required.', 'Feature drift and SHAP drift are separate signals.')],
    260: [('Hidden_model_instability if alignment is low or review_required if it is high else low feature drift with high attribution drift.', 'Low feature drift with high attribution drift gives hidden_model_instability if alignment is low, or review_required if it is high.', 'Restore the implemented conditional.')],
    263: [('Dual & Coupled policies update only for states that are relevant to their model.', 'Dual & Coupled policies update only for the security_relevant_drift state.', 'Name the exact update-triggering state.')],
    265: [('would provide finer temporal or relational data', 'would require finer temporal or relational data', 'Models require suitable data; they do not create finer source observations.')],
    284: [('the divergence is ½ Kullback–Leibler divergence of each distribution to m', 'the divergence is half the sum of the Kullback–Leibler divergences of the two distributions to m', 'Specify the sum in Jensen–Shannon divergence.')],
    287: [('normalizes it by the Wasserstein distance of the reference attribution with a small stabilising constant', 'normalizes it by the standard deviation of the reference attribution plus a small stabilising constant', 'The code divides by reference standard deviation, not another Wasserstein distance.')],
    288: [('The latter performs comparison between the reference sample and current sample and keeps the absolute difference for each feature.', 'The latter compares the mean absolute SHAP values in the reference sample and current sample and keeps the absolute difference for each feature.', 'Distinguish absolute SHAP displacement from signed mean change.'), ('The signed shift is an indication of a direction of shift in the contribution, the absolute shift is a measure of a magnitude of shift in the contribution.', 'The stored mean_signed_attribution_shift averages the absolute differences between signed feature means and does not retain their direction; the absolute displacement measures the magnitude of change in mean absolute SHAP values.', 'The stored aggregate takes absolute differences, so it does not preserve direction.')],
    292: [('Feature and SHAP gates do not need to pass', 'Feature and SHAP gates need to pass', 'Both magnitude gates are required before coupling can trigger adaptation.')],
    293: [('These are not assertions that the mathematical operators are equal to these simplifications of the alignment definition, but rather they are ablations.', 'These are ablations of the alignment definition, not new mathematical operators.', 'Avoid an incoherent claim about established operators.')],
    295: [("The feature scores used for candidates' validation and the feature set's SHAP thresholds are selected using fixed quantiles from the validation score distribution.", 'Candidate feature and SHAP thresholds are selected using fixed quantiles from the validation score distribution.', 'Clarify the two tuned thresholds rather than changing the method.')],
    296: [('The saved threshold of cosine is 0.8640697362, the coupling threshold is 0.8640697362.', 'The saved cosine and conservative coupling thresholds are both 0.8640697362.', 'Both alignment variants have the recorded threshold.'), ('These are constant for the source scenario (s) that are not held-out and passed over in the source-threshold external experiment.', 'These remain fixed for held-out source scenarios and are transferred unchanged in the source-threshold external experiment.', 'Correct the held-out and external transfer protocol.')],
    302: [('Your right is protected by AssumeRole.', 'AssumeRole can be legitimate.', 'The API does not guarantee rights or malicious intent.'), ('If the scenario does not fit into one of the "known" categories, then it falls into the unknown code', 'If a scenario introduces unseen categories, then they fall into the unknown code', 'Encoding applies to category values rather than scenario identities.')],
    303: [('5 to 14 seeds are held out', 'Ten seeds, 5 to 14, are held out', 'The range contains ten seeds, not a variable seed count.')],
    305: [('If not, can be inserted in 50-tree Isolation Forest on replay row and accepted current row with contamination of 0.05 and the same seed for the same run.', 'Otherwise, a 50-tree Isolation Forest is fitted on replay rows and accepted current rows with contamination of 0.05 and the same seed for the same run.', 'Restore the refitting operation and its training inputs.')],
    306: [('Normal filtering based on the normal baseline will still allow for the admission of known anomalies, although it will filter out known attacks.', 'Normal filtering based on the baseline rejects recognised anomalies but can still admit undetected attacks.', 'The filter has no knowledge of confirmed attack labels.'), ('Protected" means', '"Protected" means', 'Repair the broken technical-term quotation.')],
    309: [('Predicted mask or independent label', 'Controlled perturbation mask or independent label', 'Evaluation ground truth is not the detector prediction.')],
    329: [('Data/benchmark', 'data/benchmark', 'Keep the actual artifact path.')],
    330: [('Confusion matrix and policy chart are based on saved experiments and are included in the monthly timeline.', 'The monthly timeline, confusion matrix and policy chart are based on saved experiments.', 'These are separate figures, not components of the timeline.'), ('Data/external_validation', 'data/external_validation', 'Keep the actual artifact path.')],
    332: [('to fully regenerate the source', 'to fully regenerate the results', 'Regeneration reads the source instead of recreating it.')],
    333: [('verifies the implementation using python -m pytest tests -q.', 'python -m pytest tests -q verifies the implementation.', 'Restore the command as the subject of the verification statement.')],
    342: [('performed best among the three diagnosis classes represented with macro-F1 of 0.7306', 'achieved macro-F1 of 0.7306 over the three diagnosis classes represented', 'A macro-F1 score averages classes; classes are not competing policies.')],
    355: [('This represents about 8.85 percentage points of the benchmark being assessed.', 'This represents a reduction of about 8.85 percentage points in FPR within the benchmark being assessed.', 'Attach percentage points to the measured rate.')],
    356: [('due to crossing.', 'because its interval crosses zero.', 'State what prevents an improvement conclusion.')],
    364: [('The difficulty of the task changes as the number of rows increases', 'The difficulty of the task may change as the number of rows increases', 'A sample-size comparison does not establish the proposed cause.')],
    367: [('2,585 benign data and 21,502 attack labels', '2,585 attack-labelled records and 21,502 benign records', 'Correct the reversed external class counts.')],
    370: [('Isola Forest', 'Isolation Forest', 'Correct the detector name.')],
    375: [('Those false positive percentages are due to the small number of benign windows:', 'The FPR of 0.5 corresponds to one false positive among the two benign windows:', 'Clarify the denominator and exact false-positive count.')],
    379: [('the cost associated with the missed security times (1 - recall on security scenarios) plus (unnecessary adaptation cost) times (FPR on benign scenarios)', 'missed-security cost times (1 - recall on security scenarios), plus false-alarm cost times (FPR on benign scenarios), plus update penalty times the unnecessary-adaptation indicator', 'Restore all three terms of the implemented loss and their correct weights.')],
    381: [('Real-time throughput is not achieved with bounded samples, but makes local execution a possibility.', 'Real-time throughput is not established by bounded samples, which make local execution a possibility.', 'Unmeasured throughput cannot be declared achieved or failed.')],
    384: [('The controlled policy comparison has no effect (neutral)', 'The controlled coupling comparison has no incremental policy benefit (neutral)', 'The neutral finding concerns adding coupling, not every policy comparison.'), ('source tuning has a small success rate', 'source-threshold transfer has poor recall', 'The negative result concerns external threshold transfer.'), ('The incremental value of journal claims must support robust journal claims, appropriate baseline, and independent recovery over time.', 'A journal claim of incremental value must be supported by appropriate baselines and independent recovery over time.', 'Restore the intended evidence requirement.')],
    387: [('The drawback of validation only tuning is that it does not involve selecting a test label, but it does not rule out overfitting a small family of perturbations.', 'Validation-only tuning avoids selecting thresholds from test labels, but it does not rule out overfitting a small family of perturbations.', 'Avoiding test-label tuning is a safeguard, not the drawback.')],
    389: [('Conclusions are neutral and negative', 'Conclusions retain neutral and negative results', 'Neutral coupling results do not negate every other measured finding.')],
    396: [('It was not possible to determine whether its F1 difference was inconclusive.', 'Its F1 difference was inconclusive.', 'Remove the double uncertainty that reverses the reported conclusion.')],
    400: [('Journal submission is still required to be accompanied by a PRISMA screening and manuscript preparation.', 'The separate review paper still requires PRISMA screening, while journal submission also requires manuscript preparation.', 'PRISMA belongs to the separate systematic review, not every experimental paper.')],
}


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    with ZipFile(SOURCE) as z:
        parts = {n:z.read(n) for n in z.namelist()}
    root = E.fromstring(parts['word/document.xml'])
    body = root.find(report.W+'body')
    baseline = deepcopy(root)
    edits = []
    used = set()
    all_lines = []
    for number, identifier in enumerate(ATTACHMENTS, 1):
        path = Path('C:/Users/Lenovo/.codex/attachments') / identifier / 'Pasted text.txt'
        lines = [l.strip() for l in path.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
        all_lines.append(lines)
        for line_index, target in MAPPING[number].items():
            assert target not in used
            used.add(target)
            p = body[target]
            assert p.tag == report.W+'p'
            assert not p.findall('.//'+report.W+'drawing')
            assert not p.findall('.//'+report.W+'instrText')
            supplied = lines[line_index]
            corrected = supplied
            reasons = []
            for old, new, reason in FIXES.get(target, []):
                assert corrected.count(old) == 1, (target, old, corrected)
                corrected = corrected.replace(old, new)
                reasons.append({'old':old, 'new':new, 'reason':reason})
            old_text = report.txt(p)
            old_properties = E.tostring(p.find(report.W+'pPr'))
            report.replace_text(p, corrected)
            assert E.tostring(p.find(report.W+'pPr')) == old_properties
            edits.append({'body_index':target, 'attachment':number, 'line_index':line_index,
                          'previous':old_text, 'supplied':supplied, 'final':corrected,
                          'corrections':reasons})
    assert set(FIXES).issubset(used)
    assert all(E.tostring(before) == E.tostring(after)
               for i, (before,after) in enumerate(zip(baseline.find(report.W+'body'),body))
               if i not in used), 'An unrelated body element changed.'
    assert len(body) == len(baseline.find(report.W+'body'))
    # Every non-prose line represents an existing numbered heading. Keep that
    # heading, correcting the accidental duplicate / nontechnical replacements.
    ignored = [{'attachment':n, 'line_index':i, 'supplied':line}
               for n,lines in enumerate(all_lines,1) for i,line in enumerate(lines)
               if i not in MAPPING[n]]
    parts['word/document.xml'] = E.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
    report.write_package(parts, OUT)
    report.write_package(parts, TMP/'before_word_refresh.docx')
    shutil.copyfile(OUT, TMP/'word_refresh_working.docx')
    audit = {'source':str(SOURCE), 'source_sha256':source_hash, 'output':str(OUT),
             'attachments':len(ATTACHMENTS), 'inserted_paragraphs':len(edits),
             'paragraphs_with_factual_corrections':sum(bool(e['corrections']) for e in edits),
             'verbatim_paragraphs':sum(not e['corrections'] for e in edits),
             'correction_count':sum(len(e['corrections']) for e in edits),
             'edits':edits, 'retained_heading_slots':ignored,
             'template_parts_preserved':True, 'all_other_body_elements_preserved':True}
    (TMP/'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
    print(json.dumps({k:v for k,v in audit.items() if k not in {'edits','retained_heading_slots'}},indent=2))


if __name__ == '__main__':
    main()
