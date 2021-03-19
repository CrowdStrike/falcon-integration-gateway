import threading
from .config import config
from .falcon import Api, StreamConnection
from .queue import falcon_events


def read_and_log_queue():
    while True:
        print(falcon_events.get())


if __name__ == "__main__":
    reader = threading.Thread(target=read_and_log_queue)
    reader.start()

    falcon_api = Api()
    application_id = config.get('falcon', 'application_id')
    for s in falcon_api.streams(application_id):
        conn = StreamConnection(s)
        for event in conn.events():
            print(event)
