from fig.backends import chronicle
from . import aws
from . import azure
from . import gcp
from . import workspaceone
from ..config import config


ALL_BACKENDS = {
    'AWS': aws,
    'AZURE': azure,
    'GCP': gcp,
    'WORKSPACEONE': workspaceone,
    'CHRONICLE': chronicle
}


class Backends():
    def __init__(self):
        self.runtimes = [v.Runtime()
                         for k, v in ALL_BACKENDS.items()
                         if k in config.backends]
        if len(self.runtimes) == 0:
            raise Exception("No Backend enabled. Exiting.")

    def process(self, falcon_event):
        for runtime in self.runtimes:
            if falcon_event.original_event.event_type in runtime.RELEVANT_EVENT_TYPES and runtime.is_relevant(falcon_event):
                runtime.process(falcon_event)

    @property
    def relevant_event_types(self):
        return set(typ for r in self.runtimes for typ in r.RELEVANT_EVENT_TYPES)
