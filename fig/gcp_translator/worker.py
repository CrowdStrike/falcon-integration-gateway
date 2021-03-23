import threading
from ..log import log
from .errors import EventDataError
from .translation import Translation


class GCPWorkerThread(threading.Thread):
    def __init__(self, input_queue, translation_cache, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'gcp_worker')
        super().__init__(*args, **kwargs)
        self.input_queue = input_queue
        self.cache = translation_cache

    def run(self):
        while True:
            try:
                event = self.input_queue.get()
                self.process_event(event)
            except EventDataError:
                log.exception("Could not translate event to GCP SCC")
            except Exception:  # pylint: disable=W0703
                log.exception("Error occurred while processing event %s", event)
                self.input_queue.put(event)

    def process_event(self, event):
        translation = Translation(event, self.cache)
        log.info("Processing detection: %s", event['event']['DetectDescription'])
        if 'service_provider' in translation.device_details:
            log.info("    Service provider was: %s", translation.device_details['service_provider'])
