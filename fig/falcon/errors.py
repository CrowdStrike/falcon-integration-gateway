class ApiError(Exception):
    pass


class NoStreamsError(ApiError):
    def __init__(self, app_id):
        super().__init__(
            'Falcon Streaming API not discovered. This may be caused by second instance of this application '
            'already running in your environment with the same application_id={}, or by missing streaming API '
            'capability.'.format(app_id))


class RTRError(ApiError):
    pass


class RTRConnectionError(ApiError):
    pass
