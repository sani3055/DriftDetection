"""Generate publication figures from retained v3 outcomes, without rerunning models."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tmp/journal_paper_v3/assets'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                     'axes.spines.right': False, 'savefig.dpi': 220})
policies = ['static', 'dual_signal', 'coupled_signal', 'score_wasserstein', 'adwin_score', 'guarded_dual']
names = ['Static', 'Dual', 'Coupled', 'Score W1', 'ADWIN', 'Guarded dual']
colours = ['#222222', '#0072B2', '#D55E00', '#009E73', '#CC79A7', '#806000']
markers = ['o', 's', '^', 'D', 'P', 'X']
fig, axes = plt.subplots(2, 2, figsize=(8, 6.3), sharex=True, sharey=True)
for ax, (representation, mode) in zip(axes.flat, [(r, m) for r in ['ordinal', 'onehot'] for m in ['training_offset', 'benign_quantile']]):
    table = pd.read_csv(ROOT / f'results/journal_v3/{representation}_{mode}_w128_s42/summary.csv')
    table = table[table.session == 'pooled'].set_index('policy')
    for policy, name, colour, marker in zip(policies, names, colours, markers):
        row = table.loc[policy]
        ax.scatter(row.false_positive_rate, row.recall, label=name, c=colour, marker=marker,
                   s=62, alpha=.85, edgecolors='white', linewidths=.4)
    ax.set_title(f"{'Ordinal' if representation == 'ordinal' else 'One hot'} / {'training offset' if mode == 'training_offset' else 'benign quantile'}", fontsize=11)
    ax.set_xlim(-.025, 1.025)
    ax.set_ylim(-.025, 1.025)
    ax.grid(alpha=.2)
for ax in axes[:, 0]: ax.set_ylabel('Attack recall')
for ax in axes[1, :]: ax.set_xlabel('Benign false positive rate')
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, ncol=3, loc='lower center', frameon=False, bbox_to_anchor=(.5, -.005))
fig.tight_layout(rect=(0, .08, 1, 1))
fig.savefig(OUT / 'factorial_tradeoffs.png', bbox_inches='tight')
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(8, 3.45), sharey=True)
for ax, representation in zip(axes, ['ordinal', 'onehot']):
    folder = ROOT / f'results/journal_v3/{representation}_training_offset_w128_s42'
    cal = pd.read_csv(folder / 'calibration_signals.csv')
    test = pd.read_csv(folder / 'signals.csv')
    import json
    manifest = json.loads((folder / 'manifest.json').read_text())
    # Use the same windows and annotations as the saved failure-analysis script.
    counts = pd.read_csv(folder / 'window_counts.csv')
    base = counts[counts.policy == 'static'].copy()
    keys = ['session', 'window'] if 'window' in test.columns else ['session', 'window_index']
    merged = test.merge(base[keys + ['tp', 'fn']], on=keys, validate='one_to_one')
    samples = [cal.coupling_score.to_numpy(), merged.loc[(merged.tp + merged.fn) == 0, 'coupling_score'].to_numpy(),
               merged.loc[(merged.tp + merged.fn) > 0, 'coupling_score'].to_numpy()]
    for index, values in enumerate(samples):
        order = np.argsort(values, kind='stable')
        jitter = np.linspace(-.13, .13, len(values))
        ax.scatter(index + jitter, values[order], s=14, color=['#666666', '#0072B2', '#D55E00'][index], alpha=.65)
        ax.plot([index - .2, index + .2], [np.median(values)] * 2, color='black', linewidth=2)
    threshold = float(pd.read_csv(ROOT / 'results/journal_v3_analysis/gate_failure_analysis.csv').query(
        'configuration == @representation + "_training_offset_w128_s42" and subset == "calibration"').coupling_threshold.iloc[0])
    ax.axhline(threshold, color='#555555', linestyle='--', linewidth=1)
    ax.set_xticks([0, 1, 2], ['Earlier benign\ncalibration', 'Attack free\ntest', 'Attack containing\ntest'])
    ax.set_title('Ordinal' if representation == 'ordinal' else 'One hot')
    ax.set_ylim(0, 1.04)
    ax.grid(axis='y', alpha=.2)
axes[0].set_ylabel('Feature attribution cosine alignment')
fig.tight_layout()
fig.savefig(OUT / 'alignment_overlap.png', bbox_inches='tight')
plt.close(fig)
print(f'Figures written to {OUT}')
