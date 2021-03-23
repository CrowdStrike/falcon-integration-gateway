import os
import configparser


class FigConfig(configparser.SafeConfigParser):
    ENV_DEFAULTS = [
        ['falcon', 'cloud_region', 'FALCON_CLOUD_REGION'],
        ['falcon', 'client_id', 'FALCON_CLIENT_ID'],
        ['falcon', 'client_secret', 'FALCON_CLIENT_SECRET']
    ]

    def __init__(self):
        super().__init__()
        self.read(['config/defaults.ini', 'config/devel.ini', 'config/config.ini'])
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

        assert int(self.get('events', 'severity_threshold')) in range(0, 5)
        assert int(self.get('events', 'older_than_days_threshold')) in range(0, 10000)


config = FigConfig()
