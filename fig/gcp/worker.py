import threading
from ..log import log


class GCPWorkerThread(threading.Thread):
    def __init__(self, input_queue, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'gcp_worker')
        super().__init__(*args, **kwargs)
        self.input_queue = input_queue

    def run(self):
        while True:
            event = self.input_queue.get()
            log.info("Processing detection: %s", event['event']['DetectDescription'])
