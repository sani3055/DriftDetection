"""Count identifier ambiguity in a bounded source-order sample; export no identifiers."""
import json
from pathlib import Path
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_primary_rich_context import COLS


def main():
    path=Path('D:/Projects/CloudGuard/data/nineteenFeaturesDf.csv')
    split=json.loads((ROOT/'data/processed/temporal_split.json').read_text())
    months=split['train']+split['validation']+split['test']
    remaining={month:1000 for month in months};parts=[]
    for chunk in pd.read_csv(path,usecols=COLS,dtype=str,keep_default_na=False,chunksize=100000):
        chunk['_month']=chunk.eventTime.str.slice(0,7)
        for month,group in chunk.groupby('_month',sort=False):
            if month in remaining and remaining[month]>0:
                take=group.head(remaining[month]);parts.append(take);remaining[month]-=len(take)
        if not any(remaining.values()):break
    frame=pd.concat(parts,ignore_index=True)
    ids=frame.eventID.str.strip()
    missing=ids.str.lower().isin(['','nan','none','null','unknown'])
    duplicate_mask=~missing & ids.duplicated(keep=False)
    duplicated=frame[duplicate_mask].copy()
    duplicated['_payload_hash']=pd.util.hash_pandas_object(duplicated[COLS],index=False).to_numpy()
    groups=duplicated.groupby('eventID')
    payload_counts=groups._payload_hash.nunique()
    time_counts=groups.eventTime.nunique()
    report={'sample_rows':len(frame),'missing_or_placeholder_id_rows':int(missing.sum()),
            'rows_in_repeated_nonmissing_id_groups':len(duplicated),'repeated_nonmissing_id_groups':len(payload_counts),
            'same_selected_payload_id_groups':int((payload_counts==1).sum()),
            'different_selected_payload_id_groups':int((payload_counts>1).sum()),
            'different_timestamp_id_groups':int((time_counts>1).sum()),
            'privacy':'aggregate counts only; no raw identifiers or identity fields retained'}
    out=ROOT/'results/journal_v4_primary_rich_context';out.mkdir(parents=True,exist_ok=True)
    (out/'identifier_audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
