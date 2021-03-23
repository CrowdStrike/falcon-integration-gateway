import queue
import threading


class FalconEvents(queue.Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 0
        self._lock = threading.Lock()

    def last_offset(self):
        return self.offset

    def get(self, *args, **kwargs):
        event = super().get(*args, **kwargs)
        offset = event.offset
        with self._lock:
            self.offset = max(offset, self.offset)
        return event


falcon_events = FalconEvents()
