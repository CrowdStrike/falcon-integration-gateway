import sys
import datetime
import logging
import time
import threading
import requests

from .api import FalconAPI, NoStreamsError
from .models import Event, Stream
from ..util import StoppableThread
from ..log import log
from ..config import config


class StreamManagementThread(threading.Thread):
    """Thread that spins-out sub-threads to manage CrowdStrike Falcon Streaming API"""

    def __init__(self, output_queue, relevant_event_types, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'cs_mngmt')
        super().__init__(*args, **kwargs)
        self.output_queue = output_queue
        self.relevant_event_types = relevant_event_types
        self.application_id = config.get('falcon', 'application_id')

    def run(self):
        while True:
            try:
                workers_died_event = self.start_workers()
                while not workers_died_event.is_set():
                    time.sleep(60)
                log.debug("Restarting stream session")
            except Exception:  # pylint: disable=broad-except
                log.exception("Could not restart stream session")
                sys.exit(1)  # TODO implement re-try mechanism

    def start_workers(self):
        stop_event = threading.Event()
        falcon_api = FalconAPI()
        for stream in self.get_streams(falcon_api):
            StreamingThread(stream, self.output_queue, self.relevant_event_types, stop_event=stop_event).start()
            StreamRefreshThread(self.application_id, stream, falcon_api, stop_event=stop_event).start()
        return stop_event

    def get_streams(self, falcon_api):
        retry_count = int(config.get('falcon', 'reconnect_retry_count'))
        for attempt in range(retry_count):
            try:
                return falcon_api.streams(self.application_id)
            except NoStreamsError:
                if attempt == (retry_count - 1):
                    raise
                log.info("Falcon returns no available streams. Re-trying in 10 seconds.")
                time.sleep(10)
        raise NoStreamsError(self.application_id)


class StreamRefreshThread(StoppableThread):
    def __init__(self, application_id, stream: Stream, falcon_api: FalconAPI, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'cs_refresh')
        super().__init__(*args, **kwargs)
        self.stream = stream
        self.falcon_api = falcon_api
        self.application_id = application_id

    def run(self):
        try:
            self.sleep()
            while not self.stopped:
                self.refresh_stream_session()
                self.sleep()

        finally:
            self.stop()

    def sleep(self):
        time.sleep(self.stream.refresh_interval * 9 / 10)

    def refresh_stream_session(self):
        self.falcon_api.refresh_streaming_session(self.application_id, self.stream)
        log.debug("Refresh of streaming session succeeded")


class StreamingThread(StoppableThread):
    def __init__(self, stream: Stream, queue, relevant_event_types, *args, **kwargs):
        kwargs['name'] = kwargs.get('name', 'cs_stream')
        super().__init__(*args, **kwargs)
        self.stream = stream
        self.conn = StreamingConnection(self.stream, queue.last_offset(self.stream.feed_id))
        self.queue = queue
        self.relevant_event_types = relevant_event_types
        self.event_count = 0
        self.event_count_types = {}

    def run(self):
        try:
            for event in self.conn.events():
                if event:
                    self.process_event(event)

                if self.stopped:
                    break
        except requests.exceptions.ChunkedEncodingError:
            pass  # ChunkedEncodingError is expected when streaming session closes abruptly
        finally:
            log.warning("Streaming Connection was closed.")
            if not self.stopped:
                self.stop()
            else:
                self.conn.close()

    def process_event(self, event):
        event = Event(event, self.stream.feed_id)
        if log.level <= logging.DEBUG:
            self.log_event(event)

        if (self.relevant_event_types is None or event.event_type in self.relevant_event_types) and not event.irrelevant():
            self.queue.put(event)

    def log_event(self, event):
        self.event_count += 1
        self.event_count_types[event.event_type] = self.event_count_types.get(event.event_type, 0) + 1
        if self.event_count % 200 == 0:
            log.debug("Received %d events from the stream. Type breakdown was: %s", self.event_count, self.event_count_types)


class StreamingConnection():
    def __init__(self, stream: Stream, last_seen_offset=0):
        self.stream = stream
        self.connection = None
        self.last_seen_offset = last_seen_offset

    def open(self):
        headers = {
            'Authorization': 'Token %s' % (self.stream.token),
            'Date': datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000'),
            'Connection': 'Keep-Alive'
        }
        log.info("Opening Streaming Connection")
        url = self.stream.url + '&offset={}'.format(self.last_seen_offset + 1 if self.last_seen_offset != 0 else 0)
        self.connection = requests.get(url, headers=headers, stream=True, timeout=60)
        log.info("Established Streaming Connection: %d %s", self.connection.status_code, self.connection.reason)
        self.connection.raise_for_status()
        return self.connection

    def events(self):
        return self.open().iter_lines()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
