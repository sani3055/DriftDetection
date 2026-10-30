import numpy as np
from src.experiments.coherent_scenarios import coherent_perturbation,SCENARIOS
from src.experiments.journal_protocol import normalise


def base():
    return [{'eventName':'GetObject','eventSource':'s3.amazonaws.com','awsRegion':'us-east-1',
             'userIdentity':{'type':'AssumedRole'},'errorCode':'Unknown',
             'requestParameters':{'instanceType':'NotApplicable'}} for _ in range(20)]


def test_coherent_service_identity_and_root_flag():
    for name in SCENARIOS:
        original=base()
        changed,mask=coherent_perturbation(original,name,.25,np.random.default_rng(42))
        assert original==base()
        assert np.array_equal(mask,[normalise(a)!=normalise(b) for a,b in zip(original,changed)])
        for row in changed:
            normal=normalise(row)
            assert normal['isRoot']==int(normal['userIdentitytype']=='Root')
            if normal['eventName'] in ['AttachUserPolicy','CreateAccessKey']:assert normal['eventSource']=='iam.amazonaws.com'
            if normal['eventName']=='DeleteTrail':assert normal['eventSource']=='cloudtrail.amazonaws.com'
            if normal['eventName']=='Invoke':assert normal['eventSource']=='lambda.amazonaws.com'


def test_already_equal_replacements_do_not_become_positive_targets():
    rows=base()
    for row in rows:row['awsRegion']='ap-southeast-1'
    _,mask=coherent_perturbation(rows,'benign_region',1,np.random.default_rng(0))
    assert mask.sum()==0


def test_zero_intensity_is_identity_not_forced_one_row():
    changed,mask=coherent_perturbation(base(),'security_privilege',0,np.random.default_rng(0))
    assert changed==base() and not mask.any()
