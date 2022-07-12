import json
import re
import datetime
from ..config import config


class Event(dict):
    def __init__(self, event_string, feed_id):
        event = json.loads(event_string.decode('utf-8'))
        self.feed_id = feed_id
        super().__init__(event)

    def irrelevant(self):
        return self.severity < int(config.get('events', 'severity_threshold')) \
            or self.creation_time < self.cut_off_date()

    @property
    def event_type(self):
        return self['metadata']['eventType']

    @property
    def offset(self):
        return self['metadata']['offset']

    @property
    def uid(self):
        return str(self.feed_id) + '_' + str(self.offset)

    @property
    def severity(self):
        return self['event'].get('Severity', 5)

    @property
    def creation_time(self):
        return self.parse_cs_time(self['metadata']['eventCreationTime'])

    @property
    def sensor_id(self):
        return self['event']['SensorId']

    @classmethod
    def parse_cs_time(cls, cs_timestamp):
        return datetime.datetime.utcfromtimestamp(float(cs_timestamp) / 1000.0)

    @classmethod
    def cut_off_date(cls):
        return datetime.datetime.now() - datetime.timedelta(days=int(config.get('events', 'older_than_days_threshold')))


class Stream(dict):
    @property
    def token(self):
        return self['sessionToken']['token']

    @property
    def url(self):
        return self['dataFeedURL']

    @property
    def refresh_interval(self):
        return self['refreshActiveSessionInterval']

    @property
    def partition(self):
        match = re.match(r'.*\/sensors\/entities\/datafeed-actions/v1/([0-9a-zA-Z]+)\?',
                         self['refreshActiveSessionURL'])
        if not match or not match.group(1):
            raise Exception('Cannot parse stream partition from stream data: {}'.format(self))
        return match.group(1)

    @property
    def feed_id(self):
        match = re.match(r'.*\/sensors\/entities\/datafeed/v1/([0-9a-zA-Z]+)\?',
                         self['dataFeedURL'])
        if not match or not match.group(1):
            raise Exception('Cannot parse Feed ID from stream data: {}'.format(self))
        return match.group(1)
