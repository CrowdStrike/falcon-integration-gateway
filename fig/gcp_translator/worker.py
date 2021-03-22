import threading
from ..log import log


class GCPWorkerThread(threading.Thread):
    def __init__(self, input_queue, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'gcp_worker')
        super().__init__(*args, **kwargs)
        self.input_queue = input_queue

    def run(self):
        while True:
            try:
                event = self.input_queue.get()
                self.process_event(event)
            except Exception:  # pylint: disable=W0703
                log.exception("Error occurred while processing event %s", event)
                self.input_queue.put(event)

    @classmethod
    def process_event(cls, event):
        log.info("Processing detection: %s", event['event']['DetectDescription'])
