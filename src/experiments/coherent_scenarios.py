"""Consistent seven-field counterfactuals; never real attack ground truth."""
from copy import deepcopy
import numpy as np

from src.experiments.journal_protocol import normalise

SCENARIOS=('stable','benign_region','benign_identity','benign_lambda',
           'security_privilege','security_defense','security_credential')


def coherent_perturbation(records: list[dict], scenario: str, intensity: float,
                          rng: np.random.Generator) -> tuple[list[dict],np.ndarray]:
    if scenario not in SCENARIOS:raise ValueError(scenario)
    if not 0<=intensity<=1:raise ValueError('Intensity outside [0,1]')
    current=deepcopy(records)
    if scenario=='stable' or not len(records) or intensity==0:
        return current,np.zeros(len(records),dtype=bool)
    chosen=rng.choice(len(records),size=max(1,int(len(records)*intensity)),replace=False)
    tuples={
        'benign_lambda':('Invoke','lambda.amazonaws.com','AssumedRole'),
        'security_privilege':('AttachUserPolicy','iam.amazonaws.com','Root'),
        'security_defense':('DeleteTrail','cloudtrail.amazonaws.com','IAMUser'),
        'security_credential':('CreateAccessKey','iam.amazonaws.com','IAMUser'),
    }
    for index in chosen:
        row=current[index]
        if scenario=='benign_region':row['awsRegion']='ap-southeast-1'
        elif scenario=='benign_identity':row['userIdentity']={'type':'AWSService'}
        else:
            operation,service,identity=tuples[scenario]
            row.update({'eventName':operation,'eventSource':service,'userIdentity':{'type':identity},
                        'errorCode':'Unknown','requestParameters':{'instanceType':'NotApplicable'}})
    changed=np.asarray([normalise(before)!=normalise(after) for before,after in zip(records,current)],dtype=bool)
    return current,changed
