from .errors import EventDataError, FalconAPIDataError


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
