from logging import INFO, Formatter, getLogger
from ssl import CERT_NONE, PROTOCOL_TLSv1_2
from tlssyslog.handlers import TLSSysLogHandler
from ....config import config

serverlog = getLogger('ws1')
serverlog.setLevel(INFO)

tlsHandler = TLSSysLogHandler(
    address=(config.get('workspaceone', 'syslog_host'), int(config.get('workspaceone', 'syslog_port'))),
    ssl_kwargs={'cert_reqs': CERT_NONE, 'ssl_version': PROTOCOL_TLSv1_2}
)
tlsHandler.setLevel(INFO)

formatter = Formatter('%(asctime)s %(name)s %(threadName)-10s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
tlsHandler.setFormatter(formatter)

serverlog.addHandler(tlsHandler)
