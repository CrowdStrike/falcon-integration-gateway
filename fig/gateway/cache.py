from .errors import EventDataError, FalconAPIDataError
from .backends import gcp


class TranslationCache():
    def __init__(self, falcon_api):
        self.falcon = FalconCache(falcon_api)
        self.gcp = GCPCache()


class FalconCache():
    def __init__(self, falcon_api):
        self.falcon_api = falcon_api
        self._host_detail = {}

    def device_details(self, sensor_id):
        if not sensor_id:
            return EventDataError("Cannot process event. SensorId field is missing: ")

        if sensor_id not in self._host_detail:
            resources = self.falcon_api.device_details(sensor_id)
            if len(resources) > 1:
                raise FalconAPIDataError(
                    'Cannot process event for device: {}, multiple devices exists'.format(sensor_id))
            if len(resources) == 0:
                raise FalconAPIDataError('Cannot process event for device {}, device not known'.format(sensor_id))
            self._host_detail[sensor_id] = self.falcon_api.device_details(sensor_id)[0]

        return self._host_detail[sensor_id]


class GCPCache():
    def __init__(self):
        self._projects = {}
        self._sources = {}
        self._assets = {}

    def asset(self, event):
        asset_id = event.device_details['instance_id']

        if asset_id not in self._assets:
            scc = gcp.api.SecurityCommandCenter()
            project_number = event.cloud_provider_account_id
            assets = scc.get_asset(project_number, event.device_details['instance_id'])
            if len(assets) == 1:
                self._assets[asset_id] = assets[0]
            elif len(assets) == 0:
                raise gcp.AssetNotFound("Asset {} not found in GCP Project {}".format(asset_id, project_number))
            else:
                raise gcp.APIDataError(
                    "Multiple assets found with ID={} within GCP Project {}".format(asset_id, project_number))
        return self._assets[asset_id]

    def source(self, org_id):
        if org_id not in self._sources:
            scc = gcp.api.SecurityCommandCenter()
            self._sources[org_id] = scc.get_or_create_fig_source(org_id)
        return self._sources[org_id]

    def organization_parent_of(self, project_id):
        project = self.projects[project_id]
        if 'type' not in project.parent or project.parent['type'] != 'organization':
            raise gcp.APIDataError('Could not determine parent organization for gcp project {}'.format(project_id))
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
        self._projects = gcp.api.projects()
