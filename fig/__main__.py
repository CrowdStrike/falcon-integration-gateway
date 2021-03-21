import threading
from .falcon import StreamManagementThread
from .log import log
from .queue import falcon_events


def read_and_log_queue():
    while True:
        event = falcon_events.get()
        log.info("Detection: %s", event['event']['DetectDescription'])


if __name__ == "__main__":
    reader = threading.Thread(target=read_and_log_queue)
    reader.start()

    falcon_stream_manager = StreamManagementThread(output_queue=falcon_events)
    falcon_stream_manager.start()
