from falconpy import api_complete as FalconSDK
from ..config import config


class Api():
    CLOUD_REGIONS = {
        'us-1': 'api.crowdstrike.com',
        'us-2': 'api.us-2.crowdstrike.com',
        'eu-1': 'api.eu-1.crowdstrike.com',
        'us-gov-1': 'api.laggar.gcw.crowdstrike.com',
    }

    def __init__(self):
        self.client = FalconSDK.APIHarness(creds={
            'client_id': config.get('falcon', 'client_id'),
            'client_secret': config.get('falcon', 'client_secret')},
            base_url=Api.base_url())

    @classmethod
    def base_url(cls):
        return 'https://' + cls.CLOUD_REGIONS[config.get('falcon', 'cloud_region')]

    def streams(self):
        response = self.client.command(action='listAvailableStreamsOAuth2',
                            parameters={'appId': config.get('falcon', 'application_id')})
        if 'resources' in response['body']:
            print("stream found")
        else:
            print("stream not found")




