from ...log import log
from ...config import config


class Runtime():
    @property
    def RELEVANT_EVENT_TYPES(self):
        """
        Parse configured event types for GENERIC backend.
        Returns "ALL" or a list of event type strings.
        """
        config_value = config.get('generic', 'event_types')

        # Handle "ALL" case (case-insensitive)
        if config_value.strip().upper() == "ALL":
            return "ALL"

        # Parse comma-separated list
        event_types = [t.strip() for t in config_value.split(',') if t.strip()]

        if not event_types:
            log.warning("GENERIC backend has empty event_types configuration, defaulting to ALL")
            return "ALL"

        return event_types

    def __init__(self):
        # Log configured event types on startup
        event_types = self.RELEVANT_EVENT_TYPES
        if event_types == "ALL":
            log.info("GENERIC Backend is enabled for ALL event types.")
        else:
            log.info("GENERIC Backend is enabled for event types: %s", event_types)

    def is_relevant(self, falcon_event):
        return True

    def process(self, falcon_event):
        # Used to display falcon_events in the console
        log.info(falcon_event.original_event)


__all__ = ['Runtime']
