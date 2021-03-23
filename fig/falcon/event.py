import json
import datetime
from ..config import config


class Event(dict):
    def __init__(self, event_string):
        event = json.loads(event_string.decode('utf-8'))
        super().__init__(event)

    def irrelevant(self):
        return self['metadata']['eventType'] != 'DetectionSummaryEvent' \
            or self.severity < int(config.get('events', 'severity_threshold')) \
            or self.creation_time < self.cut_off_date()

    @property
    def offset(self):
        return self['metadata']['offset']

    @property
    def severity(self):
        return self['event'].get('Severity', 5)

    @property
    def creation_time(self):
        return self.parse_cs_time(self['metadata']['eventCreationTime'])

    @classmethod
    def parse_cs_time(cls, cs_timestamp):
        return datetime.datetime.utcfromtimestamp(float(cs_timestamp) / 1000.0)

    @classmethod
    def cut_off_date(cls):
        return datetime.datetime.now() - datetime.timedelta(days=int(config.get('events', 'older_than_days_threshold')))
