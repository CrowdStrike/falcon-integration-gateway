import json
import re
import datetime
from ..config import config
from ..log import log


class Event(dict):
    def __init__(self, event_string, feed_id):
        event = json.loads(event_string.decode('utf-8'))
        self.feed_id = feed_id
        super().__init__(event)

    def __eq__(self, other):
        if not isinstance(other, Event):
            return False
        return super().__eq__(self, other) and self.feed_id == other.feed_id

    def irrelevant(self):
        severity = self.mapped_severity()
        threshold = int(config.get('events', 'severity_threshold'))
        cutoff = self.cut_off_date()

        # Check severity threshold
        if severity < threshold:
            log.debug("Event skipped: severity %d below threshold %d (offset: %s)",
                      severity, threshold, self.offset)
            return True

        # Check cut-off date
        if self.creation_time < cutoff:
            # Format datetime objects directly
            event_date = self.creation_time.strftime('%Y-%m-%d %H:%M:%S')
            cutoff_date = cutoff.strftime('%Y-%m-%d %H:%M:%S')

            log.debug("Event skipped: creation time %s before cut-off date %s (offset: %s)",
                      event_date, cutoff_date, self.offset)
            return True

        return False

    def mapped_severity(self):
        """Map CrowdStrike severity to internal 1-5 scale"""
        severity_name = self['event'].get('SeverityName', 'Critical')
        name_to_value = {
            "Informational": 1,
            "Low": 2,
            "Medium": 3,
            "High": 4,
            "Critical": 5
        }
        return name_to_value.get(severity_name, 5)  # Default to 5 (highest) if unknown

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
        # return self['event']['SensorId']
        return self['event'].get('SensorId') or self['event'].get('AgentId')

    @property
    def computer_name(self):
        return self['event'].get('ComputerName') or self['event'].get('Hostname')

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
        if 'feed_id' not in self:
            match = re.match(r'.*\/sensors\/entities\/datafeed/v1/([0-9a-zA-Z]+)\?',
                             self['dataFeedURL'])
            if not match or not match.group(1):
                raise Exception('Cannot parse Feed ID from stream data: {}'.format(self))
            self['feed_id'] = match.group(1)
        return self['feed_id']
