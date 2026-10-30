"""Execute every declared v4 cell with bounded CPU concurrency."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seeds',nargs='+',type=int,default=[42])
    args=parser.parse_args()
    logs=ROOT/'results/journal_v4_tiesafe_grid_logs'
    logs.mkdir(parents=True,exist_ok=True)
    cells=list(itertools.product([('event','ordinal'),('event','onehot'),('behaviour','none'),
        ('combined','ordinal'),('combined','onehot')],['narrow','broad'],['training_offset','benign_quantile'],args.seeds))
    def run(cell):
        (inputs,encoding),coverage,cutoff,seed=cell
        name=f'{inputs}_{encoding}_{coverage}_{cutoff}_s{seed}'
        if (ROOT/'results/journal_v4_tiesafe'/name/'manifest.json').exists():return {'name':name,'exit_code':0,'cached':True}
        with (logs/(name+'.log')).open('w',encoding='utf-8') as log:
            result=subprocess.run([sys.executable,'-u',str(ROOT/'scripts/run_behaviour_tie_safe.py'),
                '--inputs',inputs,'--encoding',encoding,'--coverage',coverage,'--event-cutoff',cutoff,'--seed',str(seed)],
                cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        return {'name':name,'exit_code':result.returncode,'cached':False}
    status=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for task in as_completed([pool.submit(run,cell) for cell in cells]):
            row=task.result();status.append(row)
            status_name='grid_status_s'+'-'.join(map(str,args.seeds))+'.json'
            (logs/status_name).write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
            print(f'{len(status)}/{len(cells)} {row}',flush=True)
    if any(row['exit_code'] for row in status):raise SystemExit(1)


if __name__=='__main__':main()
