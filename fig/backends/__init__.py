from . import aws
from . import azure
from . import gcp
from . import workspaceone
from ..config import config


ALL_BACKENDS = {
    'AWS': aws,
    'AZURE': azure,
    'GCP': gcp,
    'WORKSPACEONE': workspaceone
}


class Backends():
    def __init__(self):
        self.runtimes = {k: v.Runtime()
                         for k, v in ALL_BACKENDS.items()
                         if k in config.backends}
        if len(self.runtimes) == 0:
            raise Exception("No Backend enabled. Exiting.")

    def process(self, falcon_event):
        for runtime in self.runtimes.values():
            if runtime.is_relevant(falcon_event):
                runtime.process(falcon_event)
