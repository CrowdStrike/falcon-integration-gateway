from . import gcp

ALL_BACKENDS = {
    'GCP': gcp
}


class Backends():
    def __init__(self):
        self.runtimes = {k: v.Runtime() for k, v in ALL_BACKENDS.items()}

    def process(self, falcon_event):
        runtime = self.runtimes.get(falcon_event.cloud_provider)
        if runtime:
            runtime.process(falcon_event)
