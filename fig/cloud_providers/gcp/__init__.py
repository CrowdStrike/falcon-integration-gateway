from google.cloud import resource_manager
from .scc import SecurityCommandCenter


def projects():
    client = resource_manager.Client()

    return {p.number: p for p in client.list_projects()}


__all__ = ['projects', 'SecurityCommandCenter']
