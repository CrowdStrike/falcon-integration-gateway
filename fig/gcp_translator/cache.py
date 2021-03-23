from .errors import EventDataError


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
            self._host_detail[sensor_id] = self.falcon_api.device_details(sensor_id)

        return self._host_detail[sensor_id]
