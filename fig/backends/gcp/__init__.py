import re
from functools import lru_cache
from google.cloud.securitycenter import Asset, Finding, SecurityCenterClient
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
        self._findings = {}

    def asset(self, event):
        asset_id = event.instance_id

        if asset_id not in self._assets:
            scc = api.SecurityCommandCenter()
            project_number = event.cloud_provider_account_id
            assets = scc.get_asset(project_number, asset_id)
            if len(assets) == 1:
                self._assets[asset_id] = assets[0].asset
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

    def submit_finding(self, finding_id, finding: Finding, org_id: str):
        if org_id not in self._findings:
            self._findings[org_id] = {}

        if finding_id in self._findings[org_id]:
            log.debug("Finding %s already exists in GCP SCC", finding_id)
            return None

        log.info("Submitting finding to GCP SCC")
        scc = api.SecurityCommandCenter()
        finding = scc.get_or_create_finding(finding_id, finding, self.source(org_id))
        self._findings[org_id][finding_id] = finding
        return finding


class Submitter():
    def __init__(self, cache, event):
        self.cache = cache
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        if not self.cache.project_number_accesible(self.gcp_project_number):
            log.warning(
                "Falcon Detection belongs to project %s, but google service account has no acess to this project",
                self.gcp_project_number)
            return

        try:
            finding = self.finding()
        except AssetNotFound:
            log.warning("Corresponding asset not found in GCP Project")

        self.submit_finding(finding)

    def finding(self):
        return Finding(
            name=self.finding_path,
            parent=self.source_path,
            resource_name=self.asset.security_center_properties.resource_name,
            state=Finding.State.ACTIVE,
            external_uri=self.event.falcon_link,
            event_time=self.event.time,
            category=self.event_category,
            severity=self.severity.upper(),

            # TODO: Source specific properties. These properties are managed by the source that writes the finding.
            # The key names in the source_properties map must be between 1 and 255 characters, and must start with
            # a letter and contain alphanumeric characters or underscores only.
            source_properties={
                'ComputerName': self.event.original_event['event']['ComputerName'],
                'Description': self.event.detect_description,
                'ProcessName': self.event.original_event['event']['FileName'],
                'ProcessPath': self.event.original_event['event']['FilePath'],
                'Severity': self.severity,
                'Title': 'Falcon Alert. Instance {}'.format(self.event.instance_id),
                'Category': self.event_category,
                'CommandLine': self.event.original_event['event']['CommandLine']
            }
        )
        # ART Uncomment these fields to force behavior parity with the prior art. Don't.
        # ART finding.severity=self.original_event['event']['Severity']
        # ART finding.source_properties.severity = self.original_event['event']['Severity']
        # ART del(finding.source_properties.CommandLine)

    @property
    def event_category(self):
        # ART Uncomment the following lines to force behavior parity with the prior art. Don't.
        # ART tactic = self.event.original_event['event']['Tactic']
        # ART technique = self.event.original_event['event']['Technique']
        # ART if tactic and technique:
        #    return 'Namespace: TTPs, Category: {}, Classifier: {}'.format(tactic, technique)
        # ART return self.event.detect_description
        return 'Falcon: ' + self.event.detect_name

    @property
    def severity(self):
        return self.event.severity.upper()

    def submit_finding(self, finding):
        return self.cache.submit_finding(self.finding_id, finding, self.org_id)

    @property
    def asset_path(self):
        return self.asset.name

    @property
    def asset(self) -> Asset:
        return self.cache.asset(self.event)

    @property
    def finding_path(self):
        return SecurityCenterClient.finding_path(self.org_id, self.source_id, self.finding_id)

    @property
    def finding_id(self):
        fid = re.sub('^ldt-', '', self.event.event_id)
        return re.sub('[^0-9a-zA-Z]+', '', fid)[0:32]

    @property
    def source_path(self):
        return SecurityCenterClient.source_path(self.org_id, self.source_id)

    @property
    def source_id(self):
        parsed = SecurityCenterClient.parse_source_path(self.source.name)
        return parsed['source']

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
