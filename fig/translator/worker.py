import threading
from ..log import log
from .errors import EventDataError
from .falcon_event import FalconEvent


class WorkerThread(threading.Thread):
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
        falcon_event = FalconEvent(event, self.cache)
        if falcon_event.cloud_provider is None:
            return
        if falcon_event.cloud_provider != 'GCP':
            return  # TODO implement other providers

        gcp_project_id = falcon_event.cloud_provider_account_id
        if not self.cache.gcp.project_number_accesible(gcp_project_id):
            log.warning(
                "Falcon Detection belongs to project %s, but google service account has no acess to this project",
                gcp_project_id)
            return

        log.info("Processing detection: %s", event['event']['DetectDescription'])
        log.info("    Service provider was: %s", falcon_event.cloud_provider)
