from google.cloud import resource_manager


def projects():
    client = resource_manager.Client()

    return {p.number: p for p in client.list_projects()}
