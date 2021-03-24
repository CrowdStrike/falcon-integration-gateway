from functools import lru_cache
from google.cloud.securitycenter import Finding, SecurityCenterClient
from ..log import log
from .errors import GCPAssetNotFound
from .falcon_event import FalconEvent


class GCPSCC():
    def __init__(self, cache, event: FalconEvent):
        self.cache = cache
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.original_event['event']['DetectDescription'])
        if not self.cache.gcp.project_number_accesible(self.gcp_project_number):
            log.warning(
                "Falcon Detection belongs to project %s, but google service account has no acess to this project",
                self.gcp_project_number)
            return

        try:
            self.finding()
        except GCPAssetNotFound:
            log.warning("Corresponding asset not found in GCP Project")

    def finding(self):
        return Finding(
            name=self.finding_path,
            parent=self.source_path,
            resource_name=self.asset_path,
            state=Finding.State.ACTIVE,
            external_uri=self.event.falcon_link,
            event_time=self.event.time,
            # TODO: The additional taxonomy group within findings from a given source. This field is immutable after
            # creation time. Example: "XSS_FLASH_INJECTION".
            # category="MEDIUM_RISK_ONE",

            # TODO: Source specific properties. These properties are managed by the source that writes the finding.
            # The key names in the source_properties map must be between 1 and 255 characters, and must start with
            # a letter and contain alphanumeric characters or underscores only.
            # source_properties= ?,

            # TODO: The severity of the finding. This field is managed by the source that writes the finding.
            # severity= ?
        )

    @property
    def asset_path(self):
        return SecurityCenterClient.asset_path(self.org_id, self.asset)

    @property
    def asset(self):
        return self.cache.gcp.asset(self.event)

    @property
    def finding_path(self):
        return SecurityCenterClient.finding_path(self.org_id, self.source_id, self.finding_id)

    @property
    def finding_id(self):
        return self.event.event_id

    @property
    def source_path(self):
        return SecurityCenterClient.source_path(self.org_id, self.source_id)

    @property
    def source_id(self):
        return self.source.name

    @property
    @lru_cache
    def source(self):
        return self.cache.gcp.source(self.org_id)

    @property
    @lru_cache
    def org_id(self):
        return self.cache.gcp.organization_parent_of(self.gcp_project_number)

    @property
    @lru_cache
    def gcp_project_number(self):
        return self.event.cloud_provider_account_id
