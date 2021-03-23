class GCPTranslatorError(Exception):
    pass


class EventDataError(GCPTranslatorError):
    pass


class FalconAPIDataError(GCPTranslatorError):
    pass
