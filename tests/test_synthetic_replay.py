from scripts.replay_independent_synthetic_cloud import sanitise


def test_synthetic_input_sanitiser_excludes_access_keys_response_and_labels():
    row={'eventID':'test','eventTime':'2026-09-01T00:00:00Z','eventName':'GetObject',
         'userIdentity':{'type':'IAMUser','arn':'actor','accessKeyId':'excluded-key'},
         'responseElements':{'secret':'excluded-response'},'should_sample':True,
         'requestParameters':{'bucketName':'bucket','sensitiveOther':'excluded-request'}}
    result=sanitise(row)
    assert result['requestParameters']['bucketName']=='bucket'
    assert 'excluded-key' not in repr(result) and 'excluded-response' not in repr(result)
    assert 'excluded-request' not in repr(result) and 'should_sample' not in result
