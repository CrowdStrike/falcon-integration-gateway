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

    def runtime(self, cloud_provider):
        # Convert the cloud_provider field from Falcon API to internal backend name
        if cloud_provider == 'AWS_EC2':
            cloud_provider = 'AWS'
        return self.runtimes.get(cloud_provider)

    def process(self, falcon_event):
        runtime = self.runtime(falcon_event.cloud_provider)
        if runtime:
            runtime.process(falcon_event)
        if falcon_event.mdm_identifier is not None:
            self.runtimes.get('WORKSPACEONE').process(falcon_event)
