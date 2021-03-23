from ..falcon import Event
from .cache import TranslationCache


class Translation():
    def __init__(self, original_event: Event, cache: TranslationCache):
        self.original_event = original_event
        self.cache = cache

    @property
    def device_details(self):
        return self.cache.falcon.device_details(self.original_event.sensor_id)
