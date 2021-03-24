class TranslatorError(Exception):
    pass


class EventDataError(TranslatorError):
    pass


class FalconAPIDataError(TranslatorError):
    pass


class GCPAPIDataError(TranslatorError):
    pass


class GCPAssetNotFound(GCPAPIDataError):
    pass
