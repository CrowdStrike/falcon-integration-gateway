from ..falcon import Event


class TranslatorError(Exception):
    pass


class EventDataError(TranslatorError):
    pass


class FalconAPIDataError(TranslatorError):
    pass


class TranslationCache():
    def __init__(self, falcon_api):
        self.falcon = FalconCache(falcon_api)


class FalconCache():
    def __init__(self, falcon_api):
        self.falcon_api = falcon_api
        self._host_detail = {}

    def device_details(self, sensor_id):
        if not sensor_id:
            return EventDataError("Cannot process event. SensorId field is missing: ")

        if sensor_id not in self._host_detail:
            resources = self.falcon_api.device_details(sensor_id)
            if len(resources) > 1:
                raise FalconAPIDataError(
                    'Cannot process event for device: {}, multiple devices exists'.format(sensor_id))
            if len(resources) == 0:
                raise FalconAPIDataError('Cannot process event for device {}, device not known'.format(sensor_id))
            self._host_detail[sensor_id] = self.falcon_api.device_details(sensor_id)[0]

        return self._host_detail[sensor_id]


class FalconEvent():
    def __init__(self, original_event: Event, cache: TranslationCache):
        self.original_event = original_event
        self.cache = cache

    @property
    def device_details(self):
        return self.cache.falcon.device_details(self.original_event.sensor_id)

    @property
    def cloud_provider(self):
        return self.device_details.get('service_provider', None)

    @property
    def cloud_provider_account_id(self):
        return self.device_details.get('service_provider_account_id')

    @property
    def falcon_link(self):
        return self.original_event['event']['FalconHostLink']

    @property
    def event_id(self):
        return self.original_event['event']['DetectId']

    @property
    def time(self):
        return self.original_event.creation_time
