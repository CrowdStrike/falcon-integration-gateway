import queue
import threading


class FalconEvents(queue.Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = {}
        self._lock = threading.Lock()

    def last_offset(self, feed_id):
        return self.offset.get(feed_id, 0)

    def get(self, *args, **kwargs):
        event = super().get(*args, **kwargs)
        feed_id = event.feed_id
        offset = event.offset
        with self._lock:
            self.offset[feed_id] = max(offset, self.last_offset(feed_id))
        return event


falcon_events = FalconEvents()
