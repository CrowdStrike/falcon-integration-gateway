from .falcon import FalconAPI, StreamManagementThread
from .worker import WorkerThread
from .queue import falcon_events
from .config import config
from .backends import Backends
from .falcon_data import FalconCache


if __name__ == "__main__":
    # Central to the fig architecture is a message queue (falcon_events). GCPWorkerThread/s read the queue and process
    # each event. The events are put on queue by StreamingThread. StreamingThread is restarted by StreamManagementThread

    config.validate()

    falcon_cache = FalconCache(FalconAPI())
    backends = Backends()

    StreamManagementThread(output_queue=falcon_events).start()

    for i in range(int(config.get('main', 'worker_threads'))):
        WorkerThread(name='worker-' + str(i),
                     input_queue=falcon_events,
                     falcon_cache=falcon_cache,
                     backends=backends,
                     daemon=True).start()
