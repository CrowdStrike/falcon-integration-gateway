import re
from functools import lru_cache
from google.cloud.securitycenter import Asset, Finding, SecurityCenterClient
import google.api_core.exceptions
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
            project_number = event.cloud_provider_account_id
            assets = self.scc.get_asset(project_number, asset_id)
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
            self._sources[org_id] = self.scc.get_or_create_fig_source(org_id)
        return self._sources[org_id]

    def organization_parent_of(self, project_id):
        project = self.project(project_id)
        return api.project_get_parent_org(project)

    def project_number_accesible(self, project_number: int) -> bool:
        try:
            return self.project(project_number) is not None
        except google.api_core.exceptions.PermissionDenied:
            return False

    def project(self, project_number: int):
        if project_number not in self._projects:
            self._projects[project_number] = api.project(project_number)
        return self._projects[project_number]

    def submit_finding(self, finding_id, finding: Finding, org_id: str):
        if org_id not in self._findings:
            self._findings[org_id] = {}

        if finding_id in self._findings[org_id]:
            log.debug("Finding %s already exists in GCP SCC", finding_id)
            return None

        finding = self.scc.get_or_create_finding(finding_id, finding, self.source(org_id))
        self._findings[org_id][finding_id] = finding
        return finding

    @property
    @lru_cache
    def scc(self):
        return api.SecurityCommandCenter()


class Submitter():
    def __init__(self, cache, event):
        self.cache = cache
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        if not self.cache.project_number_accesible(self.gcp_project_number):
            log.warning(
                "Cannot access GCP project (number=%s) to report malicious behaviour to GCP Security Command Center. Please grant 'roles/securitycenter.admin' role to this service account in every GCP organization that needs to have CrowdStrike detections forwarded to SCC.",
                self.gcp_project_number)
            return

        try:
            finding = self.finding()
        except AssetNotFound:
            log.warning("Corresponding asset not found in GCP Project")
            return

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
            source_properties={
                'FalconEventId': self.event.event_id,
                'ComputerName': self.event.original_event['event']['ComputerName'],
                'Description': self.event.detect_description,
                'Severity': self.severity,
                'Title': 'Falcon Alert. Instance {}'.format(self.event.instance_id),
                'Category': self.event_category,
                'ProcessInformation': {
                    'ProcessName': self.event.original_event['event']['FileName'],
                    'ProcessPath': self.event.original_event['event']['FilePath'],
                    'CommandLine': self.event.original_event['event']['CommandLine']
                },
            }
        )
        # ART Uncomment these fields to force behavior parity with the prior art. Don't.
        # ART finding.severity=self.original_event['event']['Severity']
        # ART finding.source_properties.severity = self.original_event['event']['Severity']
        # ART del(finding.source_properties.CommandLine)
        # ART del(finding.source_properties.FalconEventId)

    @property
    def event_category(self):
        # ART Uncomment the following lines to force behavior parity with the prior art. Don't.
        # ART tactic = self.event.original_event['event']['Tactic']
        # ART technique = self.event.original_event['event']['Technique']
        # ART if tactic and technique:
        #    return 'Namespace: TTPs, Category: {}, Classifier: {}'.format(tactic, technique)
        # ART return self.event.detect_description
        return self.event.detect_name

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
    @lru_cache
    def finding_id(self):
        event_id = re.sub('[^0-9a-zA-Z]+', '', self.event.event_id)
        creation_time = str(hex(int(self.event.original_event['metadata']['eventCreationTime'])))[-6:]
        return (event_id + creation_time)[-32:]

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
        log.info("GCP Backend is enabled.")
        self.cache = Cache()

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return falcon_event.cloud_provider == 'GCP'

    def process(self, falcon_event):
        Submitter(self.cache, falcon_event).submit()


__all__ = ['Runtime']
