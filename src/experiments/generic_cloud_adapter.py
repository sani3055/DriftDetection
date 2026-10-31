"""Lossful, explicitly cloud-neutral adapter; never reads source labels."""


def adapt_generic_event(event):
    action = event.get('action')
    timestamp = event.get('timestamp')
    actor = event.get('actor_id')
    actor_type = event.get('actor_type')
    event_id = event.get('event_id')
    if not all(isinstance(x, str) and x for x in (action, timestamp, actor, actor_type, event_id)):
        raise ValueError('Missing core synthetic event fields')
    result = event.get('result')
    if result not in {'success', 'failure', 'denied'}:
        raise ValueError('Unexpected synthetic outcome')
    resource = event.get('resource_id')
    return {'eventID': event_id, 'eventTime': timestamp, 'eventName': action,
            'eventSource': 'generic:' + action.split('.', 1)[0],
            'awsRegion': event.get('source_region'), 'sourceIPAddress': event.get('source_ip'),
            'errorCode': '' if result == 'success' else 'generic:' + result,
            'userIdentity': {'type': actor_type, 'principalId': actor},
            'resources': [{'ARN': str(resource)}] if resource else []}
