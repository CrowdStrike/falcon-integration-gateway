from base64 import b64decode, b64encode
from hashlib import sha256
from datetime import datetime
from json import dumps
from hmac import new
from requests import post
from ...log import log
from ...config import config
from ...falcon.errors import RTRConnectionError


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
    response = post(uri, data=body, headers=headers, timeout=60)
    if (response.status_code < 200 or response.status_code > 299):
        log.error("Failed to send detection to Log Analytics: %s", response.text)


class Submitter():
    AZURE_ARC_KEYS = ['resourceName', 'resourceGroup', 'subscriptionId', 'tenantId', 'vmId']

    def __init__(self, event):
        self.event = event
        self.workspace_id = config.get('azure', 'workspace_id')
        self.primary_key = config.get('azure', 'primary_key')
        self.azure_arc_config = self.autodiscovery()

    def autodiscovery(self):
        if self.event.cloud_provider == 'AZURE' or not config.getboolean('azure', 'arc_autodiscovery'):
            return None

        if self.event.device_details['platform_name'] not in ['Linux', 'Windows']:
            log.debug('Skipping Azure Arc Autodiscovery for %s (aid=%s, name=%s)',
                      self.event.device_details['platform_name'],
                      self.event.original_event.sensor_id,
                      self.event.original_event.computer_name
                      )
            return None
        if self.event.device_details['product_type_desc'] == 'Pod':
            log.debug('Skipping Azure Arc Autodiscovery for k8s pod (aid=%s, name=%s)',
                      self.event.original_event.sensor_id,
                      self.event.original_event.computer_name
                      )
            return None

        try:
            azure_arc_config = self.event.azure_arc_config()
        except RTRConnectionError as e:
            log.error("Cannot fetch Azure Arc info from host (aid=%s, hostname=%s, last_seen=%s): %s",
                      self.event.original_event.sensor_id,
                      self.event.device_details['hostname'],
                      self.event.device_details['last_seen'],
                      e
                      )
            return None
        except Exception as e:  # pylint: disable=W0703
            log.exception("Cannot fetch Azure Arc info from host (aid=%s, hostname=%s, last_seen=%s): %s",
                          self.event.original_event.sensor_id,
                          self.event.device_details['hostname'],
                          self.event.device_details['last_seen'],
                          e
                          )
            return None

        return {k: v
                for k, v in azure_arc_config.items()
                if k in self.AZURE_ARC_KEYS
                }

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)
        post_data(self.workspace_id, self.primary_key, self.log(), 'FalconIntegrationGatewayLogs')

    def log(self):
        json_data = [{
            'ExternalUri': self.event.falcon_link,
            'FalconEventId': self.event.event_id,
            'ComputerName': self.event.original_event.computer_name,
            'Description': self.event.detect_description,
            'Severity': self.event.severity,
            'Title': 'Falcon Alert. Instance {}'.format(self.event.instance_id),
            'ProcessName': self.event.original_event['event']['FileName'],
            'ProcessPath': self.event.original_event['event']['FilePath'],
            'CommandLine': self.event.original_event['event']['CommandLine'],
            'DetectName': self.event.detect_name,
            'AccountId': self.event.cloud_provider_account_id,
            'InstanceId': self.event.instance_id,
            'CloudProvider': self.cloud,
            'ResourceGroup': self.event.device_details.get('zone_group', None)
        }]

        if self.azure_arc_config is not None:
            json_data[0]['arc'] = self.azure_arc_config

        return dumps(json_data)

    @property
    def cloud(self):
        return self.event.cloud_provider if self.event.cloud_provider is not None else 'Unrecognized'


class Runtime():
    RELEVANT_EVENT_TYPES = ['DetectionSummaryEvent']

    def __init__(self):
        log.info("Azure Backend is enabled.")

    def is_relevant(self, falcon_event):
        return True

    def process(self, falcon_event):
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
