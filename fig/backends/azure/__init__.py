from ...log import log


class Runtime():
    def __init__(self):
        log.info('Initialising empty Azure backend runtime')

    def process(self, falcon_event):  # pylint: disable=R0201
        log.warning('Azure Backend received and skipped event: %s', falcon_event)


__all__ = ['Runtime']
