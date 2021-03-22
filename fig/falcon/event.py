import json
from ..config import config


class Event(dict):
    def __init__(self, event_string):
        event = json.loads(event_string.decode('utf-8'))
        super().__init__(event)

    def irrelevant(self):
        return self['metadata']['eventType'] != 'DetectionSummaryEvent' \
            or self.severity < int(config.get('events', 'severity_threshold'))

    @property
    def offset(self):
        return self['metadata']['offset']

    @property
    def severity(self):
        return self['event'].get('Severity', 5)
