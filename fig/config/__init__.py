import os
import configparser


class FigConfig(configparser.SafeConfigParser):
    ALL_BACKENDS = {'AWS', 'AZURE', 'GCP', 'WORKSPACEONE'}
    ENV_DEFAULTS = [
        ['falcon', 'cloud_region', 'FALCON_CLOUD_REGION'],
        ['falcon', 'client_id', 'FALCON_CLIENT_ID'],
        ['falcon', 'client_secret', 'FALCON_CLIENT_SECRET'],
        ['azure', 'workspace_id', 'WORKSPACE_ID'],
        ['azure', 'primary_key', 'PRIMARY_KEY'],
        ['aws', 'region', 'AWS_REGION'],
        ['workspaceone', 'token', 'WORKSPACEONE_TOKEN'],
        ['workspaceone', 'syslog_host', 'SYSLOG_HOST'],
        ['workspaceone', 'syslog_port', 'SYSLOG_PORT'],
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

        if int(self.get('events', 'severity_threshold')) not in range(0, 5):
            raise Exception('Malformed configuration: expected events.severity_threshold to be in range 0-5')
        if int(self.get('events', 'older_than_days_threshold')) not in range(0, 10000):
            raise Exception('Malformed configuration: expected events.older_than_days_threshold to be in range 0-10000')
        if int(self.get('main', 'worker_threads')) not in range(1, 128):
            raise Exception('Malformed configuration: expected main.worker_threads to be in range 1-128')
        self.validate_backends()

    def validate_backends(self):
        if not self.backends.issubset(self.ALL_BACKENDS) or len(self.backends) < 1:
            raise Exception(
                'Malformed configuration: expected main.backends to be subset of "{}" and contain at least one'.format(
                    self.ALL_BACKENDS))
        if 'AWS' in self.backends:
            if len(self.get('aws', 'region')) == 0:
                raise Exception('Malformed Configuration: expected aws.region to be non-empty')
            if len(self.get('aws', 'sqs_queue_name')) == 0:
                raise Exception('Malformed Configuration: expected aws.sqs_queue_name to be non-empty')
        if 'WORKSPACEONE' in self.backends:
            if len(self.get('workspaceone', 'token')) == 0:
                raise Exception('Malformed Configuration: expected workspaceone.token to be non-empty')
            if len(self.get('workspaceone', 'syslog_host')) == 0:
                raise Exception('Malformed Configuration: expected workspaceone.syslog_host to be non-empty')
            if int(self.get('workspaceone', 'syslog_port')) not in range(1, 65535):
                raise Exception('Malformed configuration: expected workspaceone.syslog_port to be in range 1-65335')

    @property
    def backends(self):
        return set(self.get('main', 'backends').split(','))


config = FigConfig()
