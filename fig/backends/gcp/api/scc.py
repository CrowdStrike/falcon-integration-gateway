import threading
from google.api_core.exceptions import AlreadyExists
from google.cloud import securitycenter
from google.cloud.securitycenter import CreateFindingRequest, Finding, Source
from google.protobuf.field_mask_pb2 import FieldMask
from ....log import log


_sources_lock = threading.Lock()


class SecurityCommandCenter():
    FIG_SOURCE_NAME = 'CrowdStrike Falcon'

    def __init__(self):
        self.client = securitycenter.SecurityCenterClient()

    def get_asset(self, project_number, asset_id):
        asset_iterator = self.client.list_assets(request={
            "parent": self.client.common_project_path(project_number),
            'filter': 'resource_properties.id="{}"'.format(asset_id)
        })
        return list(asset_iterator)

    def list_instances(self, project_number):
        asset_iterator = self.client.list_assets(request={
            "parent": self.client.common_project_path(project_number),
            'filter': 'security_center_properties.resource_type=' + '"google.compute.Instance"',
        })
        return list(asset_iterator)

    def get_fig_source(self, org_id):
        for _, source in enumerate(self.client.list_sources(request={"parent": self._org_name(org_id)})):
            if source.display_name == self.FIG_SOURCE_NAME:
                return source
        return None

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

    def get_or_create_finding(self, finding_id, finding: Finding, source: Source):
        existing = self.get_finding(finding, source)
        if len(existing) == 0:
            try:
                return [self.create_finding(finding_id, finding, source)]
            except AlreadyExists:
                existing = self.get_finding(finding, source)
                if len(existing) == 0:
                    raise

        log.debug("Finding %s already exists in GCP SCC", finding_id)
        return existing[0].finding

    def get_finding(self, finding: Finding, source: Source):
        return list(self.client.list_findings(
            request={
                'parent': source.name,
                'filter': 'name="{}"'.format(finding.name),
            }))

    def create_finding(self, finding_id, finding: Finding, source: Source):
        log.info('Submitting new finding to GCP Security Command Center (finding_id=%s)', finding_id)
        created_finding = self.client.create_finding(
            request=CreateFindingRequest(
                parent=source.name,
                finding_id=finding_id,
                finding=finding,
            )
        )
        return created_finding

    def update_finding(self, finding):
        field_mask = FieldMask(
            paths=['event_time']
        )
        updated_finding = self.client.update_finding(
            request={
                "finding": finding,
                "update_mask": field_mask,
            }
        )
        return updated_finding

    @classmethod
    def _org_name(cls, org_id):
        return 'organizations/{org_id}'.format(org_id=org_id)
