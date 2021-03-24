from functools import lru_cache
from google.cloud.securitycenter import Finding, SecurityCenterClient
from ...log import log
from . import api


class APIDataError(Exception):
    pass


class AssetNotFound(APIDataError):
    pass


class Cache():
    def __init__(self):
        self._projects = {}
        self._sources = {}
        self._assets = {}

    def asset(self, event):
        asset_id = event.device_details['instance_id']

        if asset_id not in self._assets:
            scc = api.SecurityCommandCenter()
            project_number = event.cloud_provider_account_id
            assets = scc.get_asset(project_number, event.device_details['instance_id'])
            if len(assets) == 1:
                self._assets[asset_id] = assets[0]
            elif len(assets) == 0:
                raise AssetNotFound("Asset {} not found in GCP Project {}".format(asset_id, project_number))
            else:
                raise APIDataError(
                    "Multiple assets found with ID={} within GCP Project {}".format(asset_id, project_number))
        return self._assets[asset_id]

    def source(self, org_id):
        if org_id not in self._sources:
            scc = api.SecurityCommandCenter()
            self._sources[org_id] = scc.get_or_create_fig_source(org_id)
        return self._sources[org_id]

    def organization_parent_of(self, project_id):
        project = self.projects[project_id]
        if 'type' not in project.parent or project.parent['type'] != 'organization':
            raise APIDataError('Could not determine parent organization for gcp project {}'.format(project_id))
        return project.parent['id']

    def project_number_accesible(self, project_number: int) -> bool:
        if project_number in self.projects:
            return True
        self._refresh_projects()
        return project_number in self.projects

    @property
    def projects(self):
        if not self._projects:
            self._refresh_projects()
        return self._projects

    def _refresh_projects(self):
        self._projects = api.projects()


class Submitter():
    def __init__(self, cache, event):
        self.cache = cache
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.original_event['event']['DetectDescription'])
        if not self.cache.project_number_accesible(self.gcp_project_number):
            log.warning(
                "Falcon Detection belongs to project %s, but google service account has no acess to this project",
                self.gcp_project_number)
            return

        try:
            self.finding()
        except AssetNotFound:
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
        return self.cache.asset(self.event)

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
        return self.cache.source(self.org_id)

    @property
    @lru_cache
    def org_id(self):
        return self.cache.organization_parent_of(self.gcp_project_number)

    @property
    @lru_cache
    def gcp_project_number(self):
        return self.event.cloud_provider_account_id


class Runtime():
    def __init__(self):
        self.cache = Cache()

    def process(self, falcon_event):
        Submitter(self.cache, falcon_event).submit()


__all__ = ['Runtime']
