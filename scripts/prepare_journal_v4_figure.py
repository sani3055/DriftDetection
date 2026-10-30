"""Render the declared main-cell tradeoffs from retained v4 evidence."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'tmp/journal_paper_v4/assets';out.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(ROOT/'results/journal_v4_tiesafe_analysis/all_main_results.csv')
items=[('event','ordinal','Event ordinal','#0072B2'),('event','onehot','Event one hot','#56B4E9'),
       ('behaviour','none','Behaviour','#009E73'),('combined','ordinal','Combined ordinal','#D55E00'),
       ('combined','onehot','Combined one hot','#CC79A7')]
policies=[('static','o'),('dual_signal','s'),('coupled_signal','^')]
fig,axes=plt.subplots(1,2,figsize=(8,3.9),sharex=True,sharey=True)
for ax,cutoff in zip(axes,['training_offset','benign_quantile']):
    for inputs,encoding,name,colour in items:
        for policy,marker in policies:
            row=df[(df.coverage=='narrow')&(df.event_cutoff==cutoff)&(df.inputs==inputs)&
                   (df.encoding==encoding)&(df.policy==policy)].iloc[0]
            ax.scatter(row.false_positive_rate,row.recall,marker=marker,color=colour,s=52,
                       edgecolors='white',linewidths=.5,alpha=.9)
    ax.set_title('Training offset' if cutoff=='training_offset' else 'Earlier benign quantile')
    ax.set_xlim(-.03,1.03);ax.set_ylim(-.03,1.03);ax.set_xlabel('Benign false positive rate');ax.grid(alpha=.2)
axes[0].set_ylabel('Attack labelled event recall')
colour_handles=[plt.Line2D([],[],marker='o',color=c,linestyle='',label=n) for _,_,n,c in items]
shape_handles=[plt.Line2D([],[],marker=m,color='#333333',linestyle='',label=n) for n,m in [('Static','o'),('Dual','s'),('Coupled','^')]]
fig.legend(handles=colour_handles+shape_handles,ncol=4,loc='lower center',frameon=False,bbox_to_anchor=(.5,-.06),fontsize=9)
fig.tight_layout(rect=(0,.12,1,1));fig.savefig(out/'tradeoffs.png',dpi=220,bbox_inches='tight');plt.close(fig)
print('Saved',out/'tradeoffs.png')
