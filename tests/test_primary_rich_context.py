import pandas as pd
import pytest
from scripts.run_primary_rich_context import COLS,convert,deduplicate_sample


def test_primary_export_conversion_excludes_access_keys_and_response_secrets():
    row={key:'' for key in COLS}
    row.update(eventID='test',eventTime='2026-01-01T00:00:00Z',userIdentitytype='IAMUser',
               userIdentityarn='transient-identity',userIdentityaccessKeyId='do-not-read',
               responseElements='do-not-read-either')
    result=convert(row)
    assert 'userIdentityaccessKeyId' not in COLS
    assert 'do-not-read' not in repr(result)
    assert result['userIdentity']['arn']=='transient-identity'


def test_duplicates_are_removed_only_when_all_selected_fields_agree():
    row={key:'' for key in COLS};row.update(eventID='same',eventTime='2020-01-01T00:00:00Z')
    unique,count=deduplicate_sample(pd.DataFrame([row,row]))
    assert len(unique)==1 and count==1
    with pytest.raises(ValueError):
        deduplicate_sample(pd.DataFrame([row,{**row,'eventName':'Different'}]))
