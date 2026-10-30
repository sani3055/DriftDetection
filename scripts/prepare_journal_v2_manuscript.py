"""Build a separate revision source from preserved legacy text and native evidence."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = (ROOT / 'docs/journal_paper_source.md').read_text(encoding='utf-8')
    old_abstract = source.split('## Abstract\n\n', 1)[1].split('\n\n**Keywords**', 1)[0]
    abstract = '''Cloud activity changes over time, making it difficult to distinguish a useful anomaly-detector update from one that absorbs suspicious activity. This study evaluates feature-distribution drift, SHAP-attribution drift and their feature-level cosine alignment for AWS CloudTrail monitoring. It separates an unlabelled 45-month corpus, a legacy controlled perturbation benchmark and a new native chronological evaluation. In the legacy benchmark, dual signals reduce mean false positives, but coupling adds no policy benefit and scoring uses the adaptation batch itself. The new protocol corrects that limitation by scoring each window before updating, matching all forests at 100 trees, calibrating gates on earlier benign windows and constructing windows without attack annotations. Across 11,531 later labelled events, the primary static detector has recall 0.9485 and false-positive rate 0.7187. Dual updating lowers the false-positive rate to 0.6651 but also lowers recall to 0.7735 and F1 from 0.4888 to 0.4343. Coupling requests no updates in all seven sensitivity settings. The study therefore establishes neither improved future detection nor portable security relevance from alignment. Its contribution is a reproducible temporal evaluation and explicit failure analysis of attribution-guided adaptation, identifying calibration, representation and candidate-contamination limits that require further investigation.'''
    source = source.replace(old_abstract, abstract)
    source = source.replace('The study asks three questions.', 'The study asks three initial questions.')
    source = source.replace('## 3 Data and Evaluation Design', '''Lara-Gutierrez and colleagues combine drift detection and adaptation in HDDAF, including incremental learning and retraining [@lara]. Their network-intrusion setting reinforces that adaptive security pipelines are established prior work. The present study instead asks whether an attribution-alignment gate improves matched-capacity, future-only CloudTrail decisions. It does not reproduce HDDAF or claim a numerical advantage over it.

## 3 Data and Evaluation Design''', 1)
    method = '''### 3.4 Native chronological evaluation

The additional evaluation uses raw timestamps from the independent corpus, rather than attack-name groups. Nine duplicate event IDs are removed from the benign archive. The earliest benign day is split chronologically into 6,881 fitting events and 2,949 reference events, with timestamp ties purged from the fitting side. The remaining 6,656 benign records, on the next two days, supply 53 calibration windows at the primary size of 128 events. Category maps use fitting events only. The original training archive ends on 20 February 2026.

All evaluation events must occur after that cutoff. This removes earlier records from the mixed archive and retains 7,315 events on 4 April. The archive named train_labeled_a is also held out here, contributing 35 events on 27 April and 4,181 on 28 April. Together these sessions contain 11,531 events, including 3,126 attack-labelled and 8,405 benign events. Its filename does not imply training use. Event IDs are disjoint across archives, and windows never depend on attack_name or should_sample.

Non-overlapping event-count windows retain a short final batch. Windows reset at date/archive boundaries to avoid combining long gaps. The primary setting has 92 windows across three date-separated sessions. These sessions originate from the same controlled deployment and do not constitute independent sites. The earlier project has already inspected this dataset, so the revised experiment is held out by procedure rather than an entirely blind new corpus. No test labels enter gate calibration.

## 4 Methodology'''
    source = source.replace('## 4 Methodology', method, 1)
    extra_method = '''### 4.7 Matched capacity and prequential updates

For the native protocol, baseline and refit forests both use 100 trees, contamination 0.05, max_samples auto and the same random seed. Every policy predicts the current batch before any model update from that batch. An update therefore affects only subsequent windows in its session. Policies retain their own deployed state within a session and restart from the same baseline at the next session boundary.

A frozen baseline computes monitoring explanations and screens normal candidates for all policies, providing equal diagnostic and candidate inputs. Each refit combines a fixed 512-record replay sample from fitting data with current records predicted normal by that baseline. At least ten current candidates are required. No attack labels screen candidates. A request can fail to produce a refit, and a successful last-window refit has no future evaluation window. Caching an identical refit shared by several policies changes computational reuse, not policy predictions. The replay/reference choice and frozen diagnostic model can become stale.

All seven encoded inputs enter the native feature-drift vector and attribution displacement, unlike the legacy five-feature coupling vector. Feature drift is their mean categorical PSI with count smoothing 0.000001. Attribution drift combines mean normalised Wasserstein displacement, top-three set disagreement and a Kendall tau-b term. The latter now compares feature-aligned mean-absolute-SHAP ranks with average ties. It does not compare sorted feature-ID sequences. For Wasserstein normalisation, each reference standard deviation is floored at the larger of 0.000001 and one tenth of the median positive reference standard deviation. Identical constant attribution vectors have full rank agreement. Zero-mass coupling remains zero.

Each magnitude and alignment threshold is the higher empirical 95th percentile of its earlier benign calibration scores. Updates use strict greater-than comparisons, preventing zero-score ties from firing. Feature-only and SHAP-only use one gate; dual requires both magnitude gates; coupling additionally requires its calibrated alignment gate. Conservative coupling uses the minimum of cosine and positive-shifted Pearson alignment. Each policy reads one complete, immutable gate object. These empirical quantiles do not imply an exact five-percent false-alarm rate under temporal dependence or deployment shift. Periodic updating requests a refit after every fifth completed batch.

The primary outcomes pool event-level confusion counts before computing precision, recall, F1 and false-positive rate. Missing denominators remain undefined rather than being silently replaced by zero. Update requests, actual refits and attack-free-window requests remain separate counts. Attack presence is used only after predictions and decisions are fixed, for retrospective evaluation. No confidence interval treating these correlated windows as independent incidents is reported.

## 5 Results'''
    source = source.replace('## 5 Results', extra_method, 1)
    result = '''### 5.6 Native chronological results and sensitivity

Table 9 reports the primary native-time result. Static and both coupling policies coincide because neither coupling gate requests any update. Their pooled recall is 0.9485, F1 is 0.4888 and false-positive rate is 0.7187. The high false-alarm burden demonstrates that a detector fitted on the earlier benign period transfers poorly to later workload activity. High recall alone would give a misleading account of this operating point.

[[TABLE:native_policies]]

Dual updating issues 85 requests and completes 42 refits. Its false-positive rate falls to 0.6651, but recall falls to 0.7735 and F1 to 0.4343. Of its requests, 51 occur in attack-free windows. These native mixed streams therefore do not reproduce the legacy claim of no unnecessary requests. Because an attack-free batch can still represent a legitimate workload shift, these counts do not prove that every such update was operationally unnecessary. Conversely, an update requested during an attack-containing window is not inherently beneficial or safe.

[[FIG:native]]

The zero coupling-request count is an operational failure mode, not successful attack rejection. Benign calibration already produces high alignment, so a high alignment quantile can suppress every future request. Avoiding all updates preserves the static detector's high false-positive burden. This result cautions against interpreting similarity as a portable security discriminator.

[[TABLE:native_sensitivity]]

The full sensitivity grid includes window sizes 64 and 256, model seeds 17 and 73, and calibration quantiles 0.90 and 0.99, alongside the primary setting. These alternatives were declared after the primary result as a robustness amendment. None is selected as a replacement primary analysis. Coupling remains inactive in every setting. Changes in window size alter the update opportunities, and model seeds alter the initial detector, so the grid should not be pooled as independent incidents. In the 0.99 setting, even the dual false-positive rate exceeds static while its recall remains lower. Thus the experiments do not establish a stable adaptation advantage.

The primary execution records a 0.132-second baseline fit, 23.711 seconds for monitored-batch SHAP computation and 39.781 seconds total wall time on this machine. These single-run measurements exclude the shared reference explanation from the monitored-batch SHAP timer. They are not a production throughput benchmark, an independent timing trial for each policy, or a peak-memory measurement. Maximum measured SHAP reconstruction residual is 1.95e-14.

## 6 Discussion and Threats to Validity'''
    source = source.replace('## 6 Discussion and Threats to Validity', result, 1)
    source = source.replace('A stronger follow-up would use time-only windows defined without attack annotations, calibrate on an earlier unlabelled target period, and freeze the complete measurement contract before assessing later windows. Matched baseline and refit capacities, future-only scoring, consistency-preserving perturbations and independent account-level repetitions would address the most direct confounds. Feature-aligned rank comparisons should replace the current index-array order statistic only in a separately regenerated experiment.', 'The new chronological protocol addresses label-informed grouping, same-batch scoring, unmatched ensemble sizes and the rank statistic within a separately versioned experiment. It does not repair the legacy controlled interventions or establish cross-account generality. Its high false-positive rates and inactive coupling gates expose representation and calibration problems that should precede further method claims. Consistency-preserving perturbations, categorical representation comparisons and independent account-level repetitions remain necessary.')
    source = source.replace('the current software suite passes 44 tests', 'the current software suite passes 59 tests')
    source = source.replace('The central hypothesis is not supported by the current policy benchmark: adding alignment does not change the held-out decisions made by simpler gates.', 'In the legacy controlled benchmark, adding alignment does not change the held-out decisions made by simpler gates. In the native protocol, alignment suppresses all updates.')
    source = source.replace('Adaptation evidence has two additional limits.', 'The legacy adaptation evidence has two additional limits.')
    source = source.replace('The experiments reset between units rather than maintain an evolving detector,', 'Those legacy experiments reset between units rather than maintain an evolving detector,')
    source = source.replace('No runtime, peak-memory or live deployment benchmark is reported, and no immutable manuscript-specific repository release is claimed.', 'Native protocol manifests record wall, fit and SHAP timing, input hashes, parameters and code hashes under results/journal_v2. No peak-memory or live deployment benchmark is reported, and no immutable manuscript-specific repository release is claimed. Reproduction starts with python scripts/run_journal_temporal.py. The full robustness commands are documented in docs/JOURNAL_STRENGTHENING_PLAN.md. New code and evidence are local until a verified repository update is made.')
    source = source.replace('Target-batch recalibration offers an exploratory response to score-scale shift, but prospective temporal validation, consistent scenario construction and future-only adaptation evaluation remain necessary.', 'The new native chronological evaluation supplies future-only scoring and matched capacities, but exposes high false-positive rates, reduced recall after some updates and inactive coupling gates. Target-batch recalibration remains exploratory, and consistency-preserving scenarios and independent accounts are still needed.')
    destination = ROOT / 'docs/journal_paper_v2_source.md'
    destination.write_text(source, encoding='utf-8')
    summary = pd.read_csv(ROOT / 'results/journal_v2/w128_q0.95_s42/policy_summary.csv')
    summary = summary[summary.session == 'pooled']
    labels = ['Static', 'Periodic', 'Feature', 'SHAP', 'Dual', 'Coupled', 'Conservative']
    ordered = summary.set_index('policy').loc[['static','periodic','feature_only','shap_only','dual_signal','coupled_signal','conservative_coupled_signal']]
    fig, ax = plt.subplots(figsize=(7.0, 3.4), constrained_layout=True)
    positions = list(range(len(labels)))
    ax.bar([x - .19 for x in positions], ordered.recall, .38, label='Recall', color='#243C5A')
    ax.bar([x + .19 for x in positions], ordered.false_positive_rate, .38, label='False-positive rate', color='#A7B2C1', hatch='//')
    ax.set_xticks(positions, labels, rotation=20, ha='right')
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('Pooled event rate')
    ax.legend(frameon=False, loc='upper center', ncols=2)
    ax.spines[['top','right']].set_visible(False)
    fig.savefig(ROOT / 'tmp/journal_paper/assets/native_prequential.png', dpi=300)
    plt.close(fig)
    print(destination)


if __name__ == '__main__':
    main()
