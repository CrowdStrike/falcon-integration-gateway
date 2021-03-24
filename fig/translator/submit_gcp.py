from ..log import log
from .falcon_event import FalconEvent


class GCPSCC():
    def __init__(self, cache, event: FalconEvent):
        self.cache = cache
        self.event = event

    def submit(self):
        if not self.cache.gcp.project_number_accesible(self.gcp_project_number):
            log.warning(
                "Falcon Detection belongs to project %s, but google service account has no acess to this project",
                self.gcp_project_number)
            return
        print(self.source)

        log.info("Processing detection: %s", event.original_event['event']['DetectDescription'])

    @property
    def source(self):
        return self.cache.gcp.source(org_id)

    @property
    def org_id(self):
        return self.cache.gcp.organization_parent_of(self.gcp_project_number)

    @property
    def gcp_project_number(self):
        return self.event.cloud_provider_account_id
