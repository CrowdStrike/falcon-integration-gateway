import os
import configparser
from functools import cached_property
from importlib.resources import files
from .credstore import CredStore


class FigConfig(configparser.ConfigParser):
    ALL_BACKENDS = {'AWS', 'AWS_SQS', 'AZURE', 'GCP', 'WORKSPACEONE', 'CLOUDTRAIL_LAKE', 'GENERIC'}
    FALCON_CLOUD_REGIONS = {'us-1', 'us-2', 'eu-1', 'us-gov-1'}
    SENSOR_RECOGNIZED_CLOUDS = {'AWS', 'Azure', 'GCP', 'unrecognized'}
    ENV_DEFAULTS = [
        ['main', 'backends', 'FIG_BACKENDS'],
        ['main', 'worker_threads', 'FIG_WORKER_THREADS'],
        ['logging', 'level', 'LOG_LEVEL'],
        ['events', 'severity_threshold', 'EVENTS_SEVERITY_THRESHOLD'],
        ['events', 'older_than_days_threshold', 'EVENTS_OLDER_THAN_DAYS_THRESHOLD'],
        ['events', 'offset', 'EVENTS_OFFSET'],
        ['falcon', 'cloud_region', 'FALCON_CLOUD_REGION'],
        ['falcon', 'client_id', 'FALCON_CLIENT_ID'],
        ['falcon', 'client_secret', 'FALCON_CLIENT_SECRET'],
        ['falcon', 'reconnect_retry_count', 'FALCON_RECONNECT_RETRY_COUNT'],
        ['falcon', 'application_id', 'FALCON_APPLICATION_ID'],
        ['credentials_store', 'store', 'CREDENTIALS_STORE'],
        ['ssm', 'region', 'SSM_REGION'],
        ['ssm', 'ssm_client_id', 'SSM_CLIENT_ID'],
        ['ssm', 'ssm_client_secret', 'SSM_CLIENT_SECRET'],
        ['secrets_manager', 'region', 'SECRETS_MANAGER_REGION'],
        ['secrets_manager', 'secrets_manager_secret_name', 'SECRETS_MANAGER_SECRET_NAME'],
        ['secrets_manager', 'secrets_manager_client_id_key', 'SECRETS_MANAGER_CLIENT_ID_KEY'],
        ['secrets_manager', 'secrets_manager_client_secret_key', 'SECRETS_MANAGER_CLIENT_SECRET_KEY'],
        ['azure', 'workspace_id', 'WORKSPACE_ID'],
        ['azure', 'primary_key', 'PRIMARY_KEY'],
        ['azure', 'arc_autodiscovery', 'ARC_AUTODISCOVERY'],
        ['aws', 'region', 'AWS_REGION'],
        ['aws', 'confirm_instance', 'AWS_CONFIRM_INSTANCE'],
        ['aws_sqs', 'region', 'AWS_REGION'],
        ['aws_sqs', 'sqs_queue_name', 'AWS_SQS'],
        ['workspaceone', 'token', 'WORKSPACEONE_TOKEN'],
        ['workspaceone', 'syslog_host', 'SYSLOG_HOST'],
        ['workspaceone', 'syslog_port', 'SYSLOG_PORT'],
        ['cloudtrail_lake', 'channel_arn', 'CLOUDTRAIL_LAKE_CHANNEL_ARN'],
        ['cloudtrail_lake', 'region', 'CLOUDTRAIL_LAKE_REGION'],
    ]

    def __init__(self):
        super().__init__()
        self._read_config_files()
        self._override_from_env()
        self._override_from_credentials_store()

    def _read_config_files(self):
        # Try reading from package first (when installed via pip)
        try:
            default_config = files("fig").joinpath("../config/defaults.ini")
            self.read(default_config)
        except (TypeError, ModuleNotFoundError, ValueError) as e:
            # If package reading fails, try reading from local paths
            base_paths = [
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # Project root
                os.getcwd(),  # Current working directory
            ]

            config_found = False
            for base_path in base_paths:
                possible_paths = [
                    os.path.join(base_path, 'config', 'defaults.ini'),
                    os.path.join(base_path, 'defaults.ini'),
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        self.read(path)
                        config_found = True
                        break

                if config_found:
                    break

            if not config_found:
                raise FileNotFoundError(
                    "Could not find defaults.ini in any expected location. "
                    "Make sure defaults.ini exists in the config directory."
                ) from e

        # Allow overrides from config.ini and devel.ini
        override_files = ['config.ini', 'devel.ini']
        for file in override_files:
            # Try current directory first
            if os.path.exists(file):
                self.read(file)
            elif os.path.exists(os.path.join('config', file)):
                self.read(os.path.join('config', file))

    def _override_from_env(self):
        for section, var, envvar in self.__class__.ENV_DEFAULTS:
            value = os.getenv(envvar)
            if value:
                self.set(section, var, value)

    def _override_from_credentials_store(self):
        credentials_store = self.get('credentials_store', 'store')
        if credentials_store:
            self._validate_credentials_store()
            region = self._get_region(credentials_store)
            credstore = CredStore(self, region)
            try:
                client_id, client_secret = credstore.load_credentials(credentials_store)
            except ValueError as e:
                raise Exception("Error loading credentials from store: {}:{}".format(credentials_store, e)) from e

            self.set('falcon', 'client_id', client_id)
            self.set('falcon', 'client_secret', client_secret)

    def _validate_credentials_store(self):
        if self.get('credentials_store', 'store') not in ['ssm', 'secrets_manager']:
            raise Exception('Malformed Configuration: expected credentials_store.store to be either ssm or secrets_manager')
        if self.get('credentials_store', 'store') == 'ssm':
            if not self.get('ssm', 'ssm_client_id') or not self.get('ssm', 'ssm_client_secret'):
                raise Exception('Malformed Configuration: expected ssm_client_id and ssm_client_secret to be provided')
        if self.get('credentials_store', 'store') == 'secrets_manager':
            if not self.get('secrets_manager', 'secrets_manager_secret_name') or not self.get('secrets_manager', 'secrets_manager_client_id_key') or not self.get('secrets_manager', 'secrets_manager_client_secret_key'):
                raise Exception('Malformed Configuration: expected secrets_manager_secret_name, secrets_manager_client_id_key and secrets_manager_client_secret_key to be provided')

    def _get_region(self, credentials_store):
        """Get the region to use for credential stores."""
        try:
            region = self.get(credentials_store, 'region')
        except configparser.NoOptionError as e:
            raise Exception("No region was found for the credential store: {}".format(e)) from e
        return region

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

        if int(self.get('events', 'severity_threshold')) not in range(1, 6):
            raise Exception('Malformed configuration: expected events.severity_threshold to be in range 1-5')
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
            if self.get('aws', 'confirm_instance') not in ['false', 'true']:
                raise Exception('Malformed Configuration: expected aws.confirm_instance must be either true or false')
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
        if 'CLOUDTRAIL_LAKE' in self.backends:
            if len(self.get('cloudtrail_lake', 'channel_arn')) == 0:
                raise Exception('Malformed Configuration: expected cloudtrail_lake.channel_arn to be non-empty')
            if len(self.get('cloudtrail_lake', 'region')) == 0:
                raise Exception('Malformed Configuration: expected cloudtrail_lake.region to be non-empty')
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
