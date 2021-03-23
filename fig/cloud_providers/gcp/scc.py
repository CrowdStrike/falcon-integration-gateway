import threading
from google.cloud import securitycenter
from ...log import log


_sources_lock = threading.Lock()


class SecurityCommandCenter():
    FIG_SOURCE_NAME = 'CrowdStrike Falcon'

    def __init__(self):
        self.client = securitycenter.SecurityCenterClient()

    def get_fig_source(self, org_id):
        for i, source in enumerate(self.client.list_sources(request={"parent": self._org_name(org_id)})):
            if source.display_name == self.FIG_SOURCE_NAME:
                return source

    def get_or_create_fig_source(self, org_id):
        source = self.get_fig_source(org_id)
        if source is not None:
            return source

        with _sources_lock:
            source = self.get_fig_source(org_id)
            if source is not None:
                return source
            return self.create_fig_source(org_id)

    def create_fig_source(self, org_id):
        log.info("Creating new Finding Source in GCP Security Command Center (org_id=%s)", org_id)
        return self.client.create_source(
            request={
                "parent": self._org_name(org_id),
                "source": {
                    "display_name": self.FIG_SOURCE_NAME,
                    "description": "CrowdStrike Falcon findings forwarded by falcon-integration-gateway",
                },
            }
        )

    @classmethod
    def _org_name(cls, org_id):
        return 'organizations/{org_id}'.format(org_id=org_id)
