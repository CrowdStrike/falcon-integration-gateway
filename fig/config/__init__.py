import os
import configparser


config = configparser.SafeConfigParser()
config.read(['config/defaults.ini', 'config/devel.ini', 'config/config.ini'])


__ENV_DEFAULTS = [
    ['falcon', 'cloud_region', 'FALCON_CLOUD_REGION'],
    ['falcon', 'client_id', 'FALCON_CLIENT_ID'],
    ['falcon', 'client_secret', 'FALCON_CLIENT_SECRET']
]


for section, var, envvar in __ENV_DEFAULTS:
    value = os.getenv(envvar)
    if value:
        config.set(section, var, value)


def validate_config():
    for section, var, envvar in __ENV_DEFAULTS:
        try:
            config.get(section, var)
        except configparser.NoOptionError:
            raise Exception(
                "Please provide environment variable {} or configuration option {}.{}".format(
                    envvar, section, var))

    assert int(config.get('events', 'severity_threshold')) in range(0, 5)
