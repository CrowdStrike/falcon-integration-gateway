from fig.backends import chronicle
from . import aws
from . import aws_sqs
from . import azure
from . import gcp
from . import workspaceone
from ..config import config
from ..log import log


ALL_BACKENDS = {
    'AWS': aws,
    'AWS_SQS': aws_sqs,
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

        accepted_types = self.relevant_event_types
        if accepted_types is None:
            log.info("At least one of the enabled backends will receive all the events")
        else:
            log.info("Enabled backends will only process events with types: %s", accepted_types)

    def process(self, falcon_event):
        for runtime in self.runtimes:
            if self.event_type_is_accepted(runtime, falcon_event) and self.cloud_detection_is_relevant(falcon_event) and runtime.is_relevant(falcon_event):
                runtime.process(falcon_event)

    def cloud_detection_is_relevant(self, falcon_event):
        if falcon_event.original_event.event_type == 'DetectionSummaryEvent':
            if falcon_event.cloud_provider in config.detections_exclude_clouds or falcon_event.cloud_provider is None and 'unrecognized' in config.detections_exclude_clouds:
                log.debug('A detection event is skipped based on cloud based exclusion')
                return False
        return True

    def event_type_is_accepted(self, runtime, falcon_event):
        return runtime.RELEVANT_EVENT_TYPES == "ALL" or falcon_event.original_event.event_type in runtime.RELEVANT_EVENT_TYPES

    @property
    def relevant_event_types(self):
        if any(r.RELEVANT_EVENT_TYPES == "ALL" for r in self.runtimes):
            return None
        return set(typ for r in self.runtimes for typ in r.RELEVANT_EVENT_TYPES)
