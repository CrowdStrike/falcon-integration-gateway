import datetime
import requests

from .api import Stream
from .event import Event
from ..util import StoppableThread
from ..log import log


class StreamingThread(StoppableThread):
    def __init__(self, stream: Stream, queue, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'cs_stream')
        super().__init__(*args, **kwargs)
        self.conn = StreamingConnection(stream)
        self.queue = queue

    def run(self):
        try:
            for event in self.conn.events():
                if event:
                    self.process_event(event)

                if self.stopped:
                    break
        finally:
            log.warning("Streaming Connection was closed.")
            self.conn.close()

    def process_event(self, event):
        e = Event(event)
        if not e.irrelevant():
            self.queue.put(e)


class StreamingConnection():
    def __init__(self, stream: Stream):
        self.stream = stream
        self.connection = None

    def open(self):
        headers = {
            'Authorization': 'Token %s' % (self.stream.token),
            'Date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000'),
            'Connection': 'Keep-Alive'
        }
        log.info("Opening Streaming Connection")
        self.connection = requests.get(self.stream.url, headers=headers, stream=True)
        return self.connection

    def events(self):
        return self.open().iter_lines()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None