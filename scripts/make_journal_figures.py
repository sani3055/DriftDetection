"""Create manuscript figures from saved data without rerunning experiments."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'tmp/journal_paper/assets'
OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'savefig.facecolor':'white'})

fig,ax=plt.subplots(figsize=(10,3.7))
ax.set_xlim(0,10);ax.set_ylim(0,3.7);ax.axis('off')
boxes={
    'input':(.10,1.30,2.0,.9,'CloudTrail records\nTraining only encoding'),
    'feature':(2.75,2.25,2.25,.9,'Feature distributions\nPSI and scalar shift'),
    'shap':(2.75,.35,2.25,.9,'Isolation Forest and SHAP\nAttribution drift'),
    'coupling':(5.75,1.30,1.95,.9,'Magnitude gates\nFeature alignment'),
    'decision':(8.15,1.30,1.75,.9,'Diagnosis\nUpdate request'),
}
for x,y,w,h,label in boxes.values():
    ax.add_patch(Rectangle((x,y),w,h,linewidth=.8,edgecolor='#4b5563',facecolor='#f4f6f8'))
    ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=10)
for start,end in [((2.1,1.95),(2.75,2.7)),((2.1,1.55),(2.75,.8)),((5,2.7),(5.75,1.95)),((5,.8),(5.75,1.55)),((7.7,1.75),(8.15,1.75))]:
    ax.add_patch(FancyArrowPatch(start,end,arrowstyle='-|>',mutation_scale=11,linewidth=1,color='#374151'))
ax.text(9.02,.66,'Replay and predicted-normal\ncandidates if a refit is requested',ha='center',va='center',fontsize=8.5)
ax.annotate('',xy=(9.02,.9),xytext=(9.02,1.3),arrowprops={'arrowstyle':'-|>','lw':.8,'color':'#374151'})
fig.tight_layout(pad=.3)
fig.savefig(OUT/'pipeline.png',dpi=300,bbox_inches='tight')
plt.close(fig)

data=pd.read_csv(ROOT/'data/benchmark/diagnosis_results.csv')
data=data[data['split'].eq('test')]
thresholds=json.loads((ROOT/'data/benchmark/diagnosis_thresholds.json').read_text())
fig,ax=plt.subplots(figsize=(7.2,4.1))
groups=[('stable','Stable family','#2563eb','o'),('benign_','Benign interventions','#c17a00','s'),('security_','Security interventions','#a33848','^')]
for prefix,label,color,marker in groups:
    group=data[data.scenario.eq('stable')] if prefix=='stable' else data[data.scenario.str.startswith(prefix)]
    ax.scatter(group.feature_drift_score,group.shap_drift_score,label=label,c=color,marker=marker,s=39,alpha=.8,edgecolors='white',linewidths=.45,zorder=3)
ax.axvline(thresholds['feature_threshold'],color='#6b7280',ls='--',lw=.9)
ax.axhline(thresholds['shap_threshold'],color='#6b7280',ls='--',lw=.9)
privilege=data[data.scenario.eq('security_privilege')]
xy=(privilege.feature_drift_score.mean(),privilege.shap_drift_score.mean())
ax.annotate('Privilege family remains\nbelow the SHAP gate',xy=xy,xytext=(.35,.44),fontsize=9,
            arrowprops={'arrowstyle':'-','lw':.7,'color':'#4b5563'},ha='left')
ax.set_xlabel('Feature drift score');ax.set_ylabel('SHAP drift score')
ax.set_xlim(-.06,max(data.feature_drift_score.max()*1.08,1.6))
ax.set_ylim(-.05,data.shap_drift_score.max()*1.13)
ax.spines[['top','right']].set_visible(False)
ax.grid(alpha=.15,lw=.6)
ax.legend(loc='lower left',bbox_to_anchor=(0,1.02),ncol=3,fontsize=8,frameon=False)
fig.tight_layout()
fig.savefig(OUT/'controlled_signals.png',dpi=300,bbox_inches='tight')
plt.close(fig)
print('Saved manuscript figures in',OUT)
