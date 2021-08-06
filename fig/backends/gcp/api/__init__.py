from google.cloud.resourcemanager import FoldersClient, Project, ProjectsClient
from .scc import SecurityCommandCenter


def project(project_number: int):
    client = ProjectsClient()
    return client.get_project(name="projects/" + project_number)


def folder(folder_path: str):
    client = FoldersClient()
    return client.get_folder(name=folder_path)


def project_get_parent_org(prj: Project):
    client = ProjectsClient()
    item = prj
    while True:
        parent = item.parent
        parsed = client.parse_common_organization_path(parent)
        if parsed:
            return parsed['organization']
        parsed = client.parse_common_folder_path(parent)
        if parsed:
            item = folder(parent)
        else:
            raise Exception('Could not detemine parent organization for GCP project {}, last parent determined was: {}'.format(prj.name, parent))


__all__ = ['project', 'SecurityCommandCenter']
