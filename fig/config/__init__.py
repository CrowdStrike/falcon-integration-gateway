import os
import configparser
from functools import cached_property


class FigConfig(configparser.SafeConfigParser):
    ALL_BACKENDS = {'AWS', 'AWS_SQS', 'AZURE', 'GCP', 'WORKSPACEONE', 'CHRONICLE'}
    FALCON_CLOUD_REGIONS = {'us-1', 'us-2', 'eu-1', 'us-gov-1'}
    SENSOR_RECOGNIZED_CLOUDS = {'AWS', 'Azure', 'GCP', 'unrecognized'}
    ENV_DEFAULTS = [
        ['main', 'backends', 'FIG_BACKENDS'],
        ['main', 'worker_threads', 'FIG_WORKER_THREADS'],
        ['logging', 'level', 'LOG_LEVEL'],
        ['events', 'severity_threshold', 'EVENTS_SEVERITY_THRESHOLD'],
        ['events', 'older_than_days_threshold', 'EVENTS_OLDER_THAN_DAYS_THRESHOLD'],
        ['falcon', 'cloud_region', 'FALCON_CLOUD_REGION'],
        ['falcon', 'client_id', 'FALCON_CLIENT_ID'],
        ['falcon', 'client_secret', 'FALCON_CLIENT_SECRET'],
        ['falcon', 'reconnect_retry_count', 'FALCON_RECONNECT_RETRY_COUNT'],
        ['falcon', 'application_id', 'FALCON_APPLICATION_ID'],
        ['azure', 'workspace_id', 'WORKSPACE_ID'],
        ['azure', 'primary_key', 'PRIMARY_KEY'],
        ['aws', 'region', 'AWS_REGION'],
        ['aws_sqs', 'region', 'AWS_REGION'],
        ['aws_sqs', 'sqs_queue_name', 'AWS_SQS'],
        ['workspaceone', 'token', 'WORKSPACEONE_TOKEN'],
        ['workspaceone', 'syslog_host', 'SYSLOG_HOST'],
        ['workspaceone', 'syslog_port', 'SYSLOG_PORT'],
        ['chronicle', 'service_account', 'GOOGLE_SERVICE_ACCOUNT_FILE'],
        ['chronicle', 'customer_id', 'GOOGLE_CUSTOMER_ID'],
        ['chronicle', 'region', 'CHRONICLE_REGION']
    ]

    def __init__(self):
        super().__init__()
        self.read(['config/defaults.ini', 'config/config.ini', 'config/devel.ini'])
        self._override_from_env()

    def _override_from_env(self):
        for section, var, envvar in self.__class__.ENV_DEFAULTS:
            value = os.getenv(envvar)
            if value:
                self.set(section, var, value)

    def validate(self):
        for section, var, envvar in self.__class__.ENV_DEFAULTS:
            try:
                self.get(section, var)
            except configparser.NoOptionError as err:
                raise Exception(
                    "Please provide environment variable {} or configuration option {}.{}".format(
                        envvar, section, var)) from err

        if int(self.get('main', 'worker_threads')) not in range(1, 128):
            raise Exception('Malformed configuration: expected main.worker_threads to be in range 1-128')
        self.validate_falcon()
        self.validate_events()
        self.validate_backends()

    def validate_falcon(self):
        if int(self.get('falcon', 'reconnect_retry_count')) not in range(1, 10000):
            raise Exception('Malformed configuration: expected falcon.reconnect_retry_count to be in range 0-10000')
        if self.get('falcon', 'cloud_region') not in self.FALCON_CLOUD_REGIONS:
            raise Exception(
                'Malformed configuration: expected falcon.cloud_region to be in {}'.format(self.FALCON_CLOUD_REGIONS)
            )

    def validate_events(self):
        if not self.detections_exclude_clouds.issubset(self.SENSOR_RECOGNIZED_CLOUDS):
            raise Exception(
                'Malformed configuration: expected events.detections_exclude_clouds to be subset of "{}" got "{}"'.format(
                    self.SENSOR_RECOGNIZED_CLOUDS, self.detections_exclude_clouds))

        if int(self.get('events', 'severity_threshold')) not in range(0, 5):
            raise Exception('Malformed configuration: expected events.severity_threshold to be in range 0-4')
        if int(self.get('events', 'older_than_days_threshold')) not in range(0, 10000):
            raise Exception('Malformed configuration: expected events.older_than_days_threshold to be in range 0-10000')

    def validate_backends(self):
        if not self.backends.issubset(self.ALL_BACKENDS) or len(self.backends) < 1:
            raise Exception(
                'Malformed configuration: expected main.backends to be subset of "{}" and contain at least one'.format(
                    self.ALL_BACKENDS))
        if 'AWS' in self.backends:
            if len(self.get('aws', 'region')) == 0:
                raise Exception('Malformed Configuration: expected aws.region to be non-empty')
        if 'AWS_SQS' in self.backends:
            if len(self.get('aws_sqs', 'region')) == 0:
                raise Exception('Malformed Configuration: expected aws_sqs.region to be non-empty')
            if len(self.get('aws_sqs', 'sqs_queue_name')) == 0:
                raise Exception('Malformed Configuration: expected aws_sqs.sqs_queue_name to be non-empty')
        if 'WORKSPACEONE' in self.backends:
            if len(self.get('workspaceone', 'token')) == 0:
                raise Exception('Malformed Configuration: expected workspaceone.token to be non-empty')
            if len(self.get('workspaceone', 'syslog_host')) == 0:
                raise Exception('Malformed Configuration: expected workspaceone.syslog_host to be non-empty')
            if int(self.get('workspaceone', 'syslog_port')) not in range(1, 65535):
                raise Exception('Malformed configuration: expected workspaceone.syslog_port to be in range 1-65335')
        if 'CHRONICLE' in self.backends:
            if len(self.get('chronicle', 'service_account')) == 0:
                raise Exception('Malformed Configuration: expected chronicle.service_account_file to be non-empty')
            if len(self.get('chronicle', 'region')) == 0:
                raise Exception('Malformed Configuration: expected chronicle.region to be non-empty')
            if len(self.get('chronicle', 'customer_id')) == 0:
                raise Exception('Malformed Configuration: expected chronicle.customer_id to be non-empty')
        if 'AZURE' in self.backends:
            if len(self.get('azure', 'workspace_id')) == 0:
                raise Exception('Malformed Configuration: expected azure.workspace_id to be non-empty')
            if len(self.get('azure', 'primary_key')) == 0:
                raise Exception('Malformed Configuration: expected azure.primary_key to be non-empty')
            if self.get('azure', 'arc_autodiscovery') not in ['false', 'true']:
                raise Exception('Malformed Configuration: expected azure.arc_autodiscovery must be either true or false')

    @cached_property
    def backends(self):
        return set(self.get('main', 'backends').split(','))

    @cached_property
    def detections_exclude_clouds(self):
        value = self.get('events', 'detections_exclude_clouds')
        if value == '':
            return set()
        return set(value.split(','))


config = FigConfig()
