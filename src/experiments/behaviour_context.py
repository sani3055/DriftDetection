"""Strictly earlier actor history for CloudTrail research, never outcome labels.

Tied timestamps are transformed as one group before state changes. The history
describes retained records only, not the full underlying AWS request stream.
"""
from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from datetime import datetime, timezone
import math
from typing import Any

import numpy as np

BEHAVIOUR_FEATURES = (
    'actor_log_events_5m', 'actor_log_events_1h', 'actor_log_same_api_1h',
    'actor_failure_fraction_1h', 'actor_log_services_1h', 'actor_log_resources_1h',
    'actor_service_new', 'actor_resource_new', 'actor_source_new', 'actor_agent_new',
    'actor_log_gap_seconds', 'actor_seen_before', 'has_resource',
    'hour_sin', 'hour_cos', 'read_only',
)


def timestamp(record: dict) -> float:
    raw = str(record.get('eventTime') or '')
    if not raw:
        raise ValueError('Behaviour features require an event timestamp')
    dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp timezone is required')
    return dt.timestamp()


def actor_key(record: dict) -> tuple[str, str]:
    identity = record.get('userIdentity') or {}
    if not isinstance(identity, dict):
        identity = {}
    issuer = (identity.get('sessionContext') or {}).get('sessionIssuer') or {}
    for kind, value in [('issuer', issuer.get('arn')), ('arn', identity.get('arn')),
                        ('principal', identity.get('principalId')), ('service', identity.get('invokedBy'))]:
        if value:
            return kind, str(value)
    return 'fallback', str(identity.get('type') or 'Unknown') + ':' + str(identity.get('accountId') or '')


def resource_tokens(record: dict) -> tuple[str, ...]:
    found = set()
    resources = record.get('resources') or []
    if isinstance(resources, list):
        for item in resources:
            if isinstance(item, dict):
                arn = item.get('ARN') or item.get('arn')
                if arn:
                    found.add('arn:' + str(arn))
    request = record.get('requestParameters') or {}
    if isinstance(request, dict):
        for name in ('bucketName', 'tableName', 'functionName', 'secretId', 'roleArn', 'policyArn', 'resourceArn', 'trailName'):
            value = request.get(name)
            if isinstance(value, (str, int)) and str(value):
                found.add(name + ':' + str(value))
    return tuple(sorted(found))


class CausalHistory:
    def __init__(self):
        self.recent: dict[Any, deque] = defaultdict(deque)
        self.last: dict[Any, float] = {}
        self.services: dict[Any, set] = defaultdict(set)
        self.resources: dict[Any, set] = defaultdict(set)
        self.sources: dict[Any, set] = defaultdict(set)
        self.agents: dict[Any, set] = defaultdict(set)
        self.last_group_time: float | None = None

    def clone(self):
        return deepcopy(self)

    def _describe(self, record: dict, now: float) -> tuple[list[float], tuple]:
        actor = actor_key(record)
        recent = self.recent[actor]
        while recent and recent[0][0] < now - 3600:
            recent.popleft()
        api = str(record.get('eventName') or 'Unknown')
        service = str(record.get('eventSource') or 'Unknown')
        source = str(record.get('sourceIPAddress') or '')
        agent = str(record.get('userAgent') or '')
        resources = resource_tokens(record)
        seen = actor in self.last
        gap = min(max(now - self.last[actor], 0), 86400) if seen else 86400
        count = len(recent)
        dt = datetime.fromtimestamp(now, timezone.utc)
        hour = dt.hour + dt.minute / 60 + dt.second / 3600
        values = [
            math.log1p(sum(item[0] >= now - 300 for item in recent)), math.log1p(count),
            math.log1p(sum(item[1] == api for item in recent)),
            sum(item[3] for item in recent) / count if count else 0,
            math.log1p(len({item[2] for item in recent})),
            math.log1p(len({value for item in recent for value in item[4]})),
            float(service not in self.services[actor]),
            float(bool(resources) and any(value not in self.resources[actor] for value in resources)),
            float(bool(source) and source not in self.sources[actor]),
            float(bool(agent) and agent not in self.agents[actor]),
            math.log1p(gap), float(seen), float(bool(resources)),
            math.sin(2 * math.pi * hour / 24), math.cos(2 * math.pi * hour / 24),
            float(record.get('readOnly') is True or str(record.get('readOnly')).lower() == 'true'),
        ]
        error = str(record.get('errorCode') or '')
        failed = bool(error and error not in {'NoError', 'Unknown'})
        update = (actor, now, api, service, failed, resources, source, agent)
        return values, update

    def transform(self, records: list[dict]) -> np.ndarray:
        if not records:
            return np.empty((0, len(BEHAVIOUR_FEATURES)))
        times = [timestamp(record) for record in records]
        if any(a > b for a, b in zip(times, times[1:])):
            raise ValueError('Events must be chronological')
        if self.last_group_time is not None and times[0] <= self.last_group_time:
            raise ValueError('A new call must start strictly after the last complete timestamp group')
        result = []
        index = 0
        while index < len(records):
            end = index + 1
            while end < len(records) and times[end] == times[index]:
                end += 1
            pending = []
            for record in records[index:end]:
                values, update = self._describe(record, times[index])
                result.append(values)
                pending.append(update)
            for actor, now, api, service, failed, resources, source, agent in pending:
                self.recent[actor].append((now, api, service, failed, resources))
                self.last[actor] = now
                self.services[actor].add(service)
                self.resources[actor].update(resources)
                if source: self.sources[actor].add(source)
                if agent: self.agents[actor].add(agent)
            self.last_group_time = times[index]
            index = end
        matrix = np.asarray(result, dtype=float)
        if not np.isfinite(matrix).all():
            raise ValueError('Nonfinite behavioural features')
        return matrix
