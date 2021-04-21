import threading
from .log import log
from .falcon_data import FalconEvent, EventDataError


class WorkerThread(threading.Thread):
    def __init__(self, input_queue, falcon_cache, backends, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'worker')
        super().__init__(*args, **kwargs)
        self.input_queue = input_queue
        self.cache = falcon_cache
        self.backends = backends

    def run(self):
        while True:
            try:
                event = self.input_queue.get()
                self.process_event(event)
            except EventDataError:
                log.exception("Could not translate falcon event to cloud provider")
            except Exception:  # pylint: disable=W0703
                log.exception("Error occurred while processing event %s", event)

    def process_event(self, event):
        falcon_event = FalconEvent(event, self.cache)
        self.backends.process(falcon_event)
