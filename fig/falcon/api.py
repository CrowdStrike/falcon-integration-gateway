from falconpy import api_complete as FalconSDK
from ..config import config


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

    def streams(self, app_id):
        response = self.client.command(action='listAvailableStreamsOAuth2',
                                       parameters={'appId': config.get('falcon', 'application_id')})
        body = response['body']
        if 'resources' in body and len(body['resources']) > 0:
            return (Stream(s) for s in body['resources'])
        else:
            raise ApiError(
                'Falcon Streaming API not discovered. This may be caused by second instance of this application '
                'already running in your environment with the same application_id={}, or by missing streaming API '
                ' capability.'.format(app_id))

    def refresh_streaming_session(self, app_id):
        response = self.client.command(action='refreshActiveStreamSession',
                                       parametes={
                                           'action_name': 'refresh_active_stream_session',
                                           'appId': app_id
                                       })
        if 'status_code' not in response or response['status_code'] != 200:
            raise ApiError(
                'Could not refresh Falcon Streaming API. Response was: {}'.format(response)
            )


class Stream(dict):
    @property
    def token(self):
        return self['sessionToken']['token']

    @property
    def url(self):
        return self['dataFeedURL']

    @property
    def refresh_interval(self):
        return self['refreshActiveSessionInterval']
