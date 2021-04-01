from . import azure
from . import gcp
from ..config import config

ALL_BACKENDS = {
    'Azure': azure,
    'GCP': gcp
}


class Backends():
    def __init__(self):
        self.runtimes = {k: v.Runtime()
                         for k, v in ALL_BACKENDS.items()
                         if k in config.backends}
        if len(self.runtimes) == 0:
            raise Exception("No Backend enabled. Exiting.")

    def process(self, falcon_event):
        runtime = self.runtimes.get(falcon_event.cloud_provider)
        if runtime:
            runtime.process(falcon_event)
