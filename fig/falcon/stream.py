import datetime
import requests

from .api import Stream
from ..util import StoppableThread


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
                    self.queue.put(event)

                if self.stopped:
                    break
        finally:
            self.conn.close()


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
        self.connection = requests.get(self.stream.url, headers=headers, stream=True)
        return self.connection

    def events(self):
        return self.open().iter_lines()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
