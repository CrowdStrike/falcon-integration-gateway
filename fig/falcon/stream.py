import datetime
import requests
import threading

from .api import Api, Stream
from .event import Event
from ..util import StoppableThread
from ..log import log
from ..config import config


class StreamManagementThread(threading.Thread):
    def __init__(self, output_queue, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'cs_mngmt')
        super().__init__(*args, **kwargs)
        self.output_queue = output_queue

    def run(self):
        falcon_api = Api()
        application_id = config.get('falcon', 'application_id')
        for stream in falcon_api.streams(application_id):
            thread = StreamingThread(stream, self.output_queue)
            thread.start()


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
