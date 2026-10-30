"""Apply the same source-schema audit to the supplementary trace selection."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import scripts.audit_external_cloudtrail_traces as audit

audit.OUT=Path(__file__).resolve().parents[1]/'data/external/splunk_cloudtrail_v4_extension'
if __name__=='__main__':audit.main()
