from ...log import log


class Submitter():
    def __init__(self, event):
        self.event = event

    def submit(self):
        log.info("Processing detection: %s", self.event.detect_description)


class Runtime():
    def __init__(self):
        log.info("GCP Backend is enabled.")

    def process(self, falcon_event):  # pylint: disable=R0201
        Submitter(falcon_event).submit()


__all__ = ['Runtime']
