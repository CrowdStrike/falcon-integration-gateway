from ...log import log


class Runtime():
    def __init__(self):
        log.info("Humio Backend is enabled.")

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return True

    def process(self, falcon_event):
        log.error("TODO HUMIO not implemented yet")


__all__ = ['Runtime']
