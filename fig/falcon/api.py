from falconpy import api_complete as FalconSDK
from ..config import config
from .models import Stream


class ApiError(Exception):
    pass


class NoStreamsError(ApiError):
    def __init__(self, app_id):
        super().__init__(
            'Falcon Streaming API not discovered. This may be caused by second instance of this application '
            'already running in your environment with the same application_id={}, or by missing streaming API '
            'capability.'.format(app_id))


class FalconAPI():
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
            base_url=self.__class__.base_url())

    @classmethod
    def base_url(cls):
        return 'https://' + cls.CLOUD_REGIONS[config.get('falcon', 'cloud_region')]

    def streams(self, app_id):
        resources = self._resources(action='listAvailableStreamsOAuth2',
                                    parameters={'appId': config.get('falcon', 'application_id')})
        if not resources:
            raise NoStreamsError(app_id)
        return (Stream(s) for s in resources)

    def refresh_streaming_session(self, app_id, stream):
        self._command(action='refreshActiveStreamSession',
                      partition=stream.partition,
                      parameters={
                          'action_name': 'refresh_active_stream_session',
                          'appId': app_id
                      })

    def device_details(self, device_id):
        return self._resources(action='GetDeviceDetails', ids=[device_id])

    def init_rtr_session(self, device_id):
        return self._resources(
            action='RTR_InitSession',
            body={
                'device_id': device_id
            }
        )

    def execute_rtr_command(self, action, session_id, base_command, command_string):
        return self._resources(
            action=action,
            body={
                'base_command': base_command,
                'command_string': command_string,
                'session_id': session_id
            }
        )

    def check_rtr_command_status(self, cloud_request_id, sequence_id):
        return self._resources(
            action='RTR_CheckCommandStatus',
            parameters={
                'cloud_request_id': cloud_request_id,
                'sequence_id': sequence_id,
            }
        )

    def _resources(self, *args, **kwargs):
        response = self._command(*args, **kwargs)
        body = response['body']
        if 'resources' not in body or not body['resources']:
            return []
        return body['resources']

    def _command(self, *args, **kwargs):
        response = self.client.command(*args, **kwargs)
        body = response['body']
        if 'errors' in body and body['errors'] is not None:
            if len(body['errors']) > 0:
                raise ApiError('Error received from CrowdStrike Falcon platform: {}'.format(body['errors']))
        if 'status_code' not in response or (response['status_code'] != 200 and response['status_code'] != 201):
            raise ApiError('Unexpected response code from Falcon API. Response was: {}'.format(response))
        return response
