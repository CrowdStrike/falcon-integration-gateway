from ...log import log


class Runtime():
    RELEVANT_EVENT_TYPES = "ALL"

    def __init__(self):
        log.info("GENERIC Backend is enabled.")

    def is_relevant(self, falcon_event):
        return True

    def process(self, falcon_event):
        # Used to display falcon_evnts in the console
        log.info(falcon_event.original_event)


__all__ = ['Runtime']
