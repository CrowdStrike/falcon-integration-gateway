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


__all__ = ['api', 'APIDataError', 'AssetNotFound', 'Cache']
