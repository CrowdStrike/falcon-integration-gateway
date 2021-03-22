import json


class Event(dict):
    def __init__(self, event_string):
        event = json.loads(event_string.decode('utf-8'))
        super().__init__(event)

    def irrelevant(self):
        return self['metadata']['eventType'] != 'DetectionSummaryEvent'
