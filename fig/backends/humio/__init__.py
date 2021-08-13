from functools import lru_cache
from humiolib.HumioClient import HumioIngestClient

from ...log import log
from ...config import config


class Submitter():
    def __init__(self):
        _ = self.client  # instantiate the client

    def submit(self, event):
        structured_data = {
            "tags": {
                "source": "falcon-integration-gateway",
            },
            "events": [
                {
                    "timestamp": event.time,
                    "attributes": event.original_event['event'],
                }
            ]
        }
        self.client.ingest_json_data(structured_data)

    @property
    @lru_cache
    def client(self):
        return HumioIngestClient(base_url=self._base_url(), ingest_token=self._token())

    @classmethod
    def _base_url(cls):
        return config.get('humio', 'host')

    @classmethod
    def _token(cls):
        return config.get('humio', 'ingest_token')


class Runtime():
    def __init__(self):
        log.info("Humio Backend is enabled.")
        self.submitter = Submitter()

    def is_relevant(self, falcon_event):  # pylint: disable=R0201
        return True

    def process(self, falcon_event):
        self.submitter.submit(falcon_event)


__all__ = ['Runtime']
