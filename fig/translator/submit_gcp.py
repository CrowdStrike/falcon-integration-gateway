from ..log import log
from .falcon_event import FalconEvent
from ..cloud_providers import gcp


class GCPSCC():
    def __init__(self, cache):
        self.cache = cache

    def submit(self, event: FalconEvent):
        gcp_project_id = event.cloud_provider_account_id
        if not self.cache.gcp.project_number_accesible(gcp_project_id):
            log.warning(
                "Falcon Detection belongs to project %s, but google service account has no acess to this project",
                gcp_project_id)
            return
        org_id = self.cache.gcp.organization_parent_of(gcp_project_id)
        scc = gcp.SecurityCommandCenter()
        source = scc.get_or_create_fig_source(org_id)
        print(source)

        log.info("Processing detection: %s", event.original_event['event']['DetectDescription'])
