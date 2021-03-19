import threading


class StoppableThread(threading.Thread):
    def __init__(self, stop_event=threading.Event(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stop_event = stop_event

    @property
    def stopped(self):
        return self.stop_event.is_set()
