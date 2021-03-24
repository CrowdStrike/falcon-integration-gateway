class TranslatorError(Exception):
    pass


class EventDataError(TranslatorError):
    pass


class FalconAPIDataError(TranslatorError):
    pass
