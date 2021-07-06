from base64 import b64decode, b64encode
from hashlib import sha256
from datetime import datetime
from json import dumps
from hmac import new
from requests import post
from ...log import log
from ...config import config


def build_signature(workspace_id, primary_key, date, content_length, method, content_type, resource):
    x_headers = 'x-ms-date:' + date
    string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = b64decode(primary_key)
    encoded_hash = b64encode(new(decoded_key, bytes_to_hash, digestmod=sha256).digest()).decode()
    authorization = "SharedKey {}:{}".format(workspace_id, encoded_hash)
    return authorization


def post_data(workspace_id, primary_key, body, log_type):
    method = 'POST'
    content_type = 'application/json'
    resource = '/api/logs'
    rfc1123date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(body)
    signature = build_signature(
        workspace_id,
        primary_key,
        rfc1123date,
        content_length,
        method,
        content_type,
        resource)
    uri = 'https://' + workspace_id + '.ods.opinsights.azure.com' + resource + '?api-version=2016-04-01'
    headers = {
        'content-type': content_type,
        'Authorization': signature,
        'Log-Type': log_type,
        'x-ms-date': rfc1123date
    }
    response = post(uri, data=body, headers=headers)
    if (response.status_code < 200 or response.status_code > 299):
        log.error("Failed to send detection to Log Analytics: %s", response.text)


class Submitter():
    def __init__(self, event):
        self.event = event
        self.workspace_id = config.get('azure', 'workspace_id')
        self.primary_key = config.get('azure', 'primary_key')

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        post_data(self.workspace_id, self.primary_key, self.log(), 'FalconIntegrationGatewayLogs')

    def log(self):
        json_data = [{
            'ExternalUri': self.event.falcon_link,
            'FalconEventId': self.event.event_id,
            'ComputerName': self.event.original_event['event']['ComputerName'],
            'Description': self.event.detect_description,
            'Severity': self.event.severity,
            'Title': 'Falcon Alert. Instance {}'.format(self.event.instance_id),
            'ProcessName': self.event.original_event['event']['FileName'],
            'ProcessPath': self.event.original_event['event']['FilePath'],
            'CommandLine': self.event.original_event['event']['CommandLine'],
            'DetectName': self.event.detect_name,
            'AccountId': self.event.cloud_provider_account_id,
            'InstanceId': self.event.instance_id,
            'ResourceGroup': self.event.device_details['zone_group']
        }]
        return dumps(json_data)


class Runtime():
    def __init__(self):
        log.info("Azure Backend is enabled.")

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return falcon_event.cloud_provider == 'AZURE'

    def process(self, falcon_event):  # pylint: disable=R0201
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
