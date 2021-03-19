from falconpy import api_complete as FalconSDK
from ..config import config
from ..log import log


class ApiError(Exception):
    pass


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
        app_id = config.get('falcon', 'application_id')
        response = self.client.command(action='listAvailableStreamsOAuth2',
                            parameters={'appId': config.get('falcon', 'application_id')})
        if 'resources' in response['body']:
            log.debug("stream found")
        else:
            raise ApiError('Falcon Streaming API not discovered. This may be caused by second instance of this application already running in your environment with the same application_id={}, or by missing streaming API capability.'.format(app_id))




