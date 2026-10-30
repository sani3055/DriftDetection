import json
from scripts.audit_external_cloudtrail_traces import decode_objects,native_records
from scripts.run_external_trace_replay import event_key


def test_json_lines_and_native_wrapper_are_parsed_without_inventing_labels():
    event={'eventTime':'2021-01-01T00:00:00Z','eventName':'GetObject','eventID':'x'}
    data=(json.dumps({'Records':[event]})+'\n'+json.dumps({'_raw':json.dumps(event)})).encode()
    records=[row for value in decode_objects(data) for row in native_records(value)]
    assert len(records)==2 and all('should_sample' not in row for row in records)
    assert event_key(records[0])==event_key(records[1])


def test_non_native_schema_is_not_silently_converted_to_attack():
    assert list(native_records({'api':{'operation':'GetObject'},'time':'2020'}))==[]
