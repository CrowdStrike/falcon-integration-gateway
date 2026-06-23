from base64 import b64decode, b64encode
from hashlib import sha256
from datetime import datetime
from json import dumps
from hmac import new
from requests import post
from azure.monitor.ingestion import LogsIngestionClient
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from ...log import log
from ...config import config
from ...falcon.errors import RTRConnectionError

STREAM_NAME = 'Custom-FalconIntegrationGatewayLogs'


def post_data(client, dcr_immutable_id, body):
    try:
        client.upload(dcr_immutable_id, STREAM_NAME, body)
    except ClientAuthenticationError as e:
        log.error("Azure authentication failed sending detection to Log Analytics: %s", e)
    except HttpResponseError as e:
        log.error("Failed to send detection to Log Analytics: %s", e)


def post_data_legacy(workspace_id, primary_key, body, log_type):
    body = dumps(body, ensure_ascii=False).encode('utf-8')
    method = 'POST'
    content_type = 'application/json'
    resource = '/api/logs'
    rfc1123date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(body)
    x_headers = 'x-ms-date:' + rfc1123date
    string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = b64decode(primary_key)
    encoded_hash = b64encode(new(decoded_key, bytes_to_hash, digestmod=sha256).digest()).decode()
    authorization = "SharedKey {}:{}".format(workspace_id, encoded_hash)
    uri = 'https://' + workspace_id + '.ods.opinsights.azure.com' + resource + '?api-version=2016-04-01'
    headers = {
        'content-type': content_type,
        'Authorization': authorization,
        'Log-Type': log_type,
        'x-ms-date': rfc1123date
    }
    response = post(uri, data=body, headers=headers, timeout=60)
    if (response.status_code < 200 or response.status_code > 299):
        log.error("Failed to send detection to Log Analytics: %s", response.text)


class Submitter():
    AZURE_ARC_KEYS = ['resourceName', 'resourceGroup', 'subscriptionId', 'tenantId', 'vmId']

    def __init__(self, event, ingestion_client=None, dcr_immutable_id=None,
                 workspace_id=None, primary_key=None):
        self.event = event
        self.ingestion_client = ingestion_client
        self.dcr_immutable_id = dcr_immutable_id
        self.workspace_id = workspace_id
        self.primary_key = primary_key
        self.azure_arc_config = self.autodiscovery()

    def autodiscovery(self):
        if self.event.cloud_provider == 'AZURE' or not config.getboolean('azure', 'arc_autodiscovery'):
            return None

        if self.event.device_details['platform_name'] not in ['Linux', 'Windows']:
            log.info('Skipping Azure Arc Autodiscovery for %s (aid=%s, name=%s)',
                     self.event.device_details['platform_name'],
                     self.event.original_event.sensor_id,
                     self.event.original_event.computer_name
                     )
            return None
        if self.event.device_details['product_type_desc'] == 'Pod':
            log.info('Skipping Azure Arc Autodiscovery for k8s pod (aid=%s, name=%s)',
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
        if self.ingestion_client is not None:
            post_data(self.ingestion_client, self.dcr_immutable_id, self.log())
        else:
            post_data_legacy(self.workspace_id, self.primary_key, self.log(), 'FalconIntegrationGatewayLogs')

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

        return json_data

    @property
    def cloud(self):
        return self.event.cloud_provider if self.event.cloud_provider is not None else 'Unrecognized'


class Runtime():
    RELEVANT_EVENT_TYPES = ['EppDetectionSummaryEvent']

    def __init__(self):
        auth_method = config.get('azure', 'auth_method')
        if auth_method == 'workload_identity':
            log.info("Azure Backend is enabled (auth: workload federated identity).")
            credential = DefaultAzureCredential()
            self._ingestion_client = LogsIngestionClient(
                config.get('azure', 'dcr_endpoint'), credential
            )
            self._dcr_immutable_id = config.get('azure', 'dcr_immutable_id')
            self._workspace_id = None
            self._primary_key = None
        elif auth_method == 'client_secret':
            log.info("Azure Backend is enabled (auth: client secret).")
            credential = ClientSecretCredential(
                tenant_id=config.get('azure', 'tenant_id'),
                client_id=config.get('azure', 'client_id'),
                client_secret=config.get('azure', 'client_secret'),
            )
            self._ingestion_client = LogsIngestionClient(
                config.get('azure', 'dcr_endpoint'), credential
            )
            self._dcr_immutable_id = config.get('azure', 'dcr_immutable_id')
            self._workspace_id = None
            self._primary_key = None
        else:
            log.warning(
                "Azure Backend is enabled using the deprecated HTTP Data Collector API. "
                "Please migrate to the Logs Ingestion API by setting azure.auth_method to "
                "'workload_identity' or 'client_secret'."
            )
            self._ingestion_client = None
            self._dcr_immutable_id = None
            self._workspace_id = config.get('azure', 'workspace_id')
            self._primary_key = config.get('azure', 'primary_key')

    def is_relevant(self, falcon_event):
        return True

    def process(self, falcon_event):
        Submitter(
            falcon_event,
            ingestion_client=self._ingestion_client,
            dcr_immutable_id=self._dcr_immutable_id,
            workspace_id=self._workspace_id,
            primary_key=self._primary_key,
        ).submit()


__all__ = ['Runtime']
