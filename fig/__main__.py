from .falcon import FalconAPI, StreamManagementThread
from .gcp_translator import TranslationCache, GCPWorkerThread
from .queue import falcon_events
from .config import config


if __name__ == "__main__":
    # Central to the fig architecture is a message queue (falcon_events). GCPWorkerThread/s read the queue and process
    # each event. The events are put on queue by StreamingThread. StreamingThread is restarted by StreamManagementThread

    config.validate()

    translation_cache = TranslationCache(FalconAPI())

    StreamManagementThread(output_queue=falcon_events).start()
    GCPWorkerThread(input_queue=falcon_events, translation_cache=translation_cache,
                    daemon=True).start()  # TODO: Run multiple reader threads in pool
