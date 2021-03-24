from ..falcon import Event
from .cache import TranslationCache


class FalconEvent():
    def __init__(self, original_event: Event, cache: TranslationCache):
        self.original_event = original_event
        self.cache = cache

    @property
    def device_details(self):
        return self.cache.falcon.device_details(self.original_event.sensor_id)

    @property
    def cloud_provider(self):
        return self.device_details.get('service_provider', None)

    @property
    def cloud_provider_account_id(self):
        return self.device_details.get('service_provider_account_id')

    @property
    def falcon_link(self):
        return self.original_event['event']['FalconHostLink']

    @property
    def event_id(self):
        return self.original_event['event']['DetectId']

    @property
    def time(self):
        return self.original_event.creation_time
