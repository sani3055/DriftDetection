"""Resume the declared factorial/sensitivity grid without replacing evidence."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    log_dir=ROOT/'results/journal_v3_grid_logs'
    log_dir.mkdir(parents=True,exist_ok=True)
    configurations=[]
    for seed,size in [(42,128),(17,128),(73,128),(42,64),(42,256)]:
        for representation in ['ordinal','onehot']:
            for cutoff in ['training_offset','benign_quantile']:
                configurations.append((representation,cutoff,size,seed))
    def run(config):
        representation,cutoff,size,seed=config
        name=f'{representation}_{cutoff}_w{size}_s{seed}'
        if (ROOT/'results/journal_v3'/name/'manifest.json').is_file():
            return {'configuration':name,'status':'preserved_existing'}
        command=[sys.executable,str(ROOT/'scripts/run_journal_comparison.py'),
                 '--representation',representation,'--event-cutoff',cutoff,'--window-size',str(size),'--seed',str(seed)]
        print(f'Starting {name}',flush=True)
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (log_dir/f'{name}.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        print(f'Finished {name}: exit {result.returncode}',flush=True)
        return {'configuration':name,'status':'completed' if result.returncode==0 else 'failed','exit_code':result.returncode}
    results=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for task in as_completed([pool.submit(run,config) for config in configurations]):
            results.append(task.result())
    results.sort(key=lambda row:row['configuration'])
    (log_dir/'grid_status.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'settings':len(results),'failures':sum(row['status']=='failed' for row in results)},indent=2),flush=True)
    if any(row['status']=='failed' for row in results):raise SystemExit(1)


if __name__=='__main__':main()
