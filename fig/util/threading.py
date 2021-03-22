import threading
from ..log import log


class StoppableThread(threading.Thread):
    def __init__(self, *args, stop_event=threading.Event(), **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = stop_event

    @property
    def stopped(self):
        return self.stop_event.is_set()

    def stop(self):
        if not self.stopped:
            log.info("Thread requested to stop")
            self.stop_event.set()
