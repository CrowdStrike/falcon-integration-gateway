import logging
from ..config import config

level = logging.getLevelName(config.get('logging', 'level'))

log = logging.getLogger('fig')
log.setLevel(level)

ch = logging.StreamHandler()
ch.setLevel(level)

formatter = logging.Formatter('%(asctime)s %(name)s %(threadName)-10s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
log.addHandler(ch)
