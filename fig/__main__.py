from .falcon import FalconAPI, StreamManagementThread
from .gateway import TranslationCache, WorkerThread
from .queue import falcon_events
from .config import config
from .gateway.backends import Backends


if __name__ == "__main__":
    # Central to the fig architecture is a message queue (falcon_events). GCPWorkerThread/s read the queue and process
    # each event. The events are put on queue by StreamingThread. StreamingThread is restarted by StreamManagementThread

    config.validate()

    translation_cache = TranslationCache(FalconAPI())
    backends = Backends()

    StreamManagementThread(output_queue=falcon_events).start()
    WorkerThread(input_queue=falcon_events,
                 translation_cache=translation_cache,
                 backends=Backends(),
                 daemon=True).start()  # TODO: Run multiple reader threads in pool
