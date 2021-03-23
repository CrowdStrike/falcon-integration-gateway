from .falcon import StreamManagementThread
from .gcp_translator import GCPWorkerThread
from .queue import falcon_events
from .config import validate_config


if __name__ == "__main__":
    # Central to the fig architecture is a message queue (falcon_events). GCPWorkerThread/s read the queue and process
    # each event. The events are put on queue by StreamingThread. StreamingThread is restarted by StreamManagementThread

    validate_config()

    StreamManagementThread(output_queue=falcon_events).start()
    GCPWorkerThread(input_queue=falcon_events, daemon=True).start()  # TODO: Run multiple reader threads in pool
